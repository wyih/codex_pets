import subprocess
import sys
import unittest


def run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "shinsekai_pet_host.cli", *args],
        text=True,
        capture_output=True,
        check=False,
    )


class CliTests(unittest.TestCase):
    def test_list_command_shows_both_pets(self) -> None:
        result = run_cli("list")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("anaxa-sage", result.stdout)
        self.assertIn("mj-legends", result.stdout)

    def test_validate_command_passes(self) -> None:
        result = run_cli("validate")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("2 pet(s) ok", result.stdout)


if __name__ == "__main__":
    unittest.main()

