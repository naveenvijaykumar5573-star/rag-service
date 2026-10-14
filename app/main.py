import os
import uuid
import fitz
MAX_FILE_SIZE = 10 * 1024 * 1024

from fastapi import (
    FastAPI,
    UploadFile,
    File,
    HTTPException,
    Depends
)
from pydantic import BaseModel

from app.retriever import (
    retrieve_chunks,
    document_belongs_to_tenant
)
from app.llm import generate_answer
from fastapi import HTTPException
from app.ingestion import process_document
from app.database import get_connection
from app.auth import get_current_user
from fastapi import Depends
from app.auth import get_current_user
from pydantic import BaseModel, Field

# ============================================================
# FastAPI Application
# ============================================================

app = FastAPI(
    title="Multi-Tenant AI Document RAG Service",
    description="AI document processing and question answering service",
    version="1.0.0"
)


# ============================================================
# Request Model
# ============================================================
class QuestionRequest(BaseModel):
    question: str
    document_id: str | None = None


# ============================================================
# Home
# ============================================================

@app.get("/")
def home():

    return {
        "message": "RAG Service is running"
    }


# ============================================================
# Ask Question
# ============================================================
@app.post("/ask")
def ask_question_api(
    request: QuestionRequest,
    current_user: dict = Depends(get_current_user)
):
    tenant_id = current_user["tenant_id"]

    # Validate question
    if not request.question.strip():
        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty"
        )

    if request.document_id:

        if not document_belongs_to_tenant(
            request.document_id,
            tenant_id
        ):
            raise HTTPException(
                status_code=404,
                detail="Document not found"
            )

    try:

        # -----------------------------------------
        # 1. Retrieve relevant chunks
        # -----------------------------------------
        
        results = retrieve_chunks(
            question=request.question,
            tenant_id=tenant_id,
            document_id=request.document_id,
            top_k=3
        )

        if not results:

            return {
                "question": request.question,
                "tenant_id": tenant_id,
                "answer": "I don't know based on the provided documents.",
                "sources": []
            }

        # -----------------------------------------
        # 2. Build context
        # -----------------------------------------

        context = "\n\n".join(
            content
            for (
                chunk_id,
                document_id,
                filename,
                chunk_index,
                content,
                distance
            ) in results
        )

        answer = generate_answer(
            request.question,
            context
        )

        sources = []

        for (
            chunk_id,
            document_id,
            filename,
            chunk_index,
            content,
            distance
        ) in results:

            sources.append({
                "document_id": document_id,
                "filename": filename,
                "chunk_id": chunk_id,
                "chunk_index": chunk_index,
                "distance": float(distance)
            })

        # -----------------------------------------
        # 5. Return response
        # -----------------------------------------

        return {
            "question": request.question,
            "tenant_id": tenant_id,
            "answer": answer,
            "sources": sources
        }

    except HTTPException:
            raise

    except Exception as e:

        print(f"RAG service error: {e}")

        raise HTTPException(
            status_code=500,
            detail="RAG service temporarily unavailable"
        )

# ============================================================
# Upload Document
# ============================================================
@app.post("/documents/upload")
async def upload_document(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    tenant_id = current_user["tenant_id"]

    # -----------------------------------------
    # 1. Validate filename
    # -----------------------------------------

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="Filename is required"
        )

    # -----------------------------------------
    # 2. Validate file type
    # -----------------------------------------

    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are allowed"
        )

    # -----------------------------------------
    # 3. Read uploaded file
    # -----------------------------------------

    content = await file.read()

    # -----------------------------------------
    # 4. Validate empty file
    # -----------------------------------------

    if not content:
        raise HTTPException(
            status_code=400,
            detail="Uploaded file is empty"
        )
    
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail="File size exceeds the maximum allowed limit of 10 MB"
        )
        

    # -----------------------------------------
    # 5. Create uploads directory
    # -----------------------------------------

    upload_directory = "uploads"

    os.makedirs(
        upload_directory,
        exist_ok=True
    )

    # -----------------------------------------
    # 6. Generate document ID
    # -----------------------------------------

    document_id = str(uuid.uuid4())

    # -----------------------------------------
    # 7. Create file path
    # -----------------------------------------

    file_path = os.path.join(
        upload_directory,
        f"{document_id}.pdf"
    )

    # -----------------------------------------
    # 8. Save uploaded PDF
    # -----------------------------------------

    try:

        with open(file_path, "wb") as buffer:
            buffer.write(content)

        # -----------------------------------------
        # 9. Process document
        # -----------------------------------------

        result = process_document(
            document_id=document_id,
            file_path=file_path,
            filename=file.filename,
            tenant_id=tenant_id
        )

        return result

    except Exception as e:

        # Delete file if processing fails

        if os.path.exists(file_path):
            os.remove(file_path)

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )
# ============================================================
# Get All Documents
# ============================================================

