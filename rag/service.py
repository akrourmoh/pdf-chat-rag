"""Service layer: the high-level RAG operations.

This module ties together all the small RAG pieces (load, chunk, embed, store,
search, answer) into a few simple operations. Both the API and any other caller
use these functions, so the orchestration logic lives in exactly one place.

Every operation is scoped to a specific user: each user's documents live in
their OWN Qdrant collection ("user_<id>"), so users can never see each other's
files. This is what makes the app safe for multiple users (multi-tenancy).
"""

from rag.loader import load_pdfs
from rag.chunker import split_documents
from rag.embedder import embed_chunks, embed_query
from rag.vectorstore import build_vectorstore, search_vectorstore, has_documents
from rag.chain import get_answer
from rag.citations import format_sources


def _collection_for(user_id):
    # The private collection name for a given user.
    return f"user_{user_id}"


def process_documents(files, user_id):
    # files: a list of (filename, pdf_bytes) pairs.
    # Stores the chunks in THIS user's collection and returns how many were stored.
    pages = load_pdfs(files)
    chunks = split_documents(pages)
    embeddings = embed_chunks(chunks)
    build_vectorstore(chunks, embeddings, collection_name=_collection_for(user_id))
    return len(chunks)


def answer_question(question, user_id):
    # Searches only THIS user's documents, then asks the LLM.
    # Returns (answer, sources).
    query_embedding = embed_query(question)
    relevant_chunks = search_vectorstore(
        query_embedding, collection_name=_collection_for(user_id)
    )
    answer = get_answer(question, relevant_chunks)
    sources = format_sources(relevant_chunks)
    return answer, sources


def documents_ready(user_id):
    # True if THIS user has already processed and stored documents.
    return has_documents(collection_name=_collection_for(user_id))
