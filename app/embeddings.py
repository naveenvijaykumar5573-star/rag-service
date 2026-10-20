
import os
import requests

JINA_API_URL = "https://api.jina.ai/v1/embeddings"
MODEL = "jina-embeddings-v5-omni-small"
DIMENSIONS = 384


def _embed(texts: list[str], task: str) -> list[list[float]]:
    api_key = os.getenv("JINA_API_KEY")
    if not api_key:
        raise RuntimeError("JINA_API_KEY environment variable is missing")

    response = requests.post(
        JINA_API_URL,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": MODEL,
            "task": task,
            "dimensions": DIMENSIONS,
            "normalized": True,
            "input": [{"text": text} for text in texts],
        },
        timeout=60,
    )
    response.raise_for_status()

    data = response.json()["data"]
    data.sort(key=lambda item: item["index"])
    embeddings = [item["embedding"] for item in data]

    for embedding in embeddings:
        if len(embedding) != DIMENSIONS:
            raise ValueError(
                f"Expected {DIMENSIONS} dimensions, got {len(embedding)}"
            )

    return embeddings


def create_embedding(text: str):
    return _embed([text], "retrieval.query")[0]


def create_embeddings(texts: list[str]):
    return _embed(texts, "retrieval.passage")
