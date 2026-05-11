from __future__ import annotations

import json
import os
from urllib import error, request

from shinsekai_pet_host.backends import BackendConfig, BackendResult


def build_chat_request(model: str, system_prompt: str, user_message: str) -> dict:
    messages = []
    if system_prompt.strip():
        messages.append({"role": "system", "content": system_prompt.strip()})
    messages.append({"role": "user", "content": user_message.strip()})
    return {"model": model, "messages": messages, "stream": False}


def parse_chat_response(body: str) -> str:
    data = json.loads(body)
    try:
        return data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise ValueError("OpenAI-compatible response did not include choices[0].message.content") from exc


class OpenAICompatibleBackend:
    provider_id = "openai-compatible"

    def __init__(self, config: BackendConfig) -> None:
        self.config = config

    def send(self, message: str, *, system_prompt: str = "", mode: str = "chat", workspace: str = "") -> BackendResult:
        endpoint = (self.config.endpoint or os.environ.get("PET_HOST_OPENAI_BASE_URL") or "").rstrip("/")
        api_key = self.config.api_key or os.environ.get("PET_HOST_OPENAI_API_KEY", "")
        model = self.config.model or os.environ.get("PET_HOST_OPENAI_MODEL", "")
        if not endpoint or not api_key or not model:
            return BackendResult(
                "",
                ok=False,
                provider=self.provider_id,
                status="failed",
                error="endpoint, api key, and model are required for openai-compatible",
            )
        payload = json.dumps(build_chat_request(model, system_prompt, message)).encode("utf-8")
        req = request.Request(
            f"{endpoint}/v1/chat/completions",
            data=payload,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with request.urlopen(req, timeout=self.config.timeout_seconds) as response:
                raw = response.read().decode("utf-8")
        except error.HTTPError as exc:
            raw_error = exc.read().decode("utf-8", errors="replace")
            return BackendResult("", ok=False, provider=self.provider_id, status="failed", error=raw_error)
        except OSError as exc:
            return BackendResult("", ok=False, provider=self.provider_id, status="failed", error=str(exc))
        try:
            text = parse_chat_response(raw)
        except ValueError as exc:
            return BackendResult("", ok=False, provider=self.provider_id, status="failed", error=str(exc), raw=raw)
        return BackendResult(text, ok=True, provider=self.provider_id, raw=raw)

