import uuid  # used to give each stored chunk a unique id

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

import config  # central settings (Qdrant connection, collection name, top_k)


# We keep a single Qdrant client for the whole app (created on first use).
_client = None


def get_client():
    # Return the shared Qdrant client, creating it the first time it's needed.
    global _client
    if _client is None:
        if config.QDRANT_URL:
            # Production: connect to a hosted Qdrant server (e.g. Qdrant Cloud).
            _client = QdrantClient(url=config.QDRANT_URL, api_key=config.QDRANT_API_KEY)
        else:
            # Local development: a self-contained on-disk database (no server needed).
            _client = QdrantClient(path=config.QDRANT_PATH)
    return _client


def build_vectorstore(chunks, embeddings, collection_name=None):
    # This function stores the chunks and their vectors in Qdrant so we can
    # search them later. It (re)creates the collection from scratch each time
    # the user processes documents.

    collection = collection_name or config.QDRANT_COLLECTION
    client = get_client()

    # The vector size is the length of one embedding (e.g. 3072 for gemini-embedding-001).
    dimension = len(embeddings[0])

    # Start fresh: drop the collection if it already exists, then create it.
    if client.collection_exists(collection):
        client.delete_collection(collection)
    client.create_collection(
        collection_name=collection,
        # COSINE distance is the standard choice for text embeddings.
        vectors_config=VectorParams(size=dimension, distance=Distance.COSINE),
    )

    # Build one "point" per chunk: a vector plus its metadata (the payload).
    points = []
    for chunk, vector in zip(chunks, embeddings):
        points.append(
            PointStruct(
                id=str(uuid.uuid4()),
                vector=vector,
                payload={
                    "text": chunk["text"],
                    "source": chunk["source"],
                    "page": chunk["page"],
                },
            )
        )

    # Insert all the points into the collection.
    client.upsert(collection_name=collection, points=points)


def search_vectorstore(query_embedding, collection_name=None, top_k=None):
    # This function searches Qdrant for the chunks most similar to the question
    # and returns them as chunk records (the same {text, source, page} shape as
    # before), so the rest of the app does not need to change.

    collection = collection_name or config.QDRANT_COLLECTION
    if top_k is None:
        top_k = config.TOP_K

    client = get_client()
    response = client.query_points(
        collection_name=collection,
        query=query_embedding,
        limit=top_k,
    )

    # Each hit's payload is the chunk record we stored earlier.
    return [hit.payload for hit in response.points]


def has_documents(collection_name=None):
    # Returns True if the collection exists and contains at least one chunk.
    # Because Qdrant persists data, this stays True across app restarts.

    collection = collection_name or config.QDRANT_COLLECTION
    client = get_client()
    try:
        info = client.get_collection(collection)
        return (info.points_count or 0) > 0
    except Exception:
        # Collection does not exist yet.
        return False
