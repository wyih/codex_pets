from __future__ import annotations

from pathlib import Path
import sys

from shinsekai_pet_host.petpack import PetRegistry, read_webp_dimensions


def main() -> int:
    try:
        from PySide6.QtCore import Qt
        from PySide6.QtGui import QPixmap
        from PySide6.QtWidgets import QApplication, QComboBox, QLabel, QVBoxLayout, QWidget
    except ImportError:
        print("PySide6 is not installed. Install Shinsekai dependencies to run the desktop preview.", file=sys.stderr)
        return 1

    root = Path(__file__).resolve().parents[1]
    pets = PetRegistry([root / "pets", Path.home() / ".codex" / "shinsekai-pets"]).discover()
    app = QApplication(sys.argv)
    window = QWidget()
    window.setWindowTitle("Shinsekai Pet Host Preview")
    layout = QVBoxLayout(window)
    selector = QComboBox()
    image = QLabel()
    image.setAlignment(Qt.AlignmentFlag.AlignCenter)
    image.setMinimumSize(256, 256)

    for pet in pets:
        selector.addItem(f"{pet.manifest.display_name} ({pet.manifest.id})", pet)

    def show_current() -> None:
        pet = selector.currentData()
        if pet is None:
            return
        pixmap = QPixmap(str(pet.spritesheet))
        width, height = read_webp_dimensions(pet.spritesheet)
        frame = pixmap.copy(0, 0, width // 8, height // 9)
        image.setPixmap(frame.scaled(220, 240, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))

    selector.currentIndexChanged.connect(show_current)
    layout.addWidget(selector)
    layout.addWidget(image)
    show_current()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())

