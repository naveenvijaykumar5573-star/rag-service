from sentence_transformers import SentenceTransformer


MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


embedding_model = SentenceTransformer(
    MODEL_NAME
)


def create_embedding(text: str):
    """
    Create an embedding for a single piece of text.
    """
    return embedding_model.encode(text)


def create_embeddings(texts):
    """
    Create embeddings for multiple pieces of text.
    """
    return embedding_model.encode(texts)