import base64
import json
import os

import anthropic

DEFAULT_MODEL = os.environ.get("LOG_MODEL", "claude-sonnet-5")

IMAGE_MEDIA_TYPES = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg"}


class LogLLM:
    def __init__(self, model: str = DEFAULT_MODEL):
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError(
                "ANTHROPIC_API_KEY is not set. Copy .env.example to .env and add your key."
            )
        self._client = anthropic.Anthropic(api_key=api_key)
        self._model = model

    def complete_json(self, system: str, user: str, max_tokens: int = 1500) -> dict:
        """Same truncation-aware retry as the AI Tutor's client.py: a response
        cut off by max_tokens gets a doubled budget (capped at 8192) since
        resending the same budget would truncate at the identical point again;
        anything else (extra prose, markdown fences) gets a stricter reminder
        instead. Truncation mid-thinking-block (no text emitted at all) is
        folded into the same retry rather than raising immediately."""
        text = None
        for attempt in range(2):
            message = self._client.messages.create(
                model=self._model,
                max_tokens=max_tokens,
                system=system,
                messages=[{"role": "user", "content": user}],
            )
            text = _find_text_block(message)
            if text is not None:
                text = _strip_code_fence(text.strip())
                try:
                    return json.loads(text)
                except json.JSONDecodeError:
                    pass

            if attempt == 0:
                if message.stop_reason == "max_tokens":
                    max_tokens = min(max_tokens * 2, 8192)
                else:
                    user = user + "\n\nReminder: respond with ONLY valid JSON, no prose, no markdown fences."
                continue

            if text is None:
                raise ValueError(f"LLM response contained no text block (stop_reason={message.stop_reason}).")
            raise ValueError(f"LLM did not return valid JSON (stop_reason={message.stop_reason}):\n{text}")

    def transcribe(self, file_bytes: bytes, extension: str, prompt: str) -> str:
        """OCR a photo/export of handwritten notes (image or PDF) into plain
        text, for the 'upload from iPad/tablet' path instead of typing."""
        extension = extension.lower().lstrip(".")
        b64 = base64.b64encode(file_bytes).decode("ascii")

        if extension == "pdf":
            content_block = {
                "type": "document",
                "source": {"type": "base64", "media_type": "application/pdf", "data": b64},
            }
        elif extension in IMAGE_MEDIA_TYPES:
            content_block = {
                "type": "image",
                "source": {"type": "base64", "media_type": IMAGE_MEDIA_TYPES[extension], "data": b64},
            }
        else:
            raise ValueError(f"Unsupported file type for transcription: .{extension}")

        message = self._client.messages.create(
            model=self._model,
            max_tokens=2000,
            messages=[{
                "role": "user",
                "content": [content_block, {"type": "text", "text": prompt}],
            }],
        )
        text = _find_text_block(message)
        return text.strip() if text else ""


def _find_text_block(message) -> str | None:
    for block in message.content:
        if block.type == "text":
            return block.text
    return None


def _strip_code_fence(text: str) -> str:
    if text.startswith("```"):
        lines = text.splitlines()
        lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        return "\n".join(lines).strip()
    return text
