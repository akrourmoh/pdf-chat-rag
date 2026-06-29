from concurrent.futures import ThreadPoolExecutor

import config          # central settings (embedding concurrency)
import gemini_client   # shared Gemini client (handles the API + retries + cache)


def embed_chunks(chunks):
    # This function takes a list of chunk records and converts each one's text
    # into a vector using the Gemini API.
    #
    # The embedding model accepts only one text per request, so instead of doing
    # them strictly one after another, we send several requests in parallel
    # (they are network-bound). executor.map keeps the results in order.

    texts = [chunk["text"] for chunk in chunks]
    if not texts:
        return []

    def _embed_one(text):
        return gemini_client.embed(text, task_type="RETRIEVAL_DOCUMENT")

    with ThreadPoolExecutor(max_workers=config.EMBED_CONCURRENCY) as executor:
        return list(executor.map(_embed_one, texts))


def embed_query(query):
    # This function takes a single question (string) and converts it into a
    # vector so we can search the vectorstore.

    return gemini_client.embed(query, task_type="RETRIEVAL_QUERY")
