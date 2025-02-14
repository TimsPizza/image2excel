"""Module providing a self-correction mechanism for the image-to-Excel flow."""

from .request import active_sessions, send_request
from .prompt import get_error_prompt, get_feedback_prompt, get_initial_prompt

def init_session(session_id: str, initial_prompt: str) -> None:
    """
    Initialize a session with a unique session_id and store the initial prompt.
    """
    active_sessions[session_id] = {
        "prompt": initial_prompt,
        "completion_id": None,
    }



def iterate_session(session_id: str, error_msg: str = None, user_feedback: str = None) -> str:
    """
    Append detailed error or feedback prompts to the existing session prompt and request a new code generation from the AI model.
    Reuse completion_id to maintain context.

    :param session_id: Identifier for the session.
    :param error_msg: Error information from code execution.
    :param user_feedback: Feedback provided by the user.
    :return: Generated code as a string.
    """
    session_data = active_sessions[session_id]

    if error_msg:
        session_data["prompt"] += "\n" + get_error_prompt(error_msg)
    if user_feedback:
        session_data["prompt"] += "\n" + get_feedback_prompt(user_feedback)

    response = send_request(
        prompt=session_data["prompt"],
        completion_id=session_data["completion_id"]
    )
    session_data["completion_id"] = response["completion_id"]
    return response["generated_code"]
