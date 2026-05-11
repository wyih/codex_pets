from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Iterable


REQUIRED_ATLAS_COLUMNS = 8
REQUIRED_ATLAS_ROWS = 9
ASSET_FORMAT_CODEX_ATLAS = "codex-8x9-atlas"


@dataclass(frozen=True)
class PetManifest:
    schema_version: int
    id: str
    display_name: str
    description: str
    asset_format: str
    spritesheet_path: str
    persona_path: str | None = None
    dialogue_path: str | None = None
    icon_path: str | None = None

    @classmethod
    def from_json(cls, data: dict) -> "PetManifest":
        return cls(
            schema_version=int(data.get("schemaVersion", 1)),
            id=str(data["id"]),
            display_name=str(data.get("displayName", data["id"])),
            description=str(data.get("description", "")),
            asset_format=str(data.get("assetFormat", ASSET_FORMAT_CODEX_ATLAS)),
            spritesheet_path=str(data.get("spritesheetPath", "spritesheet.webp")),
            persona_path=data.get("personaPath"),
            dialogue_path=data.get("dialoguePath"),
            icon_path=data.get("iconPath"),
        )


@dataclass(frozen=True)
class AtlasMetadata:
    width: int
    height: int
    columns: int
    rows: int
    cell_width: int
    cell_height: int


@dataclass(frozen=True)
class PetPack:
    root: Path
    manifest_path: Path
    manifest: PetManifest
    atlas: AtlasMetadata

    @property
    def spritesheet(self) -> Path:
        return self.root / self.manifest.spritesheet_path

    @property
    def persona(self) -> Path | None:
        return self.root / self.manifest.persona_path if self.manifest.persona_path else None

    @property
    def dialogue(self) -> Path | None:
        return self.root / self.manifest.dialogue_path if self.manifest.dialogue_path else None


@dataclass(frozen=True)
class ValidationReport:
    ok: bool
    messages: list[str]


class PetRegistry:
    def __init__(self, roots: Iterable[Path | str]):
        self.roots = [Path(root).expanduser().resolve() for root in roots]

    def discover(self) -> list[PetPack]:
        pets: list[PetPack] = []
        seen: set[str] = set()
        for root in self.roots:
            if not root.is_dir():
                continue
            for manifest_path in sorted(root.glob("*/pet.json")):
                pet = load_petpack(manifest_path.parent)
                if pet.manifest.id in seen:
                    continue
                seen.add(pet.manifest.id)
                pets.append(pet)
        return pets


def load_petpack(root: Path | str) -> PetPack:
    pet_root = Path(root).expanduser().resolve()
    manifest_path = pet_root / "pet.json"
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest = PetManifest.from_json(data)
    width, height = read_webp_dimensions(pet_root / manifest.spritesheet_path)
    atlas = AtlasMetadata(
        width=width,
        height=height,
        columns=REQUIRED_ATLAS_COLUMNS,
        rows=REQUIRED_ATLAS_ROWS,
        cell_width=width // REQUIRED_ATLAS_COLUMNS,
        cell_height=height // REQUIRED_ATLAS_ROWS,
    )
    return PetPack(root=pet_root, manifest_path=manifest_path, manifest=manifest, atlas=atlas)


def validate_petpack(pet: PetPack) -> ValidationReport:
    messages: list[str] = []
    if pet.manifest.schema_version != 1:
        messages.append(f"{pet.manifest.id}: unsupported schemaVersion {pet.manifest.schema_version}")
    if pet.manifest.asset_format != ASSET_FORMAT_CODEX_ATLAS:
        messages.append(f"{pet.manifest.id}: unsupported assetFormat {pet.manifest.asset_format}")
    if not pet.spritesheet.is_file():
        messages.append(f"{pet.manifest.id}: missing {pet.manifest.spritesheet_path}")
    if pet.atlas.width % REQUIRED_ATLAS_COLUMNS:
        messages.append(f"{pet.manifest.id}: atlas width {pet.atlas.width} is not divisible by 8")
    if pet.atlas.height % REQUIRED_ATLAS_ROWS:
        messages.append(f"{pet.manifest.id}: atlas height {pet.atlas.height} is not divisible by 9")
    if pet.manifest.persona_path and not (pet.root / pet.manifest.persona_path).is_file():
        messages.append(f"{pet.manifest.id}: missing {pet.manifest.persona_path}")
    if pet.manifest.dialogue_path and not (pet.root / pet.manifest.dialogue_path).is_file():
        messages.append(f"{pet.manifest.id}: missing {pet.manifest.dialogue_path}")
    return ValidationReport(ok=not messages, messages=messages)


def read_webp_dimensions(path: Path) -> tuple[int, int]:
    data = path.read_bytes()
    if len(data) < 30 or data[:4] != b"RIFF" or data[8:12] != b"WEBP":
        raise ValueError(f"{path} is not a WebP file")
    offset = 12
    while offset + 8 <= len(data):
        chunk = data[offset : offset + 4]
        size = int.from_bytes(data[offset + 4 : offset + 8], "little")
        start = offset + 8
        payload = data[start : start + size]
        if chunk == b"VP8X" and len(payload) >= 10:
            width = 1 + int.from_bytes(payload[4:7], "little")
            height = 1 + int.from_bytes(payload[7:10], "little")
            return width, height
        if chunk == b"VP8L" and len(payload) >= 5:
            bits = int.from_bytes(payload[1:5], "little")
            width = (bits & 0x3FFF) + 1
            height = ((bits >> 14) & 0x3FFF) + 1
            return width, height
        if chunk == b"VP8 " and len(payload) >= 10:
            width = int.from_bytes(payload[6:8], "little") & 0x3FFF
            height = int.from_bytes(payload[8:10], "little") & 0x3FFF
            return width, height
        offset = start + size + (size % 2)
    raise ValueError(f"{path} does not contain a supported WebP size chunk")

