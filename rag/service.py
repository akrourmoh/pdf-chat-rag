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
from rag.vectorstore import (
    build_vectorstore,
    search_vectorstore,
    has_documents,
    delete_documents,
)
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


# Tag the model appends when its reply is not based on the documents
# (greetings, small talk, or "I don't know"). We use it to hide the sources line.
_NO_SOURCES_TAG = "<no_sources>"


def answer_question(question, user_id):
    # Returns (answer, sources).
    #
    # If the user has uploaded documents, we retrieve the relevant passages and
    # let the model answer from them (with sources). If they have no documents,
    # we pass no context and the model answers as a general assistant.
    if documents_ready(user_id):
        query_embedding = embed_query(question)
        relevant_chunks = search_vectorstore(
            query_embedding, collection_name=_collection_for(user_id)
        )
    else:
        relevant_chunks = []

    answer = get_answer(question, relevant_chunks)

    # If the model marked the reply as not document-based, drop the tag and
    # return no sources; otherwise show the sources it was based on.
    if _NO_SOURCES_TAG in answer:
        answer = answer.replace(_NO_SOURCES_TAG, "").strip()
        sources = []
    else:
        sources = format_sources(relevant_chunks)

    return answer, sources


def documents_ready(user_id):
    # True if THIS user has already processed and stored documents.
    return has_documents(collection_name=_collection_for(user_id))


def delete_user_documents(user_id):
    # Permanently delete all of THIS user's stored documents.
    delete_documents(collection_name=_collection_for(user_id))
