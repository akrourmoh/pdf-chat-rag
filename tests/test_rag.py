"""Unit tests for the pure RAG logic (no network, no app needed)."""

from rag.chunker import split_documents
from rag.citations import format_sources


def test_split_documents_keeps_metadata():
    pages = [
        {"source": "report.pdf", "page": 1, "text": "Hello world. " * 200},
        {"source": "report.pdf", "page": 2, "text": "Second page. " * 200},
    ]
    chunks = split_documents(pages)

    assert len(chunks) > 0
    # Every chunk carries text + its origin (source + page).
    for chunk in chunks:
        assert set(chunk.keys()) == {"text", "source", "page"}
        assert chunk["source"] == "report.pdf"
        assert chunk["page"] in (1, 2)


def test_format_sources_dedups_and_keeps_order():
    chunks = [
        {"text": "a", "source": "report.pdf", "page": 4},
        {"text": "b", "source": "report.pdf", "page": 4},  # duplicate
        {"text": "c", "source": "report.pdf", "page": 7},
        {"text": "d", "source": "notes.pdf", "page": 1},
    ]
    sources = format_sources(chunks)

    assert sources == ["report.pdf (p.4)", "report.pdf (p.7)", "notes.pdf (p.1)"]
