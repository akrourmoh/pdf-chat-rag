import os                       # os - used to read environment variables
from google import genai        # Google's current (supported) Gemini SDK
from google.genai import types  # types - used to pass extra options like task_type
from dotenv import load_dotenv   # load_dotenv reads our .env file to get the API key

# Load the API key from the .env file and create a Gemini client.
# (On Render there is no .env file - the key comes from an environment variable
#  set in the Render dashboard, which load_dotenv simply leaves untouched.)
load_dotenv()
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

# The Gemini embedding model - free to use with your API key and very lightweight,
# so it works on Render's free tier (no heavy PyTorch model to load into memory).
EMBED_MODEL = "gemini-embedding-001"


def embed_chunks(chunks):
    # This function takes a list of text chunks and converts each one into a
    # vector (a list of numbers) using the Gemini API.

    embeddings = []

    # gemini-embedding-001 accepts only one text per request, so we embed the
    # chunks one at a time and collect the resulting vectors.
    for chunk in chunks:
        result = client.models.embed_content(
            model=EMBED_MODEL,
            contents=chunk,
            config=types.EmbedContentConfig(task_type="RETRIEVAL_DOCUMENT"),
        )

        # result.embeddings[0].values holds the actual vector of numbers.
        embeddings.append(result.embeddings[0].values)

    # Return all the embeddings (vectors)
    return embeddings


def embed_query(query):
    # This function takes a single question (string) and converts it into a
    # vector so we can search the vectorstore.

    result = client.models.embed_content(
        model=EMBED_MODEL,
        contents=query,
        config=types.EmbedContentConfig(task_type="RETRIEVAL_QUERY"),
    )

    # Return the single vector
    return result.embeddings[0].values
