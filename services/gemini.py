import base64
import traceback
from typing import TypeVar

from google import genai
from pydantic import BaseModel

from utils.config import GEMINI_API_KEY

MODEL = "gemini-3.1-flash-lite"
client = genai.Client(api_key=GEMINI_API_KEY)

T = TypeVar("T", bound=BaseModel)


class GeminiError(Exception):
    pass


def generate(
    prompt: str,
    schema: type[T],
    image_bytes: bytes | None = None,
    mime_type: str = "image/jpeg",
    *,
    model: str = MODEL,
    thinking_level: str | None = None,
) -> T:
    payload: list[dict] = [{"type": "text", "text": prompt}]
    if image_bytes is not None:
        payload.append(
            {
                "type": "image",
                "data": base64.b64encode(image_bytes).decode("utf-8"),
                "mime_type": mime_type,
            }
        )
    kwargs: dict = {
        "model": model,
        "input": payload,
        "response_format": {
            "type": "text",
            "mime_type": "application/json",
            "schema": schema.model_json_schema(),
        },
    }
    if thinking_level is not None:
        kwargs["generation_config"] = {"thinking_level": thinking_level}
    try:
        interaction = client.interactions.create(**kwargs)
        text = interaction.output_text
        if not text:
            raise ValueError("empty output")
        return schema.model_validate_json(text)
    except Exception as e:
        traceback.print_exception(e)
        raise GeminiError(f"Gemini request failed. {e}") from e
