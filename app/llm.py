import torch
from transformers import AutoTokenizer, AutoModelForCausalLM


MODEL_NAME = "Qwen/Qwen2.5-0.5B-Instruct"

tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

llm = AutoModelForCausalLM.from_pretrained(
    MODEL_NAME,
    torch_dtype="auto"
)


def generate_answer(question: str, context: str):

    prompt = f"""
You are a document question-answering assistant.

Your task is to answer the user's question using ONLY the information
contained in the provided context.

Rules:
1. Do not use outside knowledge.
2. Do not invent facts.
3. Do not assume information that is not present in the context.
4. If the context does not contain enough information to answer the question,
   respond exactly:
   "I don't know based on the provided documents."
5. Keep the answer focused on the question.
6. Do not add unrelated topics.
7. When the question asks what a document is about, summarize only the
   main topics clearly supported by the context.

Context:
{context}

Question:
{question}

Answer:
"""

    messages = [
        {
            "role": "user",
            "content": prompt
        }
    ]

    text = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True
    )

    inputs = tokenizer(
        [text],
        return_tensors="pt"
    )

    with torch.no_grad():
        outputs = llm.generate(
            **inputs,
            max_new_tokens=200
        )

    generated_tokens = outputs[0][
        inputs["input_ids"].shape[-1]:
    ]

    answer = tokenizer.decode(
        generated_tokens,
        skip_special_tokens=True
    )

    return answer