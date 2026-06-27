import gemini_client  # shared Gemini client (handles the API + retries)


def embed_chunks(chunks):
    # This function takes a list of chunk records and converts each one's text
    # into a vector (a list of numbers) using the Gemini API.

    embeddings = []

    # gemini-embedding-001 accepts only one text per request, so we embed the
    # chunks one at a time and collect the resulting vectors.
    for chunk in chunks:
        vector = gemini_client.embed(chunk["text"], task_type="RETRIEVAL_DOCUMENT")
        embeddings.append(vector)

    # Return all the embeddings (vectors), in the same order as the chunks
    return embeddings


def embed_query(query):
    # This function takes a single question (string) and converts it into a
    # vector so we can search the vectorstore.

    return gemini_client.embed(query, task_type="RETRIEVAL_QUERY")
