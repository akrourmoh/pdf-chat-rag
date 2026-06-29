"""Integration tests for the RAG endpoints and per-user isolation."""


def test_process_then_ask(client, auth_headers, make_pdf):
    headers = auth_headers("rag1@test.com")
    pdf = make_pdf("The Eiffel Tower is located in Paris, France.")

    r = client.post(
        "/process",
        files=[("files", ("doc.pdf", pdf, "application/pdf"))],
        headers=headers,
    )
    assert r.status_code == 200
    assert r.json()["chunks"] >= 1

    r = client.post("/ask", json={"question": "Where is the Eiffel Tower?"}, headers=headers)
    assert r.status_code == 200
    data = r.json()
    assert "answer" in data and data["answer"]
    assert isinstance(data["sources"], list) and len(data["sources"]) >= 1


def test_ask_before_processing_is_rejected(client, auth_headers):
    headers = auth_headers("empty@test.com")
    r = client.post("/ask", json={"question": "anything?"}, headers=headers)
    assert r.status_code == 400


def test_user_documents_are_isolated(client, auth_headers, make_pdf):
    user_a = auth_headers("iso_a@test.com")
    user_b = auth_headers("iso_b@test.com")

    # User A uploads a document.
    client.post(
        "/process",
        files=[("files", ("a.pdf", make_pdf("User A secret content."), "application/pdf"))],
        headers=user_a,
    )

    # User A can query their own documents.
    assert client.get("/status", headers=user_a).json()["documents_ready"] is True

    # User B has uploaded nothing -> sees no documents and cannot ask.
    assert client.get("/status", headers=user_b).json()["documents_ready"] is False
    r = client.post("/ask", json={"question": "What is the secret?"}, headers=user_b)
    assert r.status_code == 400


def test_delete_my_documents(client, auth_headers, make_pdf):
    headers = auth_headers("del_docs@test.com")
    client.post(
        "/process",
        files=[("files", ("d.pdf", make_pdf("Some content."), "application/pdf"))],
        headers=headers,
    )
    assert client.get("/status", headers=headers).json()["documents_ready"] is True

    r = client.delete("/me/documents", headers=headers)
    assert r.status_code == 200
    # After deletion, the user has no documents.
    assert client.get("/status", headers=headers).json()["documents_ready"] is False


def test_delete_my_account(client, auth_headers):
    headers = auth_headers("del_acct@test.com")
    # Account works before deletion.
    assert client.get("/me", headers=headers).status_code == 200

    r = client.delete("/me", headers=headers)
    assert r.status_code == 200

    # The token now points to a user that no longer exists -> rejected.
    assert client.get("/me", headers=headers).status_code == 401
