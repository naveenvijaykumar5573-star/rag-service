from app.document import extract_text_from_pdf
from app.chunking import split_text_into_chunks
from app.embeddings import create_embeddings
from app.database import get_connection


def process_document(
    document_id: str,
    file_path: str,
    filename: str,
    tenant_id: str
):

    # --------------------------------
    # 1. Extract text from PDF
    # --------------------------------

    text = extract_text_from_pdf(file_path)

    if not text.strip():
        raise ValueError("PDF contains no readable text")


    # --------------------------------
    # 2. Split text into chunks
    # --------------------------------

    chunks = split_text_into_chunks(text)

    if not chunks:
        raise ValueError("No chunks were created from the PDF")


    # --------------------------------
    # 3. Generate embeddings
    # --------------------------------

    embeddings = create_embeddings(chunks)


    # --------------------------------
    # 4. Connect to PostgreSQL
    # --------------------------------

    conn = get_connection()
    cursor = conn.cursor()


    try:

        # --------------------------------
        # 5. Save document metadata
        # --------------------------------

        cursor.execute(
            """
            INSERT INTO documents
            (
                id,
                tenant_id,
                filename,
                file_path,
                status
            )
            VALUES (%s, %s, %s, %s, %s)
            """,
            (
                document_id,
                tenant_id,
                filename,
                file_path,
                "PROCESSING"
            )
        )


        # --------------------------------
        # 6. Save chunks + embeddings
        # --------------------------------

        for index, (chunk, embedding) in enumerate(
            zip(chunks, embeddings)
        ):

            cursor.execute(
                """
                INSERT INTO document_chunks
                (
                    document_id,
                    tenant_id,
                    chunk_index,
                    content,
                    embedding
                )
                VALUES (%s, %s, %s, %s, %s)
                """,
                (
                    document_id,
                    tenant_id,
                    index,
                    chunk,
                    embedding
                )
            )


        # --------------------------------
        # 7. Mark document completed
        # --------------------------------

        cursor.execute(
            """
            UPDATE documents
            SET status = %s
            WHERE id = %s
            """,
            (
                "COMPLETED",
                document_id
            )
        )


        # --------------------------------
        # 8. Commit transaction
        # --------------------------------

        conn.commit()


    except Exception:

        conn.rollback()

        # Try to mark the document as failed
        try:

            cursor.execute(
                """
                UPDATE documents
                SET status = %s
                WHERE id = %s
                """,
                (
                    "FAILED",
                    document_id
                )
            )

            conn.commit()

        except Exception:

            conn.rollback()

        raise


    finally:

        cursor.close()
        conn.close()


    return {
        "document_id": document_id,
        "filename": filename,
        "tenant_id": tenant_id,
        "chunks": len(chunks),
        "status": "COMPLETED"
    }