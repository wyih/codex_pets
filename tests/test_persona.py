from pathlib import Path
import unittest

from shinsekai_pet_host.petpack import PetRegistry
from shinsekai_pet_host.persona import compose_pet_prompt, load_dialogue


ROOT = Path(__file__).resolve().parents[1]


class PersonaTests(unittest.TestCase):
    def test_persona_prompt_differs_by_pet(self) -> None:
        pets = {pet.manifest.id: pet for pet in PetRegistry([ROOT / "pets"]).discover()}
        anaxa = compose_pet_prompt(pets["anaxa-sage"], "解释一下状态机", mode="chat")
        mj = compose_pet_prompt(pets["mj-legends"], "解释一下状态机", mode="chat")
        self.assertIn("那刻夏", anaxa)
        self.assertTrue("rehearsal" in mj.lower() or "stage" in mj.lower())
        self.assertNotEqual(anaxa, mj)

    def test_dialogue_loads_without_yaml_dependency(self) -> None:
        pet = PetRegistry([ROOT / "pets"]).discover()[0]
        dialogue = load_dialogue(pet)
        self.assertIn("idle", dialogue)
        self.assertTrue(dialogue["idle"])


if __name__ == "__main__":
    unittest.main()

