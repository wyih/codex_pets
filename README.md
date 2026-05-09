# Codex Pets

Fan-made animated pets for the Codex desktop app.

## Preview

### 那刻夏

![那刻夏 contact sheet](previews/anaxa-sage/contact-sheet.png)

| Idle | Waiting | Review | Run |
| --- | --- | --- | --- |
| <img src="previews/anaxa-sage/gifs/idle.gif" width="160" alt="那刻夏 idle animation"> | <img src="previews/anaxa-sage/gifs/waiting.gif" width="160" alt="那刻夏 waiting animation"> | <img src="previews/anaxa-sage/gifs/review.gif" width="160" alt="那刻夏 review animation"> | <img src="previews/anaxa-sage/gifs/running-right.gif" width="160" alt="那刻夏 running animation"> |

Full MP4 previews live in `previews/anaxa-sage/videos/`.

### MJ Legends

![MJ Legends contact sheet](previews/mj-legends/contact-sheet.png)

| Billie Jean | Bad | Smooth Criminal | Thriller |
| --- | --- | --- | --- |
| <img src="previews/mj-legends/gifs/idle.gif" width="160" alt="MJ Legends Billie Jean idle animation"> | <img src="previews/mj-legends/gifs/running-right.gif" width="160" alt="MJ Legends Bad running animation"> | <img src="previews/mj-legends/gifs/jumping.gif" width="160" alt="MJ Legends Smooth Criminal jumping animation"> | <img src="previews/mj-legends/gifs/failed.gif" width="160" alt="MJ Legends Thriller failed animation"> |

Full MP4 previews live in `previews/mj-legends/videos/`.

## Pets

| Pet | Folder | Preview |
| --- | --- | --- |
| 那刻夏 | `pets/anaxa-sage` | [contact sheet](previews/anaxa-sage/contact-sheet.png) |
| MJ Legends | `pets/mj-legends` | [contact sheet](previews/mj-legends/contact-sheet.png) |

## Install

Install one pet:

```bash
cp -R pets/anaxa-sage ~/.codex/pets/
# or
cp -R pets/mj-legends ~/.codex/pets/
```

Install with the helper:

```bash
./scripts/install_pet.sh anaxa-sage
# or
./scripts/install_pet.sh mj-legends
```

Then open Codex, select the installed pet, and start a task to see the animations.

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
