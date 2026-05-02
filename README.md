# Codex Pets

Fan-made animated pets for the Codex desktop app.

## Pets

| Pet | Folder | Preview |
| --- | --- | --- |
| 那刻夏 | `pets/anaxa-sage` | `previews/anaxa-sage/contact-sheet.png` |

## Install

Install one pet:

```bash
cp -R pets/anaxa-sage ~/.codex/pets/
```

Install with the helper:

```bash
./scripts/install_pet.sh anaxa-sage
```

Then open Codex, select `那刻夏`, and start a task to see the animations.

## Repo Layout

```text
pets/
  <pet-id>/
    pet.json
    spritesheet.webp
previews/
  <pet-id>/
    contact-sheet.png
    videos/
catalog.json
scripts/
```

Each pet folder is self-contained and ready to copy into `~/.codex/pets/`.

## Add A Pet

1. Create `pets/<pet-id>/pet.json` and `pets/<pet-id>/spritesheet.webp`.
2. Add `previews/<pet-id>/contact-sheet.png`.
3. Add preview videos under `previews/<pet-id>/videos/`.
4. Add the pet to `catalog.json`.
5. Run:

```bash
./scripts/validate_catalog.py
```

Keep assets GitHub-friendly. A finished Codex pet spritesheet is usually small enough for normal git storage.
