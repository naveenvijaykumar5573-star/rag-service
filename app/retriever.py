from app.database import get_connection
from app.embeddings import create_embedding
from pgvector import Vector

def document_belongs_to_tenant(
    document_id: str,
    tenant_id: str
):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT 1
            FROM documents
            WHERE id = %s
              AND tenant_id = %s
            LIMIT 1;
            """,
            (document_id, tenant_id)
        )

        return cursor.fetchone() is not None

    finally:
        cursor.close()
        conn.close()


def retrieve_chunks(
    question: str,
    tenant_id: str,
    document_id: str | None = None,
    top_k: int = 3,
    similarity_threshold: float = 0.10
):
    query_embedding = Vector(create_embedding(question))

    conn = get_connection()
    cursor = conn.cursor()

    try:

        if document_id:
            # Search only inside the requested document
            cursor.execute(
                """
                SELECT
                    dc.id,
                    dc.document_id,
                    d.filename,
                    dc.chunk_index,
                    dc.content,
                    dc.embedding <=> %s AS distance
                FROM document_chunks dc
                JOIN documents d
                    ON dc.document_id = d.id
                WHERE dc.tenant_id = %s
                  AND d.tenant_id = %s
                  AND dc.document_id = %s
                  AND (1 - (dc.embedding <=> %s)) >= %s
                ORDER BY dc.embedding <=> %s
                LIMIT %s;
                """,
                (
                    query_embedding,
                    tenant_id,
                    tenant_id,
                    document_id,
                    query_embedding,
                    similarity_threshold,
                    query_embedding,
                    top_k
                )
            )

        else:
            # Search across all documents belonging to the tenant
            cursor.execute(
                """
                SELECT
                    dc.id,
                    dc.document_id,
                    d.filename,
                    dc.chunk_index,
                    dc.content,
                    dc.embedding <=> %s AS distance
                FROM document_chunks dc
                JOIN documents d
                    ON dc.document_id = d.id
                WHERE dc.tenant_id = %s
                  AND d.tenant_id = %s
                  AND (1 - (dc.embedding <=> %s)) >= %s
                ORDER BY dc.embedding <=> %s
                LIMIT %s;
                """,
                (
                    query_embedding,
                    tenant_id,
                    tenant_id,
                    query_embedding,
                    similarity_threshold,
                    query_embedding,
                    top_k
                )
            )

        return cursor.fetchall()

    finally:
        cursor.close()
        conn.close()