# Shinsekai Pet Host Design

Date: 2026-05-11

## Decision

Build an independent desktop pet host from the Shinsekai codebase. Shinsekai provides the desktop chat window, character presentation model, settings surface, plugin hooks, and Galgame-style interaction pattern. The new work adds a PetPack system for generated Codex pets and a Codex CLI bridge for chat and workspace tasks.

The first release supports the existing `anaxa-sage` and `mj-legends` pets, with a design that accepts more pets through the same package contract.

## Source Context

Shinsekai is a Python/PySide desktop assistant with a separate settings window and chat window. Its plugin guide describes in-process plugins, settings UI contributions, chat UI widgets, LLM adapters, and user input hooks. The local source has `ui/chat_ui/chat_ui.py`, `main.py`, `config/character_manager.py`, and `core/runtime/workers.py` as the main integration points.

Local pet assets already use a Codex atlas:

- `pets/anaxa-sage/pet.json`
- `pets/anaxa-sage/spritesheet.webp`
- `pets/mj-legends/pet.json`
- `pets/mj-legends/spritesheet.webp`

The atlas contract is 8 columns by 9 rows with rows mapped to `idle`, `running-right`, `running-left`, `waving`, `jumping`, `failed`, `waiting`, `running`, and `review`.

External reference links:

- Shinsekai homepage: https://rachelforster.github.io/Shinsekai/
- Shinsekai repository: https://github.com/RachelForster/Shinsekai
- Shinsekai plugin guide: https://github.com/RachelForster/Shinsekai/blob/main/docs/PLUGIN_DEVELOPER_GUIDE.md
- Anaxa profile reference: https://honkai-star-rail.fandom.com/wiki/Anaxa
- Michael Jackson biography reference: https://www.britannica.com/biography/Michael-Jackson

## Product Shape

The app behaves like a desktop companion:

- A transparent or lightly framed desktop window displays the selected pet.
- A compact dialogue panel shows the pet name, mode, status, and reply text.
- A selector allows switching between installed pets.
- The pet animates while Codex CLI runs, waits, succeeds, or fails.
- A mode toggle switches between chat mode and work mode.
- Codex CLI owns authentication through `codex login` and stores tokens in its existing location.

## Modes

### Chat Mode

Chat mode is the default. It is for casual conversation, small questions, and pet-like interaction.

Command shape:

```bash
codex exec --ephemeral --skip-git-repo-check "<prompt>"
```

The bridge sends a pet persona prompt plus the user message. The response is shown in the Shinsekai dialogue panel.

### Work Mode

Work mode is enabled manually. It requires a selected workspace path and a visible confirmation step before a task is submitted.

Command shape:

```bash
codex exec -C "<workspace>" "<prompt>"
```

The UI labels this mode clearly and stores its history separately from chat mode.

## Codex CLI Bridge

Add a backend module named `codex_bridge` with these responsibilities:

- `CodexAuthService`: runs `codex login status`, opens `codex login --device-auth` when setup is needed, and reports auth state.
- `CodexCommandBuilder`: builds safe argument arrays for chat and work mode.
- `CodexRunner`: launches the process with timeout, captures stdout/stderr, and emits lifecycle events.
- `CodexResponseParser`: extracts the final answer from plain output or JSONL output when enabled.
- `CodexBackend`: exposes one high-level `send(message, mode, pet, workspace)` API to the UI.

The bridge always uses argument arrays and subprocess APIs. It passes secrets through Codex CLI's existing auth store and avoids storing OAuth tokens in Shinsekai project files.

## PetPack Contract

The app loads pets from multiple directories:

- App bundled pets: `data/pets/`
- User pets: `~/.codex/shinsekai-pets/`
- Optional source pets during development: this repo's `pets/`

Package layout:

```text
pet-id/
  pet.json
  spritesheet.webp
  persona.md
  dialogue.yaml
  icon.webp
```

Manifest shape:

```json
{
  "schemaVersion": 1,
  "id": "anaxa-sage",
  "displayName": "那刻夏",
  "description": "A tiny Anaxa-inspired wind erudition scholar pet.",
  "assetFormat": "codex-8x9-atlas",
  "spritesheetPath": "spritesheet.webp",
  "personaPath": "persona.md",
  "dialoguePath": "dialogue.yaml",
  "iconPath": "icon.webp"
}
```

The v1 required fields are `schemaVersion`, `id`, `displayName`, `assetFormat`, and `spritesheetPath`. Persona, dialogue, and icon files are optional with generated defaults.

Future `assetFormat` values can include `single-portrait`, `multi-emotion-portrait`, and `spine`. The loader dispatches by format so new renderers can be added without changing the registry.

## Pet Runtime

Add these modules:

- `PetRegistry`: scans directories, reads manifests, deduplicates by `id`, and returns installable pets.
- `PetValidator`: checks manifest fields, local file paths, atlas dimensions, frame rows, transparent/chroma background, and optional persona/dialogue files.
- `PetLoader`: converts a PetPack into runtime metadata and animation frames.
- `PetAnimator`: maps lifecycle states to atlas rows and frame timers.
- `PetRuntime`: owns selected pet, current state, and UI signals.

Lifecycle mapping:

| Backend lifecycle | Pet state |
| --- | --- |
| App ready | `idle` |
| User greeting or pet selected | `waving` |
| Codex process running | `running` |
| Waiting for user confirmation | `waiting` |
| Response ready | `review` then `idle` |
| Process failed or timeout | `failed` |
| Manual drag left/right | `running-left` / `running-right` |

## UI Integration

