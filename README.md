# Codex Pets

Fan-made animated pets for the Codex desktop app.

## Preview

### 那刻夏

![那刻夏 contact sheet](previews/anaxa-sage/contact-sheet.png)

| Idle | Waiting | Review | Run |
| --- | --- | --- | --- |
| <img src="previews/anaxa-sage/gifs/idle.gif" width="160" alt="那刻夏 idle animation"> | <img src="previews/anaxa-sage/gifs/waiting.gif" width="160" alt="那刻夏 waiting animation"> | <img src="previews/anaxa-sage/gifs/review.gif" width="160" alt="那刻夏 review animation"> | <img src="previews/anaxa-sage/gifs/running-right.gif" width="160" alt="那刻夏 running animation"> |

Full MP4 previews live in `previews/anaxa-sage/videos/`.

## Pets

| Pet | Folder | Preview |
| --- | --- | --- |
| 那刻夏 | `pets/anaxa-sage` | [contact sheet](previews/anaxa-sage/contact-sheet.png) |

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
    gifs/
    videos/
catalog.json
scripts/
```

Each pet folder is self-contained and ready to copy into `~/.codex/pets/`.

## Add A Pet

1. Create `pets/<pet-id>/pet.json` and `pets/<pet-id>/spritesheet.webp`.
2. Add `previews/<pet-id>/contact-sheet.png`.
3. Add preview GIFs under `previews/<pet-id>/gifs/`.
4. Add preview videos under `previews/<pet-id>/videos/`.
5. Add the pet to `catalog.json`.
6. Run:

```bash
./scripts/validate_catalog.py
```

Keep assets GitHub-friendly. A finished Codex pet spritesheet is usually small enough for normal git storage.
