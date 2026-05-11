from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class HostEvent:
    ok: bool
    pet_state: str
    message: str


@dataclass
class PetHostController:
    selected_pet_id: str
    backend_id: str = "codex-cli"
    mode: str = "chat"
    workspace: str = ""
    pet_state: str = "idle"
    status_text: str = "Ready"

    def select_pet(self, pet_id: str) -> HostEvent:
        self.selected_pet_id = pet_id
        self.pet_state = "waving"
        self.status_text = f"Selected {pet_id}"
        return HostEvent(True, self.pet_state, self.status_text)

    def prepare_send(self, message: str, *, workspace: str) -> HostEvent:
        if not message.strip():
            self.pet_state = "waiting"
            self.status_text = "Message is required"
            return HostEvent(False, self.pet_state, self.status_text)
        self.workspace = workspace
        if self.mode == "work" and not workspace.strip():
            self.pet_state = "waiting"
            self.status_text = "Workspace is required for work mode"
            return HostEvent(False, self.pet_state, self.status_text)
        self.pet_state = "running"
        self.status_text = "Thinking"
        return HostEvent(True, self.pet_state, self.status_text)

    def complete(self, *, ok: bool, message: str) -> HostEvent:
        self.pet_state = "review" if ok else "failed"
        self.status_text = "Ready" if ok else "Failed"
        return HostEvent(ok, self.pet_state, message)

