from fastapi.testclient import TestClient
from jose import jwt

from app.main import app
from app.auth import JWT_SECRET, JWT_ALGORITHM

TENANT_1 = "7b93c62c-b74f-41da-bb97-3a8da5a674a5"


client = TestClient(app)


def test_ask_without_token():

    response = client.post(
        "/ask",
        json={
            "question": "What is this document about?"
        }
    )

    assert response.status_code == 401


def test_ask_with_invalid_token():

    response = client.post(
        "/ask",
        headers={
            "Authorization": "Bearer invalid-token"
        },
        json={
            "question": "What is this document about?"
        }
    )

    assert response.status_code == 401


def test_tenant_cannot_access_other_tenant_document():

    # Tenant 2 JWT
    token = jwt.encode(
        {
            "user_id": "test-user-tenant-2",
            "tenant_id": "3b08e914-48ee-41f4-9742-91004c85637b"
        },
        JWT_SECRET,
        algorithm=JWT_ALGORITHM
    )

    response = client.post(
        "/ask",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "question": "What is this document about?",
            "document_id": "e577efc0-744e-421a-b27c-488598ffaadd"
        }
    )

    assert response.status_code == 404

def test_tenant_can_access_own_document():

    # Tenant 1 JWT
    token = jwt.encode(
        {
            "user_id": "test-user-tenant-1",
            "tenant_id": "7b93c62c-b74f-41da-bb97-3a8da5a674a5"
        },
        JWT_SECRET,
        algorithm=JWT_ALGORITHM
    )

    response = client.post(
        "/ask",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "question": "What is this document about?",
            "document_id": "e577efc0-744e-421a-b27c-488598ffaadd"
        }
    )

    assert response.status_code == 200

