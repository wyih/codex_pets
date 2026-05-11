# Shinsekai Pet Host Phase 1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a testable Phase 1 Pet Host core that loads extensible PetPacks, talks through pluggable backends, and offers a small desktop/CLI preview path.

**Architecture:** Add a standalone `shinsekai_pet_host` Python package inside this repo. PetPack loading, backend providers, persona composition, CLI, and optional PySide UI are separate modules with tests around the pure-Python pieces.

**Tech Stack:** Python 3 stdlib, `unittest`, optional PySide6 for the preview UI, existing `.webp` pet assets, Codex CLI, OpenAI-compatible HTTP chat completions.

---

## File Structure

- Create `shinsekai_pet_host/__init__.py`: package exports.
- Create `shinsekai_pet_host/petpack.py`: manifest parsing, registry scanning, validation, atlas metadata.
- Create `shinsekai_pet_host/backends.py`: backend protocol, registry, config, result model.
- Create `shinsekai_pet_host/codex_cli.py`: Codex CLI command builder, auth status probe, runner, response parser.
- Create `shinsekai_pet_host/openai_compatible.py`: OpenAI-compatible request/response builder using `urllib`.
- Create `shinsekai_pet_host/persona.py`: persona/dialogue loading and prompt composition.
- Create `shinsekai_pet_host/cli.py`: `list`, `validate`, and `chat` commands.
- Create `shinsekai_pet_host/desktop_preview.py`: optional PySide6 desktop preview.
- Create `tests/test_petpack.py`, `tests/test_backends.py`, `tests/test_persona.py`, `tests/test_cli.py`.
- Modify `pets/anaxa-sage/pet.json`, `pets/mj-legends/pet.json`: v1 PetPack metadata.
- Create `pets/anaxa-sage/persona.md`, `pets/anaxa-sage/dialogue.yaml`, `pets/mj-legends/persona.md`, `pets/mj-legends/dialogue.yaml`.
- Modify `README.md`: document Phase 1 Pet Host commands.

## Task 1: PetPack Metadata And Registry

**Files:**
- Create: `shinsekai_pet_host/petpack.py`
- Test: `tests/test_petpack.py`
- Modify: `pets/anaxa-sage/pet.json`
- Modify: `pets/mj-legends/pet.json`

- [ ] **Step 1: Write failing tests**

```python
from pathlib import Path
from shinsekai_pet_host.petpack import PetRegistry, validate_petpack

ROOT = Path(__file__).resolve().parents[1]

def test_registry_finds_existing_pets():
    registry = PetRegistry([ROOT / "pets"])
    pets = registry.discover()
    assert [pet.manifest.id for pet in pets] == ["anaxa-sage", "mj-legends"]

def test_existing_petpacks_validate():
    registry = PetRegistry([ROOT / "pets"])
    for pet in registry.discover():
        report = validate_petpack(pet)
        assert report.ok, report.messages
        assert pet.manifest.asset_format == "codex-8x9-atlas"
        assert pet.atlas.columns == 8
        assert pet.atlas.rows == 9
```

- [ ] **Step 2: Run tests and verify failure**

Run: `python3 -m unittest tests.test_petpack -v`
Expected: failure with import error for `shinsekai_pet_host`.

- [ ] **Step 3: Implement PetPack parsing and validation**

Create dataclasses for manifest, atlas metadata, validation report, and registry scanning. Implement WebP dimension extraction with a RIFF VP8X/VP8L/VP8 parser so the repo has no Pillow dependency.

- [ ] **Step 4: Upgrade both `pet.json` files**

Add `schemaVersion`, `assetFormat`, `personaPath`, and `dialoguePath` while preserving the existing `id`, `displayName`, `description`, and `spritesheetPath`.

- [ ] **Step 5: Run tests**

Run: `python3 -m unittest tests.test_petpack -v`
Expected: 2 tests pass.

## Task 2: Persona And Dialogue Files

**Files:**
- Create: `shinsekai_pet_host/persona.py`
- Create: `pets/anaxa-sage/persona.md`
- Create: `pets/anaxa-sage/dialogue.yaml`
- Create: `pets/mj-legends/persona.md`
- Create: `pets/mj-legends/dialogue.yaml`
- Test: `tests/test_persona.py`

- [ ] **Step 1: Test persona composition**

Run: `python3 -m unittest tests.test_persona -v`
Expected: 2 tests pass after implementation.

- [ ] **Step 2: Implement persona loader**

Use a small YAML subset parser for `dialogue.yaml` and compose prompts from persona, companion rules, mode rules, and user message.

## Task 3: Backend Provider Registry

**Files:**
- Create: `shinsekai_pet_host/backends.py`
- Create: `shinsekai_pet_host/codex_cli.py`
- Create: `shinsekai_pet_host/openai_compatible.py`
- Test: `tests/test_backends.py`

- [ ] **Step 1: Test backend ids and builders**

Run: `python3 -m unittest tests.test_backends -v`
Expected: 4 tests pass after implementation.

- [ ] **Step 2: Implement default providers**

Register `codex-cli` and `openai-compatible`. Use subprocess argument arrays for Codex CLI and stdlib `urllib` for HTTP chat completions.

## Task 4: CLI And Optional Desktop Preview

**Files:**
- Create: `shinsekai_pet_host/cli.py`
- Create: `shinsekai_pet_host/desktop_preview.py`
- Test: `tests/test_cli.py`
- Modify: `README.md`

- [ ] **Step 1: Test CLI commands**

Run: `python3 -m unittest tests.test_cli -v`
Expected: 2 tests pass after implementation.

- [ ] **Step 2: Implement CLI and PySide preview**

Provide `list`, `validate`, `auth`, and `chat`. The PySide preview imports PySide6 lazily and displays the selected pet's first frame.

## Task 5: Full Verification And Commit

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Run all unit tests**

Run: `python3 -m unittest discover -v`
Expected: all tests pass.

- [ ] **Step 2: Run catalog validation**

Run: `python3 scripts/validate_catalog.py`
Expected: `catalog ok: 2 pet(s)`.

- [ ] **Step 3: Run CLI smoke checks**

Run:

```bash
python3 -m shinsekai_pet_host.cli list
python3 -m shinsekai_pet_host.cli validate
python3 -m shinsekai_pet_host.cli auth
```

Expected: pet list, `2 pet(s) ok`, and a Codex login status line.

