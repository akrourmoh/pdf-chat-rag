import os                          # os - used to read environment variables
import google.generativeai as genai  # Google's library to talk to the Gemini API
from dotenv import load_dotenv        # load_dotenv reads our .env file to get the API key

# Load the API key from the .env file and configure Gemini.
# (On Render there is no .env file - the key comes from an environment variable
#  you set in the Render dashboard, which load_dotenv simply leaves untouched.)
load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# The Gemini embedding model - free to use with your API key and very lightweight,
# so it works on Render's free tier (no heavy PyTorch model to load into memory).
EMBED_MODEL = "models/text-embedding-004"


def embed_chunks(chunks):
    # This function takes a list of text chunks
    # and converts each one into a vector (a list of numbers) using the Gemini API.

    embeddings = []

    # The API accepts up to 100 texts per request, so we send the chunks
    # in batches of 100 to avoid hitting that limit on large PDFs.
    for i in range(0, len(chunks), 100):
        batch = chunks[i:i + 100]

        result = genai.embed_content(
            model=EMBED_MODEL,
            content=batch,
            task_type="retrieval_document",  # tells Gemini these are documents to search later
        )

        # result["embedding"] is a list of vectors (one per chunk in the batch)
        embeddings.extend(result["embedding"])

    # Return all the embeddings (vectors)
    return embeddings


def embed_query(query):
    # This function takes a single question (string)
    # and converts it into a vector so we can search the vectorstore.

    result = genai.embed_content(
        model=EMBED_MODEL,
        content=query,
        task_type="retrieval_query",  # tells Gemini this is a search question
    )

    # Return the single vector
    return result["embedding"]