Reuse the Shinsekai chat window and add a small Pet toolbar:

- Pet selector with icon and name.
- Mode segmented control: Chat / Work.
- Login status chip with setup action.
- Workspace picker visible in Work mode.
- Current status text: Ready, Thinking, Waiting, Reviewing, Failed.

Settings gets a Pet page:

- Installed pets list.
- Import PetPack zip.
- Validate selected pet.
- Open user pet directory.
- Persona preview.
- Dialogue preview.

The first implementation can add these directly to the fork. A later pass can move most of it into a Shinsekai plugin if the fork stabilizes the host APIs needed for animation and process state.

## Persona Design

Each pet owns a `persona.md` and optional `dialogue.yaml`. The bridge composes:

1. Pet persona.
2. Global companion rules.
3. Mode-specific instructions.
4. User message.

The persona is inspiration-based. It captures tone and interaction style while keeping every response original.

### 那刻夏 Persona

Reference basis:

- Anaxa is associated with Wind and Erudition.
- Profile references describe him as Anaxagoras, a scholar of the Grove of Epiphany, founder of the Nousporists, and one who challenges prophecy and the Coreflame of Reason.
- Local motion notes already encode a cool, precise, slightly unimpressed scholar.

Persona direction:

- Precise, sharp, intellectually proud.
- Uses short analytical observations and pointed questions.
- Treats uncertainty as material for classification and hypothesis.
- Shows care through accuracy, correction, and useful structure.
- Keeps a dry, restrained sense of humor.

Sample dialogue:

```yaml
idle:
  - "证据还在发芽。给我一个问题。"
running:
  - "正在拆解变量。保持安静会提升成功率。"
waiting:
  - "缺一条前提。补上它。"
review:
  - "结论已经成形，你可以检查它。"
failed:
  - "这个路径塌了。换一组假设。"
```

### MJ Legends Persona

Reference basis:

- Local asset notes define MJ Legends as a fan-made homage to classic stage-era looks and dance poses.
- Britannica describes Michael Jackson as a singer, songwriter, dancer, and one of the most influential entertainers of the late 20th and early 21st centuries, with influence across dance, concert touring, video presentation, and music production.

Persona direction:

- Warm, rhythmic, encouraging.
- Speaks like a rehearsal partner: precise about timing, generous about momentum.
- Frames work as performance practice: polish, repeat, find the groove.
- Shows confidence through focus and kindness.
- Avoids lyric quotes and exact real-person impersonation.

Sample dialogue:

```yaml
idle:
  - "节拍在这儿。准备好就开始。"
running:
  - "我在找那个最准的点。再给我一拍。"
waiting:
  - "你的下一句会决定动作。"
review:
  - "完成了。现在看它能不能站上舞台。"
failed:
  - "这一遍断拍了。我们重新踩准。"
```

## Data And History

Store user app state under Shinsekai's `data/` root or a user config directory:

```text
data/pet_host/
  settings.yaml
  history/
    anaxa-sage.chat.jsonl
    anaxa-sage.work.jsonl
    mj-legends.chat.jsonl
    mj-legends.work.jsonl
```

Settings include selected pet, selected mode, last workspace, user pet directories, and animation scale.

History records user message, pet id, mode, workspace, Codex CLI command metadata, response text, and timestamps. It stores command arguments with sensitive environment values redacted.

## Error Handling

- Missing Codex CLI: show setup text and `codex` path probe result.
- Logged out: show login action and keep pet in `waiting`.
- Login command failed: show stderr summary and set `failed`.
- Pet manifest invalid: keep the pet out of the selectable list and expose validation details in settings.
- Codex command timeout: terminate the process, set `failed`, and keep a retry action.
- Work mode without workspace: require workspace selection before send.

## Validation

Automated checks:

- PetPack manifest validation for both existing pets.
- Atlas loader checks dimensions and frame row counts.
- Codex command builder tests for chat and work mode argument arrays.
- Codex response parser tests for plain output and JSONL output.
- UI state transition tests for idle, running, waiting, review, failed.

Manual checks:

- `codex login status` displays current auth state.
- Chat mode returns a reply for each bundled pet.
- Work mode runs against a temporary workspace after explicit confirmation.
- Pet switching preserves mode and updates persona.
- Imported zip pet appears after validation.

## Implementation Phases

### Phase 1

- Create a Shinsekai fork/worktree.
- Add PetPack scanner, validator, and loader.
- Convert the two existing pets into v1 PetPacks with `persona.md` and `dialogue.yaml`.
- Add Codex auth status and Codex backend.
- Add pet selector and mode switch to Chat UI.
- Wire lifecycle states to animation rows.

### Phase 2

- Add Pet settings page with import, validate, and preview.
- Add zip import into `~/.codex/shinsekai-pets/`.
- Add per-pet history split by mode.
- Add more robust response parsing with `codex exec --json`.

### Phase 3

- Add more asset formats.
- Add more backends, such as OpenClaw or direct OpenAI API.
- Move stable pieces into a Shinsekai plugin when host APIs cover animation, process state, and pet registry well.

## Acceptance Criteria

- The app launches as an independent Shinsekai-derived desktop app.
- The user can choose `那刻夏` or `MJ Legends`.
- Both pets animate from their current atlas assets.
- Chat mode talks through Codex CLI using current Codex auth.
- Work mode requires a workspace and visible confirmation.
- More PetPacks can be added by placing a folder or importing a zip.
- Invalid PetPacks produce clear validation messages.
- Persona output visibly differs between 那刻夏 and MJ Legends.

