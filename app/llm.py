import time
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

MODEL_NAME = "Qwen/Qwen2.5-0.5B-Instruct"

# Select GPU when available; otherwise use CPU
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

print(f"Loading Qwen model on: {DEVICE}")

tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

model_kwargs = {}
if DEVICE == "cuda":
    model_kwargs["torch_dtype"] = torch.float16

llm = AutoModelForCausalLM.from_pretrained(
    MODEL_NAME,
    **model_kwargs
)

llm = llm.to(DEVICE)
llm.eval()

print(f"Qwen model loaded successfully on {DEVICE}")


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

    # Move input tensors to the same device as the model
    inputs = {key: value.to(DEVICE) for key, value in inputs.items()}

    start_time = time.time()

    with torch.inference_mode():
        outputs = llm.generate(
            **inputs,
            max_new_tokens=100,
            do_sample=False
        )

        if DEVICE == "cuda":
            torch.cuda.synchronize()
            generated_token_count = (
                outputs[0].shape[0] - inputs["input_ids"].shape[1]
            )
            print(f"Generated tokens: {generated_token_count}")
    print(
        f"LLM generation time on {DEVICE}: "
        f"{time.time() - start_time:.2f} seconds"
    )

    generated_tokens = outputs[0][
        inputs["input_ids"].shape[-1]:
    ]

    answer = tokenizer.decode(
        generated_tokens,
        skip_special_tokens=True
    )

    return answer
