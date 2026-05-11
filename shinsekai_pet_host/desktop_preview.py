from __future__ import annotations

from pathlib import Path
import sys

from shinsekai_pet_host.backends import BackendConfig, BackendProviderRegistry, BackendResult
from shinsekai_pet_host.codex_cli import CodexAuthService
from shinsekai_pet_host.host_controller import PetHostController
from shinsekai_pet_host.persona import compose_pet_prompt
from shinsekai_pet_host.petpack import PetPack, PetRegistry
from shinsekai_pet_host.runtime import PetAnimator


def main() -> int:
    try:
        from PySide6.QtCore import QThread, QTimer, Qt, Signal
        from PySide6.QtGui import QPixmap
        from PySide6.QtWidgets import (
            QApplication,
            QComboBox,
            QHBoxLayout,
            QLabel,
            QLineEdit,
            QMessageBox,
            QPushButton,
            QTextEdit,
            QVBoxLayout,
            QWidget,
        )
    except ImportError:
        print("PySide6 is not installed. Install Shinsekai dependencies to run the desktop preview.", file=sys.stderr)
        return 1

    root = Path(__file__).resolve().parents[1]
    pets = PetRegistry([root / "pets", Path.home() / ".codex" / "shinsekai-pets"]).discover()
    if not pets:
        print("No PetPacks found.", file=sys.stderr)
        return 1

    class SendWorker(QThread):
        completed = Signal(object)

        def __init__(self, pet: PetPack, backend_id: str, mode: str, workspace: str, message: str) -> None:
            super().__init__()
            self.pet = pet
            self.backend_id = backend_id
            self.mode = mode
            self.workspace = workspace
            self.message = message

        def run(self) -> None:
            config = BackendConfig(provider=self.backend_id)
            backend = BackendProviderRegistry.default().create(config)
            prompt = compose_pet_prompt(self.pet, self.message, mode=self.mode)
            result = backend.send(prompt, mode=self.mode, workspace=self.workspace)
            self.completed.emit(result)

    app = QApplication(sys.argv)
    window = QWidget()
    window.setWindowTitle("Shinsekai Pet Host")
    layout = QVBoxLayout(window)

    top_row = QHBoxLayout()
    selector = QComboBox()
    backend_selector = QComboBox()
    mode_selector = QComboBox()
    status = QLabel("Ready")
    auth_button = QPushButton("Auth")
    for provider_id in BackendProviderRegistry.default().ids():
        backend_selector.addItem(provider_id, provider_id)
    mode_selector.addItem("Chat", "chat")
    mode_selector.addItem("Work", "work")

    image = QLabel()
    image.setAlignment(Qt.AlignmentFlag.AlignCenter)
    image.setMinimumSize(256, 256)
    workspace = QLineEdit()
    workspace.setPlaceholderText("Workspace for Work mode")
    message = QTextEdit()
    message.setPlaceholderText("Talk to the selected pet")
    message.setMinimumHeight(90)
    send = QPushButton("Send")
    reply = QTextEdit()
    reply.setReadOnly(True)
    reply.setMinimumHeight(140)

    for pet in pets:
        selector.addItem(f"{pet.manifest.display_name} ({pet.manifest.id})", pet)

    controller = PetHostController(selected_pet_id=pets[0].manifest.id)
    tick = {"value": 0}
    state = {"pet_state": "idle", "worker": None}

    def current_pet() -> PetPack:
        pet = selector.currentData()
        return pet if pet is not None else pets[0]

    def set_pet_state(pet_state: str) -> None:
        state["pet_state"] = pet_state
        tick["value"] = 0
        render_frame()

    def render_frame() -> None:
        pet = current_pet()
        pixmap = QPixmap(str(pet.spritesheet))
        frame_info = PetAnimator(pet.atlas).frame_at(state["pet_state"], tick["value"])
        frame = pixmap.copy(frame_info.x, frame_info.y, frame_info.width, frame_info.height)
        image.setPixmap(frame.scaled(220, 240, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))

    def advance_frame() -> None:
        tick["value"] += 1
        render_frame()

    def on_pet_changed() -> None:
        event = controller.select_pet(current_pet().manifest.id)
        status.setText(event.message)
        set_pet_state(event.pet_state)

    def on_auth_clicked() -> None:
        auth = CodexAuthService().status()
        status.setText(auth.message)
        set_pet_state("review" if auth.ok else "failed")

    def on_send_clicked() -> None:
        pet = current_pet()
        mode = mode_selector.currentData()
        backend_id = backend_selector.currentData()
        text = message.toPlainText().strip()
        workdir = workspace.text().strip()
        controller.mode = mode
        controller.backend_id = backend_id
        event = controller.prepare_send(text, workspace=workdir)
        status.setText(event.message)
        set_pet_state(event.pet_state)
        if not event.ok:
            return
        if mode == "work":
            answer = QMessageBox.question(
                window,
                "Confirm Work Mode",
                f"Run backend task in workspace?\n\n{workdir}\n\n{text}",
            )
            if answer != QMessageBox.StandardButton.Yes:
                status.setText("Waiting")
                set_pet_state("waiting")
                return
        send.setEnabled(False)
        worker = SendWorker(pet, backend_id, mode, workdir, text)
        state["worker"] = worker

        def finished(result: BackendResult) -> None:
            event_done = controller.complete(ok=result.ok, message=result.text or result.error)
            status.setText(event_done.message or event_done.pet_state)
            reply.setPlainText(result.text or result.error)
            set_pet_state(event_done.pet_state)
            send.setEnabled(True)
            worker.deleteLater()
            state["worker"] = None

        worker.completed.connect(finished)
        worker.start()

    selector.currentIndexChanged.connect(on_pet_changed)
    auth_button.clicked.connect(on_auth_clicked)
    send.clicked.connect(on_send_clicked)

    top_row.addWidget(QLabel("Pet"))
    top_row.addWidget(selector, 2)
    top_row.addWidget(QLabel("Backend"))
    top_row.addWidget(backend_selector, 1)
    top_row.addWidget(QLabel("Mode"))
    top_row.addWidget(mode_selector, 1)
    top_row.addWidget(auth_button)
    layout.addLayout(top_row)
    layout.addWidget(status)
    layout.addWidget(image)
    layout.addWidget(workspace)
    layout.addWidget(message)
    layout.addWidget(send)
    layout.addWidget(reply)
    timer = QTimer(window)
    timer.timeout.connect(advance_frame)
    timer.start(140)
    render_frame()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
