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

