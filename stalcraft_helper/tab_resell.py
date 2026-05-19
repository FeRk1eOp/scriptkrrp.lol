"""\"Основное перекупство\" tab — grid of item cards plus running total."""

from __future__ import annotations

from typing import Iterable, List, Optional

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from .flow_layout import FlowLayout
from .utils import format_number
from .widgets import AddCard, HSeparator, ItemCard


class ResellTab(QWidget):
    """Grid of item cards with a running total at the bottom."""

    state_changed = pyqtSignal()

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)

        self._cards: List[ItemCard] = []

        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 0)
        root.setSpacing(10)

        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        title = QLabel("Карточки предметов")
        title.setObjectName("Title")
        hint = QLabel("Цена × Количество = сумма карточки")
        hint.setObjectName("Hint")
        header.addWidget(title)
        header.addSpacing(10)
        header.addWidget(hint)
        header.addStretch(1)
        root.addLayout(header)

        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

        container = QWidget()
        container.setObjectName("ResellContainer")
        self._flow = FlowLayout(container, margin=0, h_spacing=12, v_spacing=12)
        container.setLayout(self._flow)
        self._scroll.setWidget(container)
        root.addWidget(self._scroll, 1)

        self._add_card = AddCard()
        self._add_card.clicked.connect(self._on_add_clicked)
        self._flow.addWidget(self._add_card)

        root.addWidget(HSeparator())

        bottom = QFrame()
        bottom.setObjectName("BottomBar")
        bottom_layout = QHBoxLayout(bottom)
        bottom_layout.setContentsMargins(16, 12, 16, 12)
        bottom_layout.setSpacing(12)

        total_label = QLabel("ИТОГО")
        total_label.setObjectName("Section")
        self.total_value = QLabel("0")
        self.total_value.setObjectName("Total")
        self.total_value.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )

        self.copy_btn = QPushButton("Копировать")
        self.copy_btn.setObjectName("Accent")
        self.copy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.copy_btn.clicked.connect(self._copy_total)

        bottom_layout.addWidget(total_label)
        bottom_layout.addStretch(1)
        bottom_layout.addWidget(self.total_value)
        bottom_layout.addSpacing(12)
        bottom_layout.addWidget(self.copy_btn)

        root.addWidget(bottom)

    # ---- Persistence ----------------------------------------------------
    def load(self, items: Iterable[dict]) -> None:
        for item in items:
            self._insert_card(
                name=item.get("name", ""),
                price=float(item.get("price", 0)),
                quantity=int(item.get("quantity", 1)),
                image_path=item.get("image_path"),
                item_id=item.get("id"),
                emit=False,
            )
        self._refresh_total()

    def dump(self) -> list[dict]:
        return [card.to_dict() for card in self._cards]

    # ---- Card management ------------------------------------------------
    def _on_add_clicked(self) -> None:
        self._insert_card()
        self.state_changed.emit()

    def _insert_card(
        self,
        *,
        name: str = "",
        price: float = 0.0,
        quantity: int = 1,
        image_path: Optional[str] = None,
        item_id: Optional[str] = None,
        emit: bool = True,
    ) -> ItemCard:
        card = ItemCard(
            item_id=item_id,
            name=name,
            price=price,
            quantity=quantity,
            image_path=image_path,
        )
        card.changed.connect(self._on_card_changed)
        card.removed.connect(self._on_card_removed)

        insert_at = self._flow.count() - 1
        if insert_at < 0:
            insert_at = 0
        # Remove "+" card, append new card, re-add "+" card to keep it last.
        self._flow.takeAt(self._flow.count() - 1)
        self._flow.addWidget(card)
        self._flow.addWidget(self._add_card)
        self._cards.append(card)

        if emit:
            self._refresh_total()
        return card

    def _on_card_changed(self) -> None:
        self._refresh_total()
        self.state_changed.emit()

    def _on_card_removed(self, card: ItemCard) -> None:
        if card not in self._cards:
            return
        self._cards.remove(card)
        idx = self._flow.indexOf(card)
        if idx >= 0:
            item = self._flow.takeAt(idx)
            if item is not None:
                w = item.widget()
                if w is not None:
                    w.setParent(None)
                    w.deleteLater()
        self._refresh_total()
        self.state_changed.emit()

    # ---- Total + copy ---------------------------------------------------
    def _total(self) -> float:
        return sum(card.subtotal() for card in self._cards)

    def _refresh_total(self) -> None:
        self.total_value.setText(format_number(self._total()))

    def _copy_total(self) -> None:
        total = self._total()
        text = format_number(total).replace(" ", "")
        QApplication.clipboard().setText(text)
        original = self.copy_btn.text()
        self.copy_btn.setText("Скопировано")
        self.copy_btn.setEnabled(False)
        from PyQt6.QtCore import QTimer

        def restore() -> None:
            self.copy_btn.setText(original)
            self.copy_btn.setEnabled(True)

        QTimer.singleShot(1200, restore)
