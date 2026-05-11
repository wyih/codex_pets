from __future__ import annotations

from pathlib import Path

from shinsekai_pet_host.petpack import PetPack


GLOBAL_COMPANION_RULES = """You are a desktop pet companion inside a Shinsekai-style host.
Answer as the selected pet while staying useful, concise, and original.
Never quote song lyrics. Never claim to be the real person or official character.
"""

MODE_RULES = {
    "chat": "Mode: chat. Keep the reply conversational and light.",
    "work": "Mode: work. Help with the task, ask for missing workspace details when needed, and keep actions explicit.",
}


def load_persona(pet: PetPack) -> str:
    if pet.persona and pet.persona.is_file():
        return pet.persona.read_text(encoding="utf-8").strip()
    return f"You are {pet.manifest.display_name}, a helpful desktop pet."


def load_dialogue(pet: PetPack) -> dict[str, list[str]]:
    if not pet.dialogue or not pet.dialogue.is_file():
        return {}
    return parse_dialogue_yaml_subset(pet.dialogue.read_text(encoding="utf-8"))


def compose_pet_prompt(pet: PetPack, user_message: str, *, mode: str) -> str:
    mode_rule = MODE_RULES.get(mode, MODE_RULES["chat"])
    return "\n\n".join(
        [
            load_persona(pet),
            GLOBAL_COMPANION_RULES,
            mode_rule,
            f"User message:\n{user_message}",
        ]
    )


def parse_dialogue_yaml_subset(text: str) -> dict[str, list[str]]:
    dialogue: dict[str, list[str]] = {}
    current_key: str | None = None
    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if not line.startswith(" ") and line.endswith(":"):
            current_key = line[:-1].strip()
            dialogue[current_key] = []
            continue
        stripped = line.strip()
        if current_key and stripped.startswith("- "):
            value = stripped[2:].strip()
            dialogue[current_key].append(_unquote(value))
            continue
        raise ValueError(f"Unsupported dialogue line: {raw_line}")
    return dialogue


def _unquote(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value