def test_tenant_can_only_see_own_documents():

    # Tenant 1 JWT
    tenant1_token = jwt.encode(
        {
            "user_id": "test-user-tenant-1",
            "tenant_id": "7b93c62c-b74f-41da-bb97-3a8da5a674a5"
        },
        JWT_SECRET,
        algorithm=JWT_ALGORITHM
    )

    response = client.get(
        "/documents",
        headers={
            "Authorization": f"Bearer {tenant1_token}"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["tenant_id"] == "7b93c62c-b74f-41da-bb97-3a8da5a674a5"

    for document in data["documents"]:
        assert document["document_id"] != "887e8dd4-d809-41ce-b1b1-b6ca1f353769"

def test_tenant_cannot_get_other_tenant_document():

    # Tenant 2 JWT
    tenant2_token = jwt.encode(
        {
            "user_id": "test-user-tenant-2",
            "tenant_id": "3b08e914-48ee-41f4-9742-91004c85637b"
        },
        JWT_SECRET,
        algorithm=JWT_ALGORITHM
    )

    response = client.get(
        "/documents/e577efc0-744e-421a-b27c-488598ffaadd",
        headers={
            "Authorization": f"Bearer {tenant2_token}"
        }
    )

    assert response.status_code == 404

def test_tenant_can_get_own_document():

    # Tenant 1 JWT
    tenant1_token = jwt.encode(
        {
            "user_id": "test-user-tenant-1",
            "tenant_id": "7b93c62c-b74f-41da-bb97-3a8da5a674a5"
        },
        JWT_SECRET,
        algorithm=JWT_ALGORITHM
    )

    response = client.get(
        "/documents/e577efc0-744e-421a-b27c-488598ffaadd",
        headers={
            "Authorization": f"Bearer {tenant1_token}"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["document_id"] == "e577efc0-744e-421a-b27c-488598ffaadd"
    assert data["filename"] == "REPORT 1.pdf"
    assert data["status"] == "COMPLETED"

def test_tenant_cannot_delete_other_tenant_document():

    # Tenant 2 JWT
    tenant2_token = jwt.encode(
        {
            "user_id": "test-user-tenant-2",
            "tenant_id": "3b08e914-48ee-41f4-9742-91004c85637b"
        },
        JWT_SECRET,
        algorithm=JWT_ALGORITHM
    )

    response = client.delete(
        "/documents/e577efc0-744e-421a-b27c-488598ffaadd",
        headers={
            "Authorization": f"Bearer {tenant2_token}"
        }
    )

    assert response.status_code == 404

def test_upload_rejects_non_pdf():

    token = jwt.encode(
        {
            "user_id": "test-user-tenant-1",
            "tenant_id": "7b93c62c-b74f-41da-bb97-3a8da5a674a5"
        },
        JWT_SECRET,
        algorithm=JWT_ALGORITHM
    )

    response = client.post(
        "/documents/upload",
        headers={
            "Authorization": f"Bearer {token}"
        },
        files={
            "file": (
                "test.txt",
                b"This is not a PDF file.",
                "text/plain"
            )
        }
    )

    assert response.status_code == 400

def test_upload_rejects_empty_file():

    token = jwt.encode(
        {
            "user_id": "test-user-tenant-1",
            "tenant_id": "7b93c62c-b74f-41da-bb97-3a8da5a674a5"
        },
        JWT_SECRET,
        algorithm=JWT_ALGORITHM
    )

    response = client.post(
        "/documents/upload",
        headers={
            "Authorization": f"Bearer {token}"
        },
        files={
            "file": (
                "empty.pdf",
                b"",
                "application/pdf"
            )
        }
    )

    assert response.status_code == 400

def test_ask_rejects_empty_question():

    token = create_token(
        user_id="test-user",
        tenant_id=TENANT_1
    )

    response = client.post(
        "/ask",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "question": ""
        }
    )

    assert response.status_code == 400

    assert response.json()["detail"] == "Question cannot be empty"

def create_token(user_id, tenant_id):
    return jwt.encode(
        {
            "user_id": user_id,
            "tenant_id": tenant_id
        },
        JWT_SECRET,
        algorithm=JWT_ALGORITHM
    )

def test_ask_with_invalid_document_id():

    token = create_token(
        user_id="test-user",
        tenant_id=TENANT_1
    )

    response = client.post(
        "/ask",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "question": "What is this document about?",
            "document_id": "does-not-exist"
        }
    )

    assert response.status_code == 404

    assert response.json()["detail"] == "Document not found"

def test_upload_rejects_large_file():

    token = create_token(
        user_id="test-user",
        tenant_id=TENANT_1
    )

    large_file = b"x" * (10 * 1024 * 1024 + 1)

    response = client.post(
        "/documents/upload",
        headers={
            "Authorization": f"Bearer {token}"
        },
        files={
            "file": (
                "large.pdf",
                large_file,
                "application/pdf"
            )
        }
    )

    assert response.status_code == 413

    assert response.json()["detail"] == (
        "File size exceeds the maximum allowed limit of 10 MB"
    )

def test_upload_rejects_invalid_pdf():

    token = create_token(
        user_id="test-user",
        tenant_id=TENANT_1
    )

    fake_pdf = b"This is not actually a PDF"

    response = client.post(
        "/documents/upload",
        headers={
            "Authorization": f"Bearer {token}"
        },
        files={
            "file": (
                "fake.pdf",
                fake_pdf,
                "application/pdf"
            )
        }
    )

    assert response.status_code == 400

    assert response.json()["detail"] == (
        "Uploaded file is not a valid PDF"
    )
def test_ask_handles_database_failure(monkeypatch):

    token = create_token(
        user_id="test-user",
        tenant_id=TENANT_1
    )

    def fake_connection():
        raise Exception("Database connection failed")

    monkeypatch.setattr(
        "app.retriever.get_connection",
        fake_connection
    )

    response = client.post(
        "/ask",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "question": "What is this document about?"
        }
    )

    print("\nDATABASE FAILURE RESPONSE:")
    print(response.status_code)
    print(response.text)

def test_ask_handles_llm_failure(monkeypatch):

    token = create_token(
        user_id="test-user",
        tenant_id=TENANT_1
    )

    def fake_generate_answer(question, context):
        raise Exception("LLM generation failed")

    monkeypatch.setattr(
        "app.main.generate_answer",
        fake_generate_answer
    )

    response = client.post(
        "/ask",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "question": "What is this document about?"
        }
    )

    print("\nLLM FAILURE RESPONSE:")
    print(response.status_code)
    print(response.text)

    assert response.status_code == 500

    assert response.json()["detail"] == (
        "RAG service temporarily unavailable"
    )