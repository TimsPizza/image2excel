from typing import Dict
from backend.app.core.config import ENV_CONFIG
from .prompt import get_initial_prompt, get_feedback_prompt, get_error_prompt
from openai import OpenAI

BASE_URL = "https://api.openai.com/v1/chat/completions"

openai_client = OpenAI(
    api_key=ENV_CONFIG.OPENAI_API_KEY,
    base_url=BASE_URL,
)


def send_request(prompt: str) -> Dict[str:str]:
    try:
        messages = [
            {"role": "developer", "content": get_initial_prompt()},
            {"role": "user", "content": prompt},
        ]
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
        )

        generated_code = response["choices"][0]["message"]["content"]

        return {"completion_id": response.id, "generated_code": generated_code}
    except Exception as e:
        # TODO: For production usage, implement proper logging and error handling.
        raise e
