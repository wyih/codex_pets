import unittest

from shinsekai_pet_host.desktop_preview import _bubble_preview


class DesktopPreviewTests(unittest.TestCase):
    def test_bubble_preview_clamps_long_text(self) -> None:
        text = "A" * 400
        preview = _bubble_preview(text)
        self.assertLessEqual(len(preview), 99)
        self.assertTrue(preview.endswith("..."))

    def test_bubble_preview_preserves_short_text(self) -> None:
        self.assertEqual(_bubble_preview("short reply"), "short reply")

    def test_bubble_preview_collapses_multiline_text(self) -> None:
        self.assertEqual(_bubble_preview("first line\n\nsecond   line"), "first line second line")


if __name__ == "__main__":
    unittest.main()
