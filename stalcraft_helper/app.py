"""Main window with two animated tabs."""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from PyQt6.QtCore import (
    QEasingCurve,
    QPoint,
    QPropertyAnimation,
    QTimer,
    Qt,
)
from PyQt6.QtGui import QIcon, QMouseEvent
from PyQt6.QtWidgets import (
    QApplication,
    QFrame,
    QGraphicsOpacityEffect,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QSizeGrip,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from .tab_catalysts import CatalystsTab
from .tab_resell import ResellTab
from .utils import load_state, save_state


APP_TITLE = "STALCRAFT X — помощник перекупщика"


class _TabButton(QPushButton):
    def __init__(self, text: str, parent: Optional[QWidget] = None) -> None:
        super().__init__(text, parent)
        self.setObjectName("TabButton")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setCheckable(True)
        self.set_active(False)

    def set_active(self, active: bool) -> None:
        self.setProperty("active", "true" if active else "false")
        self.setChecked(active)
        style = self.style()
        style.unpolish(self)
        style.polish(self)


class _TitleBar(QFrame):
    """Frameless-window title bar: drag area + min / close + tabs."""

    def __init__(self, main_window: "MainWindow") -> None:
        super().__init__(main_window)
        self.setObjectName("TopBar")
        self.setFixedHeight(54)
        self._window = main_window
        self._drag_offset: Optional[QPoint] = None

    def mousePressEvent(self, event: QMouseEvent) -> None:  # type: ignore[override]
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_offset = (
                event.globalPosition().toPoint() - self._window.frameGeometry().topLeft()
            )
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:  # type: ignore[override]
        if (
            self._drag_offset is not None
            and event.buttons() & Qt.MouseButton.LeftButton
        ):
            new_pos = event.globalPosition().toPoint() - self._drag_offset
            self._window.move(new_pos)
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:  # type: ignore[override]
        self._drag_offset = None
        super().mouseReleaseEvent(event)


class MainWindow(QMainWindow):
    """Frameless dark-glass two-tab window with cross-fade transitions."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(APP_TITLE)
        self.resize(900, 620)
        self.setMinimumSize(720, 520)

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window
        )
        # Translucent window background so the rounded corners on the
        # inner Background frame actually show through as transparency.
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

        central = QFrame()
        central.setObjectName("Background")
        self.setCentralWidget(central)

        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ---- Custom title bar (drag + tabs + window controls) -----------
        top_bar = _TitleBar(self)
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(16, 4, 8, 0)
        top_layout.setSpacing(4)

        brand = QLabel("STALCRAFT helper")
        brand.setObjectName("Title")
        top_layout.addWidget(brand)
        top_layout.addSpacing(20)

        self.tab_buttons: List[_TabButton] = []
        for idx, name in enumerate(["Основное перекупство", "Катализаторы"]):
            btn = _TabButton(name)
            btn.clicked.connect(lambda _=False, i=idx: self._switch_to(i))
            top_layout.addWidget(btn)
            self.tab_buttons.append(btn)

        top_layout.addStretch(1)

        self.min_btn = QPushButton("–")
        self.min_btn.setObjectName("WindowMin")
        self.min_btn.setToolTip("Свернуть")
        self.min_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.min_btn.setFixedSize(34, 28)
        self.min_btn.clicked.connect(self.showMinimized)
        top_layout.addWidget(self.min_btn)

        self.close_btn = QPushButton("×")
        self.close_btn.setObjectName("WindowClose")
        self.close_btn.setToolTip("Закрыть")
        self.close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.close_btn.setFixedSize(34, 28)
        self.close_btn.clicked.connect(self.close)
        top_layout.addWidget(self.close_btn)

        root.addWidget(top_bar)

        # ---- Stacked tab content ----------------------------------------
        self.stack = QStackedWidget()
        root.addWidget(self.stack, 1)

        self.resell_tab = ResellTab()
        self.catalysts_tab = CatalystsTab()
        self.stack.addWidget(self.resell_tab)
        self.stack.addWidget(self.catalysts_tab)

        self.resell_tab.state_changed.connect(self._schedule_save)
        self.catalysts_tab.state_changed.connect(self._schedule_save)

        # ---- Resize grip — top-level so it sits over rounded corner ----
        self._size_grip = QSizeGrip(self)
        self._size_grip.setObjectName("SizeGrip")
        self._size_grip.setFixedSize(16, 16)
        self._size_grip.raise_()

        # ---- Animations -------------------------------------------------
        self._anim: Optional[QPropertyAnimation] = None
        self._save_timer = QTimer(self)
        self._save_timer.setSingleShot(True)
        self._save_timer.timeout.connect(self._save)

        # ---- Load saved state -------------------------------------------
        self._load()
        self._switch_to(0, animate=False)

    # ---- Styling --------------------------------------------------------
    def apply_styles(self, stylesheet: str) -> None:
        self.setStyleSheet(stylesheet)

    # ---- Tab switching --------------------------------------------------
    def _switch_to(self, index: int, *, animate: bool = True) -> None:
        if index < 0 or index >= self.stack.count():
            return
        for i, btn in enumerate(self.tab_buttons):
            btn.set_active(i == index)

        if self.stack.currentIndex() == index and animate:
            return

        self.stack.setCurrentIndex(index)

        if not animate:
            return

        widget = self.stack.currentWidget()
        if widget is None:
            return
        effect = QGraphicsOpacityEffect(widget)
        widget.setGraphicsEffect(effect)
        anim = QPropertyAnimation(effect, b"opacity")
        anim.setDuration(220)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        def cleanup() -> None:
            widget.setGraphicsEffect(None)

        anim.finished.connect(cleanup)
        anim.start()
        self._anim = anim  # retain reference

    # ---- State persistence ---------------------------------------------
    def _schedule_save(self) -> None:
        self._save_timer.start(400)

    def _save(self) -> None:
        state = {
            "resell": self.resell_tab.dump(),
            "catalysts": self.catalysts_tab.dump(),
        }
        save_state(state)

    def _load(self) -> None:
        data = load_state()
        if not isinstance(data, dict):
            return
        resell_items = data.get("resell")
        if isinstance(resell_items, list):
            self.resell_tab.load(resell_items)
        catalysts_data = data.get("catalysts")
        if isinstance(catalysts_data, dict):
            self.catalysts_tab.load(catalysts_data)

    def closeEvent(self, event):  # type: ignore[override]
        self._save()
        super().closeEvent(event)

    def resizeEvent(self, event):  # type: ignore[override]
        super().resizeEvent(event)
        # Keep the size-grip pinned to the bottom-right corner, inset just
        # enough to stay inside the rounded background.
        margin = 6
        self._size_grip.move(
            self.width() - self._size_grip.width() - margin,
            self.height() - self._size_grip.height() - margin,
        )
        self._size_grip.raise_()


def build_app() -> tuple[QApplication, MainWindow]:
    """Create the QApplication + MainWindow with the stylesheet applied."""
    app = QApplication.instance() or QApplication([])
    app.setApplicationName(APP_TITLE)

    style_path = Path(__file__).with_name("style.qss")
    try:
        stylesheet = style_path.read_text(encoding="utf-8")
    except OSError:
        stylesheet = ""

    window = MainWindow()
    window.apply_styles(stylesheet)
    return app, window  # type: ignore[return-value]
