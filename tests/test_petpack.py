from pathlib import Path
import unittest

from shinsekai_pet_host.petpack import PetRegistry, validate_petpack


ROOT = Path(__file__).resolve().parents[1]


class PetPackTests(unittest.TestCase):
    def test_registry_finds_existing_pets(self) -> None:
        registry = PetRegistry([ROOT / "pets"])
        pets = registry.discover()
        self.assertEqual([pet.manifest.id for pet in pets], ["anaxa-sage", "mj-legends"])

    def test_existing_petpacks_validate(self) -> None:
        registry = PetRegistry([ROOT / "pets"])
        for pet in registry.discover():
            report = validate_petpack(pet)
            self.assertTrue(report.ok, report.messages)
            self.assertEqual(pet.manifest.asset_format, "codex-8x9-atlas")
            self.assertEqual(pet.atlas.columns, 8)
            self.assertEqual(pet.atlas.rows, 9)


if __name__ == "__main__":
    unittest.main()

