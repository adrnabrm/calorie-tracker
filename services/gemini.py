import base64
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
    try:
        interaction = client.interactions.create(
            model=MODEL,
            input=payload,
            response_format={
                "type": "text",
                "mime_type": "application/json",
                "schema": schema.model_json_schema(),
            },
        )
        return schema.model_validate_json(interaction.output_text)
    except Exception as e:
        raise GeminiError("Gemini request failed. Try again.") from e
