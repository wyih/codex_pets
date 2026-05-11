from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Protocol


@dataclass(frozen=True)
class BackendConfig:
    provider: str
    model: str = ""
    endpoint: str = ""
    api_key: str = ""
    command: str = "codex"
    timeout_seconds: int = 120
    extra: dict[str, str] = field(default_factory=dict)

    def redacted(self) -> dict[str, object]:
        return {
            "provider": self.provider,
            "model": self.model,
            "endpoint": self.endpoint,
            "api_key": "***" if self.api_key else "",
            "command": self.command,
            "timeout_seconds": self.timeout_seconds,
            "extra": {key: ("***" if "key" in key.lower() or "token" in key.lower() else value) for key, value in self.extra.items()},
        }


@dataclass(frozen=True)
class BackendResult:
    text: str
    ok: bool = True
    provider: str = ""
    status: str = "complete"
    error: str = ""
    raw: str = ""


class ChatBackend(Protocol):
    provider_id: str

    def send(self, message: str, *, system_prompt: str = "", mode: str = "chat", workspace: str = "") -> BackendResult:
        ...


BackendFactory = Callable[[BackendConfig], ChatBackend]


class BackendProviderRegistry:
    def __init__(self) -> None:
        self._factories: dict[str, BackendFactory] = {}

    def register(self, provider_id: str, factory: BackendFactory) -> None:
        self._factories[provider_id] = factory

    def ids(self) -> list[str]:
        return sorted(self._factories)

    def create(self, config: BackendConfig) -> ChatBackend:
        try:
            factory = self._factories[config.provider]
        except KeyError as exc:
            raise ValueError(f"Unknown backend provider: {config.provider}") from exc
        return factory(config)

    @classmethod
    def default(cls) -> "BackendProviderRegistry":
        from shinsekai_pet_host.codex_cli import CodexCliBackend
        from shinsekai_pet_host.openai_compatible import OpenAICompatibleBackend

        registry = cls()
        registry.register("codex-cli", CodexCliBackend)
        registry.register("openai-compatible", OpenAICompatibleBackend)
        return registry

