"""Shared Gemini client with retry logic and clean error handling.

Both the embedder and the chain talk to Gemini, so instead of each creating its
own client we create ONE here and reuse it. The helper functions also:

- retry automatically on temporary failures (rate limits, brief server errors)
  using exponential backoff, and
- raise a single, clear error type (GeminiError) when something really fails,
  so the rest of the app can show a friendly message instead of crashing.
"""

import time
from functools import lru_cache

from google import genai
from google.genai import types
from google.genai import errors as genai_errors

import config  # central settings (API key, model names)

# One shared client for the whole application.
client = genai.Client(api_key=config.GOOGLE_API_KEY)

# How many times to try a call, and how long to wait before the first retry.
# (Backoff doubles each time, e.g. 1s, 2s, 4s ... to ride out demand spikes.)
MAX_RETRIES = 4
INITIAL_BACKOFF_SECONDS = 1.0


class GeminiError(Exception):
    """Raised when a Gemini API call fails (after retries, if applicable)."""


def _with_retries(operation, what):
    """Run a Gemini API call, retrying temporary errors with backoff.

    `operation` is a function that performs the actual API call.
    `what` is a short label used in error messages (e.g. "Embedding request").
    """
    backoff = INITIAL_BACKOFF_SECONDS
    last_error = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            return operation()

        except genai_errors.ClientError as e:
            # 4xx errors. A 429 means "too many requests" (rate limit) and is
            # worth retrying. Anything else (e.g. 404 bad model, 401 bad key)
            # will not fix itself, so we fail immediately with a clear message.
            if getattr(e, "code", None) == 429 and attempt < MAX_RETRIES:
                last_error = e
                time.sleep(backoff)
                backoff *= 2
                continue
            raise GeminiError(f"{what} failed: {e}") from e

        except genai_errors.ServerError as e:
            # 5xx errors are temporary problems on Google's side - retry.
            last_error = e
            if attempt < MAX_RETRIES:
                time.sleep(backoff)
                backoff *= 2
                continue
            raise GeminiError(
                f"{what} failed after {MAX_RETRIES} attempts: {e}"
            ) from e

    # Should only get here if every attempt was a retryable failure.
    raise GeminiError(f"{what} failed: {last_error}")


def _embed_once(text, task_type):
    # Perform a single embedding API call (with retries).
    def operation():
        result = client.models.embed_content(
            model=config.EMBED_MODEL,
            contents=text,
            config=types.EmbedContentConfig(task_type=task_type),
        )
        return result.embeddings[0].values

    return _with_retries(operation, "Embedding request")


@lru_cache(maxsize=config.EMBED_CACHE_SIZE)
def _embed_cached(text, task_type):
    # Cache identical (text, task_type) lookups so we never pay for the same
    # embedding twice (e.g. the same question asked again). Thread-safe.
    return _embed_once(text, task_type)


def embed(text, task_type):
    """Return the embedding vector for a single piece of text (cached)."""
    return _embed_cached(text, task_type)


def generate(prompt):
    """Return the generated text answer for a prompt.

    Tries the primary model first; if it stays overloaded/unavailable even after
    retries, falls back to a secondary model so the user still gets an answer.
    """

    def make_operation(model_name):
        def operation():
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
            )
            return response.text
        return operation

    try:
        return _with_retries(make_operation(config.LLM_MODEL), "Answer generation")
    except GeminiError:
        # Primary model failed (e.g. high demand) - try the fallback model.
        fallback = config.LLM_FALLBACK_MODEL
        if fallback and fallback != config.LLM_MODEL:
            return _with_retries(make_operation(fallback), "Answer generation (fallback)")
        raise
