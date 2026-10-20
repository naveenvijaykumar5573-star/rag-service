
import os
import requests

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "openai/gpt-oss-20b"


def generate_answer(question: str, context: str) -> str:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY is missing")

    response = requests.post(
        GROQ_API_URL,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": GROQ_MODEL,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "Answer using ONLY the supplied document context. "
                        "If the answer is absent, say you don't know based "
                        "on the provided documents."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Document context:\n{context}\n\n"
                        f"Question: {question}"
                    ),
                },
            ],
            "max_completion_tokens": 500,
            "reasoning_effort": "low",
            "include_reasoning": False,
        },
        timeout=60,
    )

    response.raise_for_status()
    data = response.json()
    answer = data["choices"][0]["message"].get("content")

    if not answer or not answer.strip():
        raise RuntimeError("Groq returned an empty answer")

    return answer.strip()
