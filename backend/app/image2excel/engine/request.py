from typing import Dict
from backend.app.core.config import ENV_CONFIG
from .prompt import prompt as LMM_PROMPT
from openai import OpenAI

BASE_URL = "https://api.openai.com/v1/chat/completions"

# image_file_name: openai_completion_id
active_sessions: Dict[str, str] = {}

openai_client = OpenAI(
    api_key=ENV_CONFIG.OPENAI_API_KEY,
    base_url=BASE_URL,
)

def send_request(prompt: str, completion_id: str = None):
    """
    Send a request to the OpenAI completion API with a prompt and an optional completion_id.
    Returns a dict containing a new completion_id and generated_code.
    """
    # TODO: implement actual request logic
    # for now, return placeholders
    return {
        "completion_id": "dummy_id",
        "generated_code": "# generated pandas code"
    }
