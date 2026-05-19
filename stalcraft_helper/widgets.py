"""Reusable widgets for the STALCRAFT helper UI."""

from __future__ import annotations

import shutil
import uuid
from pathlib import Path
from typing import Optional

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtWidgets import (
    QDoubleSpinBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from .utils import app_data_dir, format_number


def _supported_image_filter() -> str:
    return "Изображения (*.png *.jpg *.jpeg *.bmp *.webp *.gif);;Все файлы (*)"


class ItemCard(QFrame):
    """A single item card with toggleable edit / view modes."""

    changed = pyqtSignal()
    removed = pyqtSignal(object)

    CARD_WIDTH = 210
    CARD_HEIGHT = 270
    IMAGE_W = 190
    IMAGE_H = 110

    def __init__(
        self,
        *,
        item_id: Optional[str] = None,
        name: str = "",
        price: float = 0.0,
        quantity: int = 1,
        image_path: Optional[str] = None,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("Card")
        self.setFixedSize(self.CARD_WIDTH, self.CARD_HEIGHT)

        self.item_id = item_id or uuid.uuid4().hex
        self._image_path: Optional[str] = None
        self._editing = True

        outer = QVBoxLayout(self)
        outer.setContentsMargins(10, 8, 10, 10)
        outer.setSpacing(6)

        # ---- Header: edit-toggle + remove ----
        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        header.setSpacing(4)
        header.addStretch(1)

        self.edit_toggle = QPushButton("✎")
        self.edit_toggle.setObjectName("CardEdit")
        self.edit_toggle.setToolTip("Изменить")
        self.edit_toggle.setCursor(Qt.CursorShape.PointingHandCursor)
        self.edit_toggle.clicked.connect(self._on_toggle_clicked)
        header.addWidget(self.edit_toggle)

        self.remove_btn = QPushButton("×")
        self.remove_btn.setObjectName("Danger")
        self.remove_btn.setToolTip("Удалить предмет")
        self.remove_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.remove_btn.clicked.connect(lambda: self.removed.emit(self))
        header.addWidget(self.remove_btn)
        outer.addLayout(header)

        # ---- Image (shared between modes) ----
        self.image_btn = QPushButton("Добавить картинку")
        self.image_btn.setObjectName("ImageButton")
        self.image_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.image_btn.setFixedSize(self.IMAGE_W, self.IMAGE_H)
        self.image_btn.setIconSize(self.image_btn.size())
        self.image_btn.clicked.connect(self._choose_image)
        outer.addWidget(self.image_btn, alignment=Qt.AlignmentFlag.AlignHCenter)

        # ---- Stacked content: edit / view ----
        self.content_stack = QStackedWidget()
        outer.addWidget(self.content_stack, 1)

        self.content_stack.addWidget(self._build_edit_page(name, price, quantity))
        self.content_stack.addWidget(self._build_view_page())

        if image_path:
            self._apply_image(image_path)

        # Newly created (empty) card → edit. Loaded card with a filled name → view.
        is_filled = bool(name.strip()) or price > 0
        self._set_editing(not is_filled, emit=False)
        self._refresh_subtotal()

    # ---- Page builders --------------------------------------------------
    def _build_edit_page(self, name: str, price: float, quantity: int) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Название")
        self.name_edit.setText(name)
        self.name_edit.textChanged.connect(self._on_text_changed)
        layout.addWidget(self.name_edit)

        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(6)

        price_col = QVBoxLayout()
        price_col.setContentsMargins(0, 0, 0, 0)
        price_col.setSpacing(2)
        price_label = QLabel("Цена")
        price_label.setObjectName("Field")
        self.price_edit = QDoubleSpinBox()
        self.price_edit.setRange(0.0, 1_000_000_000_000.0)
        self.price_edit.setDecimals(0)
        self.price_edit.setGroupSeparatorShown(True)
        self.price_edit.setButtonSymbols(QDoubleSpinBox.ButtonSymbols.NoButtons)
        self.price_edit.setValue(price)
        self.price_edit.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.price_edit.valueChanged.connect(self._on_value_changed)
        price_col.addWidget(price_label)
        price_col.addWidget(self.price_edit)
        row.addLayout(price_col)

        qty_col = QVBoxLayout()
        qty_col.setContentsMargins(0, 0, 0, 0)
        qty_col.setSpacing(2)
        qty_label = QLabel("Кол-во")
        qty_label.setObjectName("Field")
        self.qty_edit = QSpinBox()
        self.qty_edit.setRange(0, 1_000_000)
        self.qty_edit.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)
        self.qty_edit.setValue(quantity)
        self.qty_edit.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.qty_edit.valueChanged.connect(self._on_value_changed)
        qty_col.addWidget(qty_label)
        qty_col.addWidget(self.qty_edit)
        row.addLayout(qty_col)

        layout.addLayout(row)

        bottom = QHBoxLayout()
        bottom.setContentsMargins(0, 2, 0, 0)
        sum_label = QLabel("Сумма")
        sum_label.setObjectName("Field")
        self.subtotal_label = QLabel("0")
        self.subtotal_label.setObjectName("Subtotal")
        self.subtotal_label.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )
        bottom.addWidget(sum_label)
        bottom.addStretch(1)
        bottom.addWidget(self.subtotal_label)
        layout.addLayout(bottom)

        return page

    def _build_view_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 2, 0, 0)
        layout.setSpacing(4)

        self.name_view = QLabel("—")
        self.name_view.setObjectName("CardName")
        self.name_view.setWordWrap(True)
        layout.addWidget(self.name_view)

        self.priceqty_view = QLabel("0 × 0")
        self.priceqty_view.setObjectName("CardPriceQty")
        layout.addWidget(self.priceqty_view)

        layout.addStretch(1)

        bottom = QHBoxLayout()
        bottom.setContentsMargins(0, 0, 0, 0)
        sum_label = QLabel("Сумма")
        sum_label.setObjectName("Field")
        self.subtotal_view = QLabel("0")
        self.subtotal_view.setObjectName("Subtotal")
        self.subtotal_view.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )
        bottom.addWidget(sum_label)
        bottom.addStretch(1)
        bottom.addWidget(self.subtotal_view)
        layout.addLayout(bottom)

        return page

    # ---- Public API -----------------------------------------------------
    def subtotal(self) -> float:
        return float(self.price_edit.value()) * float(self.qty_edit.value())

    def to_dict(self) -> dict:
        return {
            "id": self.item_id,
            "name": self.name_edit.text(),
            "price": float(self.price_edit.value()),
            "quantity": int(self.qty_edit.value()),
            "image_path": self._image_path,
        }

    # ---- Edit / view toggle --------------------------------------------
    def _on_toggle_clicked(self) -> None:
        self._set_editing(not self._editing, emit=True)

    def _set_editing(self, editing: bool, *, emit: bool) -> None:
        self._editing = editing
        self.content_stack.setCurrentIndex(0 if editing else 1)
        self.edit_toggle.setText("✓" if editing else "✎")
        self.edit_toggle.setToolTip("Готово" if editing else "Изменить")
        self.edit_toggle.setProperty("active", "true" if editing else "false")
        style = self.edit_toggle.style()
        style.unpolish(self.edit_toggle)
        style.polish(self.edit_toggle)
        if not editing:
            self._refresh_view()
        if emit:
            self.changed.emit()

    # ---- Internal -------------------------------------------------------
    def _on_text_changed(self, _: str) -> None:
        if not self._editing:
            self._refresh_view()
        self.changed.emit()

    def _on_value_changed(self, _: float) -> None:
        self._refresh_subtotal()
        self.changed.emit()

    def _refresh_subtotal(self) -> None:
        total = format_number(self.subtotal())
        self.subtotal_label.setText(total)
        self.subtotal_view.setText(total)
        self._refresh_view()

    def _refresh_view(self) -> None:
        name = self.name_edit.text().strip() or "—"
        self.name_view.setText(name)
        price = self.price_edit.value()
        qty = int(self.qty_edit.value())
        self.priceqty_view.setText(f"{format_number(price)} × {qty}")

    def _choose_image(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Выберите картинку предмета",
            str(Path.home()),
            _supported_image_filter(),
        )
        if not path:
            return
        try:
            target_dir = app_data_dir() / "images"
            target = target_dir / f"{self.item_id}{Path(path).suffix.lower()}"
            for existing in target_dir.glob(f"{self.item_id}.*"):
                if existing != target:
                    try:
                        existing.unlink()
                    except OSError:
                        pass
            shutil.copy2(path, target)
            stored = str(target)
        except OSError:
            stored = path
        self._apply_image(stored)
        self.changed.emit()

    def _apply_image(self, path: str) -> None:
        pix = QPixmap(path)
        if pix.isNull():
            self._image_path = None
            self.image_btn.setIcon(QIcon())
            self.image_btn.setText("Добавить картинку")
            return
        scaled = pix.scaled(
            self.IMAGE_W - 8,
            self.IMAGE_H - 8,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.image_btn.setIcon(QIcon(scaled))
        self.image_btn.setIconSize(scaled.size())
        self.image_btn.setText("")
        self._image_path = path


class AddCard(QFrame):
    """A placeholder card showing a big "+" — clicking it requests a new item."""

    clicked = pyqtSignal()

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("Card")
        self.setFixedSize(ItemCard.CARD_WIDTH, ItemCard.CARD_HEIGHT)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(6)
        layout.addStretch(1)

        plus = QLabel("+")
        plus.setAlignment(Qt.AlignmentFlag.AlignCenter)
        plus.setStyleSheet(
            "font-size: 56px; font-weight: 300; color: rgba(255, 255, 255, 0.35);"
        )
        layout.addWidget(plus)

        hint = QLabel("Добавить предмет")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hint.setObjectName("Hint")
        layout.addWidget(hint)
        layout.addStretch(1)

    def mousePressEvent(self, event):  # type: ignore[override]
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


class HSeparator(QFrame):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("Divider")
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setFixedHeight(1)
