import json
import torch

from pydantic import BaseModel
from deepeval.models.base_model import DeepEvalBaseLLM

from app.llm import llm, tokenizer


class LocalQwenEvaluator(DeepEvalBaseLLM):

    def __init__(self):
        self.model = llm
        self.tokenizer = tokenizer

    def load_model(self):
        return self.model

    def get_model_name(self):
        return "Qwen2.5-0.5B-Instruct-Evaluator"

    def generate(
        self,
        prompt: str,
        schema: type[BaseModel] | None = None
    ):

        messages = [
            {
                "role": "user",
                "content": prompt
            }
        ]

        text = self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )

        inputs = self.tokenizer(
            [text],
            return_tensors="pt"
        )

        with torch.no_grad():

            outputs = self.model.generate(
                **inputs,
                max_new_tokens=300,
                do_sample=False
            )

        generated_tokens = outputs[0][
            inputs["input_ids"].shape[-1]:
        ]

        result = self.tokenizer.decode(
            generated_tokens,
            skip_special_tokens=True
        ).strip()

        # DeepEval requests structured output
        if schema is not None:

            try:

                # Try to extract JSON
                start = result.find("{")
                end = result.rfind("}") + 1

                if start != -1 and end != 0:

                    json_text = result[start:end]

                    data = json.loads(json_text)

                    return schema.model_validate(data)

            except Exception:
                pass

        return result

    async def a_generate(
        self,
        prompt: str,
        schema: type[BaseModel] | None = None
    ):

        return self.generate(
            prompt,
            schema
        )