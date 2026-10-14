import psycopg2
from pgvector.psycopg2 import register_vector


def get_connection():

    conn = psycopg2.connect(
        host="localhost",
        port=5432,
        database="rag_database",
        user="postgres",
        password="root"
    )

    register_vector(conn)

    return conn