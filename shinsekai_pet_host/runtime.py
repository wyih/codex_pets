from __future__ import annotations

from dataclasses import dataclass

from shinsekai_pet_host.petpack import AtlasMetadata


STATE_ROWS: dict[str, tuple[int, int]] = {
    "idle": (0, 6),
    "running-right": (1, 8),
    "running-left": (2, 8),
    "waving": (3, 4),
    "jumping": (4, 5),
    "failed": (5, 8),
    "waiting": (6, 6),
    "running": (7, 6),
    "review": (8, 6),
}


@dataclass(frozen=True)
class AnimationFrame:
    state: str
    row: int
    index: int
    x: int
    y: int
    width: int
    height: int


@dataclass(frozen=True)
class AmbientState:
    state: str
    start_tick: int
    duration_ticks: int


DEFAULT_AMBIENT_SEQUENCE: tuple[tuple[str, int], ...] = (
    ("idle", 8),
    ("waving", 4),
    ("idle", 6),
    ("jumping", 5),
    ("idle", 7),
    ("running-right", 8),
    ("idle", 5),
    ("running-left", 8),
    ("waiting", 6),
)


class AmbientStateScheduler:
    def __init__(self, sequence: list[tuple[str, int]] | tuple[tuple[str, int], ...] | None = None):
        self.sequence = tuple(sequence or DEFAULT_AMBIENT_SEQUENCE)
        if not self.sequence:
            raise ValueError("ambient sequence must contain at least one state")
        for state, duration in self.sequence:
            if duration <= 0:
                raise ValueError(f"ambient state {state} must have a positive duration")
        self.total_ticks = sum(duration for _, duration in self.sequence)

    def state_at(self, tick: int) -> AmbientState:
        position = tick % self.total_ticks
        start_tick = tick - position
        elapsed = 0
        for state, duration in self.sequence:
            end = elapsed + duration
            if position < end:
                return AmbientState(state=state, start_tick=start_tick + elapsed, duration_ticks=duration)
            elapsed = end
        state, duration = self.sequence[-1]
        return AmbientState(state=state, start_tick=start_tick + elapsed - duration, duration_ticks=duration)


class PetAnimator:
    def __init__(self, atlas: AtlasMetadata):
        self.atlas = atlas

    def frame_count(self, state: str) -> int:
        return self._state_info(state)[1]

    def frame_at(self, state: str, tick: int) -> AnimationFrame:
        row, count = self._state_info(state)
        index = tick % count
        return AnimationFrame(
            state=state,
            row=row,
            index=index,
            x=index * self.atlas.cell_width,
            y=row * self.atlas.cell_height,
            width=self.atlas.cell_width,
            height=self.atlas.cell_height,
        )

    def _state_info(self, state: str) -> tuple[int, int]:
        return STATE_ROWS.get(state, STATE_ROWS["idle"])
