import unittest

from shinsekai_pet_host.qt_doctor import _repair_hint


class QtDoctorTests(unittest.TestCase):
    def test_repair_hint_uses_uv_and_reinstalls_qt_packages(self) -> None:
        hint = _repair_hint()
        self.assertIn("uv sync --extra desktop", hint)
        self.assertIn("--reinstall-package PySide6", hint)
        self.assertIn("--reinstall-package shiboken6", hint)


if __name__ == "__main__":
    unittest.main()

