from __future__ import annotations

from dataclasses import dataclass
import json
import subprocess

from shinsekai_pet_host.backends import BackendConfig, BackendResult


@dataclass(frozen=True)
class CodexCommand:
    args: list[str]
    prompt: str
    mode: str


@dataclass(frozen=True)
class CodexAuthStatus:
    ok: bool
    message: str


class CodexCommandBuilder:
    def __init__(self, *, codex_bin: str = "codex") -> None:
        self.codex_bin = codex_bin

    def chat(self, prompt: str) -> CodexCommand:
        return CodexCommand(
            args=[self.codex_bin, "exec", "--ephemeral", "--skip-git-repo-check", prompt],
            prompt=prompt,
            mode="chat",
        )

    def work(self, prompt: str, workspace: str) -> CodexCommand:
        if not workspace:
            raise ValueError("workspace is required for work mode")
        return CodexCommand(
            args=[self.codex_bin, "exec", "-C", workspace, prompt],
            prompt=prompt,
            mode="work",
        )


class CodexResponseParser:
    @staticmethod
    def parse(output: str) -> str:
        last_assistant = ""
        for line in output.splitlines():
            line = line.strip()
            if not line.startswith("{"):
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            if event.get("role") == "assistant" and isinstance(event.get("content"), str):
                last_assistant = event["content"]
        return last_assistant or output.strip()


class CodexAuthService:
    def __init__(self, *, codex_bin: str = "codex", timeout_seconds: int = 30) -> None:
        self.codex_bin = codex_bin
        self.timeout_seconds = timeout_seconds

    def status(self) -> CodexAuthStatus:
        try:
            completed = subprocess.run(
                [self.codex_bin, "login", "status"],
                text=True,
                capture_output=True,
                timeout=self.timeout_seconds,
                check=False,
            )
        except OSError as exc:
            return CodexAuthStatus(False, str(exc))
        except subprocess.TimeoutExpired:
            return CodexAuthStatus(False, "codex login status timed out")
        message = (completed.stdout or completed.stderr).strip()
        return CodexAuthStatus(completed.returncode == 0, message)


class CodexCliBackend:
    provider_id = "codex-cli"

    def __init__(self, config: BackendConfig) -> None:
        self.config = config
        self.builder = CodexCommandBuilder(codex_bin=config.command or "codex")

    def send(self, message: str, *, system_prompt: str = "", mode: str = "chat", workspace: str = "") -> BackendResult:
        prompt = _join_prompt(system_prompt, message)
        command = self.builder.work(prompt, workspace) if mode == "work" else self.builder.chat(prompt)
        try:
            completed = subprocess.run(
                command.args,
                text=True,
                capture_output=True,
                timeout=self.config.timeout_seconds,
                check=False,
            )
        except subprocess.TimeoutExpired:
            return BackendResult("", ok=False, provider=self.provider_id, status="timeout", error="codex command timed out")
        except OSError as exc:
            return BackendResult("", ok=False, provider=self.provider_id, status="failed", error=str(exc))
        raw = completed.stdout or completed.stderr
        text = CodexResponseParser.parse(raw)
        return BackendResult(
            text=text,
            ok=completed.returncode == 0,
            provider=self.provider_id,
            status="complete" if completed.returncode == 0 else "failed",
            error="" if completed.returncode == 0 else (completed.stderr or "").strip(),
            raw=raw,
        )


def _join_prompt(system_prompt: str, message: str) -> str:
    return f"{system_prompt.strip()}\n\n{message.strip()}".strip() if system_prompt else message.strip()