@app.get("/documents")
def get_documents(
    current_user: dict = Depends(get_current_user)
):

    tenant_id = current_user["tenant_id"]

    conn = get_connection()
    cursor = conn.cursor()

    try:

        cursor.execute(
            """
            SELECT
                id,
                filename,
                status,
                created_at
            FROM documents
            WHERE tenant_id = %s
            ORDER BY created_at DESC
            """,
            (tenant_id,)
        )

        rows = cursor.fetchall()

        documents = []

        for row in rows:

            documents.append({
                "document_id": row[0],
                "filename": row[1],
                "status": row[2],
                "created_at": row[3]
            })

        return {
            "tenant_id": tenant_id,
            "documents": documents
        }

    finally:

        cursor.close()
        conn.close()

# ============================================================
# Get Single Document
# ============================================================

@app.get("/documents/{document_id}")
def get_document(
    document_id: str,
    current_user: dict = Depends(get_current_user)
):
    tenant_id = current_user["tenant_id"]

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT id, filename, file_path, status, created_at
            FROM documents
            WHERE id = %s
            AND tenant_id = %s
            """,
            (document_id, tenant_id)
        )

        row = cursor.fetchone()

        if not row:
            raise HTTPException(
                status_code=404,
                detail="Document not found"
            )

        return {
            "document_id": row[0],
            "filename": row[1],
            "file_path": row[2],
            "status": row[3],
            "created_at": row[4]
        }

    finally:
        cursor.close()
        conn.close()

# ============================================================
# Delete Document
# ============================================================

@app.delete("/documents/{document_id}")
def delete_document(
    document_id: str,
    current_user: dict = Depends(get_current_user)
):
    tenant_id = current_user["tenant_id"]

    conn = get_connection()
    cursor = conn.cursor()

    try:
        # -----------------------------------------
        # 1. Find document belonging to this tenant
        # -----------------------------------------

        cursor.execute(
            """
            SELECT file_path
            FROM documents
            WHERE id = %s
            AND tenant_id = %s
            """,
            (document_id, tenant_id)
        )

        row = cursor.fetchone()

        if not row:
            raise HTTPException(
                status_code=404,
                detail="Document not found"
            )

        file_path = row[0]

        # -----------------------------------------
        # 2. Delete document chunks
        # -----------------------------------------

        cursor.execute(
            """
            DELETE FROM document_chunks
            WHERE document_id = %s
            AND tenant_id = %s
            """,
            (document_id, tenant_id)
        )

        # -----------------------------------------
        # 3. Delete document metadata
        # -----------------------------------------

        cursor.execute(
            """
            DELETE FROM documents
            WHERE id = %s
            AND tenant_id = %s
            """,
            (document_id, tenant_id)
        )

        conn.commit()

    except Exception:
        conn.rollback()
        raise

    finally:
        cursor.close()
        conn.close()

    # -----------------------------------------
    # 4. Delete physical PDF file
    # -----------------------------------------

    if file_path and os.path.exists(file_path):
        try:
            os.remove(file_path)
        except OSError as e:
            return {
                "message": "Document deleted from database, but physical file could not be deleted",
                "document_id": document_id,
                "warning": str(e)
            }

    return {
        "message": "Document deleted successfully",
        "document_id": document_id
    }