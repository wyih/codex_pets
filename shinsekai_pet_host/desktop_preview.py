from __future__ import annotations

from pathlib import Path
import sys

from shinsekai_pet_host.backends import BackendConfig, BackendProviderRegistry, BackendResult
from shinsekai_pet_host.codex_cli import CodexAuthService
from shinsekai_pet_host.host_controller import PetHostController
from shinsekai_pet_host.persona import compose_pet_prompt, load_dialogue
from shinsekai_pet_host.petpack import PetPack, PetRegistry
from shinsekai_pet_host.runtime import AmbientStateScheduler, PetAnimator


BUBBLE_PREVIEW_LIMIT = 96


def _bubble_preview(text: str, limit: int = BUBBLE_PREVIEW_LIMIT) -> str:
    cleaned = " ".join(text.strip().split())
    if len(cleaned) <= limit:
        return cleaned
    return f"{cleaned[:limit].rstrip()}..."


def main() -> int:
    try:
        from PySide6.QtCore import QPoint, QThread, QTimer, Qt, Signal
        from PySide6.QtGui import QAction, QActionGroup, QPainter, QPixmap
        from PySide6.QtWidgets import (
            QApplication,
            QDialog,
            QFrame,
            QHBoxLayout,
            QInputDialog,
            QLabel,
            QLineEdit,
            QMenu,
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
    app.setApplicationName("Shinsekai Pet Host")

    window = QWidget()
    window.setWindowTitle("Shinsekai Pet Host")
    window.setWindowFlags(
        Qt.WindowType.FramelessWindowHint
        | Qt.WindowType.WindowStaysOnTopHint
        | Qt.WindowType.Tool
    )
    window.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
    window.setFixedSize(390, 405)

    layout = QVBoxLayout(window)
    layout.setContentsMargins(16, 16, 16, 16)
    layout.setSpacing(10)

    bubble = QFrame()
    bubble.setObjectName("bubble")
    bubble.setFixedHeight(178)
    bubble_layout = QVBoxLayout(bubble)
    bubble_layout.setContentsMargins(18, 14, 18, 14)
    bubble_layout.setSpacing(10)

    bubble_top = QHBoxLayout()
    close_bubble = QPushButton("×")
    close_bubble.setObjectName("closeBubble")
    close_bubble.setFixedSize(28, 28)
    status = QLabel("Ready")
    status.setObjectName("status")
    status.setWordWrap(True)
    status.setMaximumHeight(38)
    menu_button = QPushButton("⌄")
    menu_button.setObjectName("menuButton")
    menu_button.setFixedSize(34, 34)
    bubble_top.addWidget(close_bubble)
    bubble_top.addWidget(status, 1)
    bubble_top.addWidget(menu_button)

    reply = QLabel()
    reply.setObjectName("reply")
    reply.setWordWrap(True)
    reply.setFixedHeight(58)
    reply.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)

    input_row = QHBoxLayout()
    message = QLineEdit()
    message.setPlaceholderText("Reply")
    send = QPushButton("Reply")
    send.setObjectName("sendButton")
    input_row.addWidget(message, 1)
    input_row.addWidget(send)

    bubble_layout.addLayout(bubble_top)
    bubble_layout.addWidget(reply)
    bubble_layout.addLayout(input_row)

    image = QLabel()
    image.setObjectName("petImage")
    image.setAlignment(Qt.AlignmentFlag.AlignCenter)
    image.setFixedSize(260, 185)

    pet_row = QHBoxLayout()
    pet_row.addStretch(1)
    pet_row.addWidget(image)
    pet_row.addStretch(1)

    layout.addWidget(bubble)
    layout.addLayout(pet_row)

    window.setStyleSheet(
        """
        QWidget {
            color: #202124;
        }
        QFrame#bubble {
            background: rgba(255, 255, 255, 244);
            border: 1px solid rgba(0, 0, 0, 24);
            border-radius: 24px;
        }
        QLabel#status {
            font-size: 15px;
            font-weight: 650;
            color: #24262a;
        }
        QLabel#reply {
            font-size: 14px;
            line-height: 1.35;
            color: #2b2d31;
        }
        QLineEdit {
            background: white;
            border: 1px solid #4e9dff;
            border-radius: 13px;
            padding: 7px 10px;
            font-size: 14px;
            selection-background-color: #d7e9ff;
        }
        QPushButton#sendButton {
            background: #8c8f94;
            color: white;
            border: 0;
            border-radius: 14px;
            padding: 7px 18px;
            font-size: 14px;
            font-weight: 600;
        }
        QPushButton#sendButton:disabled {
            background: #c5c7cb;
            color: #f5f5f5;
        }
        QPushButton#closeBubble, QPushButton#menuButton {
            background: rgba(255, 255, 255, 235);
            border: 1px solid rgba(0, 0, 0, 22);
            border-radius: 14px;
            color: #33363b;
            font-size: 15px;
            font-weight: 700;
        }
        QPushButton#menuButton {
            border-radius: 17px;
        }
        """
    )

    registry = BackendProviderRegistry.default()
    controller = PetHostController(selected_pet_id=pets[0].manifest.id)
    animator_cache: dict[str, object] = {
        "pet_id": "",
        "pixmap": None,
        "animator": None,
    }
    scheduler = AmbientStateScheduler()
    runtime_state: dict[str, object] = {
        "ambient_tick": 0,
        "frame_tick": 0,
        "locked_state": None,
        "hold_ticks": 0,
        "busy": False,
        "worker": None,
        "drag_offset": None,
        "last_ambient": "",
        "log_dialog": None,
    }
    settings = {
        "backend_id": "codex-cli",
        "mode": "chat",
        "workspace": "",
    }
    log_lines: list[str] = []

    def current_pet() -> PetPack:
        for pet in pets:
            if pet.manifest.id == controller.selected_pet_id:
                return pet
        return pets[0]

    def dialogue_line(pet: PetPack, pet_state: str) -> str:
        lines = load_dialogue(pet).get(pet_state) or load_dialogue(pet).get("idle") or []
        if not lines:
            return f"{pet.manifest.display_name} is ready."
        index = int(runtime_state["ambient_tick"]) % len(lines)
        return lines[index]

    def set_bubble(title: str, text: str) -> None:
        status.setText(title)
        reply.setText(_bubble_preview(text))
        bubble.setVisible(True)

    def set_pet_state(pet_state: str, *, hold_ticks: int = 28, busy: bool = False) -> None:
        runtime_state["locked_state"] = pet_state
        runtime_state["hold_ticks"] = hold_ticks
        runtime_state["busy"] = busy
        runtime_state["frame_tick"] = 0
        render_frame()

    def current_display_state() -> str:
        locked = runtime_state["locked_state"]
        if isinstance(locked, str):
            return locked
        ambient = scheduler.state_at(int(runtime_state["ambient_tick"]))
        if ambient.state != runtime_state["last_ambient"]:
            runtime_state["last_ambient"] = ambient.state
            runtime_state["frame_tick"] = 0
        return ambient.state

    def current_pixmap_and_animator() -> tuple[QPixmap, PetAnimator]:
        pet = current_pet()
        if animator_cache["pet_id"] != pet.manifest.id:
            animator_cache["pet_id"] = pet.manifest.id
            animator_cache["pixmap"] = QPixmap(str(pet.spritesheet))
            animator_cache["animator"] = PetAnimator(pet.atlas)
        return animator_cache["pixmap"], animator_cache["animator"]  # type: ignore[return-value]

    def motion_offset(display_state: str, frame_tick: int) -> tuple[int, int]:
        if display_state == "running-right":
            return (-22 + (frame_tick % 8) * 6, 0)
        if display_state == "running-left":
            return (22 - (frame_tick % 8) * 6, 0)
        if display_state == "jumping":
            return (0, -16 if frame_tick % 5 in {1, 2} else 0)
        return (0, 0)

    def render_frame() -> None:
        pixmap, animator = current_pixmap_and_animator()
        display_state = current_display_state()
        frame_tick = int(runtime_state["frame_tick"])
        frame_info = animator.frame_at(display_state, frame_tick)
        frame = pixmap.copy(frame_info.x, frame_info.y, frame_info.width, frame_info.height)
        scaled = frame.scaled(164, 170, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        canvas = QPixmap(image.width(), image.height())
        canvas.fill(Qt.GlobalColor.transparent)
        offset_x, offset_y = motion_offset(display_state, frame_tick)
        x = (canvas.width() - scaled.width()) // 2 + offset_x
        y = (canvas.height() - scaled.height()) // 2 + offset_y
        painter = QPainter(canvas)
        painter.drawPixmap(x, y, scaled)
        painter.end()
        image.setPixmap(canvas)

    def advance_frame() -> None:
        runtime_state["frame_tick"] = int(runtime_state["frame_tick"]) + 1
        if runtime_state["locked_state"] is None:
            runtime_state["ambient_tick"] = int(runtime_state["ambient_tick"]) + 1
        elif not bool(runtime_state["busy"]):
            runtime_state["hold_ticks"] = int(runtime_state["hold_ticks"]) - 1
            if int(runtime_state["hold_ticks"]) <= 0:
                runtime_state["locked_state"] = None
                runtime_state["frame_tick"] = 0
        render_frame()

    def select_pet(pet: PetPack) -> None:
        event = controller.select_pet(pet.manifest.id)
        set_bubble(pet.manifest.display_name, dialogue_line(pet, "waving"))
        set_pet_state(event.pet_state, hold_ticks=24)

    def on_auth_clicked() -> None:
        auth = CodexAuthService().status()
        pet_state = "review" if auth.ok else "failed"
        set_bubble("Auth", auth.message)
        set_pet_state(pet_state, hold_ticks=34)

    def set_workspace() -> None:
        value, ok = QInputDialog.getText(
            window,
            "Workspace",
            "Work mode workspace:",
            text=settings["workspace"],
        )
        if ok:
            settings["workspace"] = value.strip()
            set_bubble("Workspace", settings["workspace"] or "Workspace cleared.")
            set_pet_state("review", hold_ticks=20)

    def show_log() -> None:
        dialog = QDialog(window)
        dialog.setWindowTitle("Pet Log")
        dialog.resize(480, 320)
        dialog_layout = QVBoxLayout(dialog)
        text = QTextEdit()
        text.setReadOnly(True)
        text.setPlainText("\n\n".join(log_lines) or "No conversation yet.")
        dialog_layout.addWidget(text)
        runtime_state["log_dialog"] = dialog
        dialog.show()

    def show_context_menu(global_pos: QPoint) -> None:
        menu = QMenu(window)

        pet_menu = menu.addMenu("Pet")
        pet_group = QActionGroup(pet_menu)
        pet_group.setExclusive(True)
        for pet in pets:
            action = QAction(pet.manifest.display_name, pet_menu)
            action.setCheckable(True)
            action.setChecked(pet.manifest.id == controller.selected_pet_id)
            action.triggered.connect(lambda _checked=False, selected=pet: select_pet(selected))
            pet_group.addAction(action)
            pet_menu.addAction(action)

        backend_menu = menu.addMenu("Backend")
        backend_group = QActionGroup(backend_menu)
        backend_group.setExclusive(True)
        for backend_id in registry.ids():
            action = QAction(backend_id, backend_menu)
            action.setCheckable(True)
            action.setChecked(backend_id == settings["backend_id"])
            action.triggered.connect(lambda _checked=False, selected=backend_id: settings.update({"backend_id": selected}))
            backend_group.addAction(action)
            backend_menu.addAction(action)

        mode_menu = menu.addMenu("Mode")
        mode_group = QActionGroup(mode_menu)
        mode_group.setExclusive(True)
        for label, value in (("Chat", "chat"), ("Work", "work")):
            action = QAction(label, mode_menu)
            action.setCheckable(True)
            action.setChecked(value == settings["mode"])
            action.triggered.connect(lambda _checked=False, selected=value: settings.update({"mode": selected}))
            mode_group.addAction(action)
            mode_menu.addAction(action)

        menu.addSeparator()
        workspace_action = menu.addAction("Workspace...")
        auth_action = menu.addAction("Auth")
        log_action = menu.addAction("Log")
        menu.addSeparator()
        toggle_bubble = menu.addAction("Hide Bubble" if bubble.isVisible() else "Show Bubble")
        quit_action = menu.addAction("Quit")

        workspace_action.triggered.connect(set_workspace)
        auth_action.triggered.connect(on_auth_clicked)
        log_action.triggered.connect(show_log)
        toggle_bubble.triggered.connect(lambda: bubble.setVisible(not bubble.isVisible()))
        quit_action.triggered.connect(app.quit)
        menu.exec(global_pos)

    def complete_send(worker: SendWorker, result: BackendResult) -> None:
        event_done = controller.complete(ok=result.ok, message=result.text or result.error)
        text = result.text or result.error
        set_bubble("Ready" if result.ok else "Failed", text)
        log_lines.append(f"Pet: {text}")
        set_pet_state(event_done.pet_state, hold_ticks=42)
        send.setEnabled(True)
        message.setEnabled(True)
        worker.deleteLater()
        runtime_state["worker"] = None

    def on_send_clicked() -> None:
        pet = current_pet()
        text = message.text().strip()
        controller.mode = settings["mode"]
        controller.backend_id = settings["backend_id"]
        event = controller.prepare_send(text, workspace=settings["workspace"])
        if not event.ok:
            set_bubble("Waiting", event.message)
            set_pet_state(event.pet_state, hold_ticks=28)
            return
        if settings["mode"] == "work":
            answer = QMessageBox.question(
                window,
                "Confirm Work Mode",
                f"Run backend task in workspace?\n\n{settings['workspace']}\n\n{text}",
            )
            if answer != QMessageBox.StandardButton.Yes:
                set_bubble("Waiting", "Work mode is waiting for confirmation.")
                set_pet_state("waiting", hold_ticks=28)
                return
        log_lines.append(f"You: {text}")
        set_bubble("Thinking", dialogue_line(pet, "running"))
        set_pet_state(event.pet_state, busy=True)
        send.setEnabled(False)
        message.setEnabled(False)
        message.clear()
        worker = SendWorker(pet, settings["backend_id"], settings["mode"], settings["workspace"], text)
        runtime_state["worker"] = worker
        worker.completed.connect(lambda result, current_worker=worker: complete_send(current_worker, result))
        worker.start()

    def event_global_pos(event: object) -> QPoint:
        if hasattr(event, "globalPosition"):
            return event.globalPosition().toPoint()
        return event.globalPos()

    def mouse_press(event: object) -> None:
        if event.button() == Qt.MouseButton.RightButton:
            show_context_menu(event_global_pos(event))
            return
        if event.button() == Qt.MouseButton.LeftButton:
            runtime_state["drag_offset"] = event_global_pos(event) - window.frameGeometry().topLeft()

    def mouse_move(event: object) -> None:
        offset = runtime_state["drag_offset"]
        if offset is not None and event.buttons() & Qt.MouseButton.LeftButton:
            window.move(event_global_pos(event) - offset)

    def mouse_release(event: object) -> None:
        runtime_state["drag_offset"] = None

    def toggle_bubble_from_pet(event: object) -> None:
        if event.button() == Qt.MouseButton.RightButton:
            show_context_menu(event_global_pos(event))
            return
        bubble.setVisible(not bubble.isVisible())
        set_pet_state("waving", hold_ticks=18)

    close_bubble.clicked.connect(lambda: bubble.setVisible(False))
    menu_button.clicked.connect(lambda: show_context_menu(menu_button.mapToGlobal(QPoint(0, menu_button.height()))))
    send.clicked.connect(on_send_clicked)
    message.returnPressed.connect(on_send_clicked)
    window.mousePressEvent = mouse_press  # type: ignore[method-assign]
    window.mouseMoveEvent = mouse_move  # type: ignore[method-assign]
    window.mouseReleaseEvent = mouse_release  # type: ignore[method-assign]
    image.mousePressEvent = toggle_bubble_from_pet  # type: ignore[method-assign]

    initial_pet = current_pet()
    set_bubble(initial_pet.manifest.display_name, dialogue_line(initial_pet, "idle"))
    render_frame()

    timer = QTimer(window)
    timer.timeout.connect(advance_frame)
    timer.start(150)

    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
