from pathlib import Path
import unittest

from shinsekai_pet_host.host_controller import PetHostController
from shinsekai_pet_host.petpack import PetRegistry
from shinsekai_pet_host.runtime import PetAnimator


ROOT = Path(__file__).resolve().parents[1]


class RuntimeTests(unittest.TestCase):
    def test_animator_maps_state_to_frame_rect(self) -> None:
        pet = PetRegistry([ROOT / "pets"]).discover()[0]
        frame = PetAnimator(pet.atlas).frame_at("running", 7)
        self.assertEqual(frame.row, 7)
        self.assertEqual(frame.index, 1)
        self.assertEqual(frame.x, pet.atlas.cell_width)
        self.assertEqual(frame.y, 7 * pet.atlas.cell_height)

    def test_controller_requires_workspace_for_work_mode(self) -> None:
        pet = PetRegistry([ROOT / "pets"]).discover()[0]
        controller = PetHostController(selected_pet_id=pet.manifest.id)
        controller.mode = "work"
        event = controller.prepare_send("change files", workspace="")
        self.assertFalse(event.ok)
        self.assertEqual(event.pet_state, "waiting")
        self.assertIn("workspace", event.message.lower())

    def test_controller_completes_success_and_failure(self) -> None:
        pet = PetRegistry([ROOT / "pets"]).discover()[0]
        controller = PetHostController(selected_pet_id=pet.manifest.id)
        start = controller.prepare_send("hello", workspace="")
        self.assertTrue(start.ok)
        self.assertEqual(controller.pet_state, "running")
        success = controller.complete(ok=True, message="done")
        self.assertEqual(success.pet_state, "review")
        failure = controller.complete(ok=False, message="failed")
        self.assertEqual(failure.pet_state, "failed")


if __name__ == "__main__":
    unittest.main()

