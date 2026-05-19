"""\"Катализаторы\" tab — catalyst crafting cost/profit calculator.

Recipe (per the user's STALCRAFT X workflow):

* Светящийся сахар (×30) ⇐ 100 аномальной пыли + 10 мякоти сластены +
  1 аномальная плазма
* Катализатор (×20) ⇐ 15 светящегося сахара + 100 аномальной пыли
"""

from __future__ import annotations

from typing import Optional

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QDoubleSpinBox,
    QFormLayout,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from .utils import format_number

SUGAR_PER_BATCH = 30
SUGAR_PUST = 100   # аномальная пыль на 1 партию сахара (30 шт)
SUGAR_SLAS = 10    # мякоть сластены на 1 партию сахара
SUGAR_PLAS = 1     # аномальная плазма на 1 партию сахара

CAT_PER_BATCH = 20
CAT_SUGAR = 15     # светящийся сахар на 1 партию катализаторов (20 шт)
CAT_PUST = 100     # аномальная пыль на 1 партию катализаторов

TARGET_CATALYSTS = 100


def _make_price_input() -> QDoubleSpinBox:
    sb = QDoubleSpinBox()
    sb.setRange(0.0, 1_000_000_000.0)
    sb.setDecimals(0)
    sb.setGroupSeparatorShown(True)
    sb.setButtonSymbols(QDoubleSpinBox.ButtonSymbols.NoButtons)
    sb.setAlignment(Qt.AlignmentFlag.AlignRight)
    return sb


class _Section(QFrame):
    def __init__(self, title: str, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("Section")

        outer = QVBoxLayout(self)
        outer.setContentsMargins(16, 14, 16, 14)
        outer.setSpacing(10)

        header = QLabel(title)
        header.setObjectName("Section")
        outer.addWidget(header)

        self.body = QVBoxLayout()
        self.body.setContentsMargins(0, 0, 0, 0)
        self.body.setSpacing(8)
        outer.addLayout(self.body)


class CatalystsTab(QWidget):
    """Two-column layout: inputs on the left, computed results on the right."""

    state_changed = pyqtSignal()

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)

        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.addWidget(scroll)

        host = QWidget()
        scroll.setWidget(host)

        grid = QGridLayout(host)
        grid.setContentsMargins(16, 16, 16, 16)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(12)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)

        # ---- Inputs: ingredient prices -----------------------------------
        ingredients = _Section("Цены на ингредиенты (за 1 шт)")
        ing_form = QFormLayout()
        ing_form.setContentsMargins(0, 0, 0, 0)
        ing_form.setHorizontalSpacing(10)
        ing_form.setVerticalSpacing(8)
        ing_form.setLabelAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )

        self.pust_price = _make_price_input()
        self.slas_price = _make_price_input()
        self.plas_price = _make_price_input()

        ing_form.addRow(self._field_label("Аномальная пыль"), self.pust_price)
        ing_form.addRow(self._field_label("Мякоть сластены"), self.slas_price)
        ing_form.addRow(self._field_label("Аномальная плазма"), self.plas_price)
        ingredients.body.addLayout(ing_form)

        recipe_hint = QLabel(
            "Рецепты:  100 пыли + 10 сластены + 1 плазма → 30 сахара  ·  "
            "15 сахара + 100 пыли → 20 катализаторов"
        )
        recipe_hint.setObjectName("Hint")
        recipe_hint.setWordWrap(True)
        ingredients.body.addWidget(recipe_hint)

        grid.addWidget(ingredients, 0, 0)

        # ---- Outputs: unit costs -----------------------------------------
        unit = _Section("Себестоимость")
        unit_form = QFormLayout()
        unit_form.setContentsMargins(0, 0, 0, 0)
        unit_form.setHorizontalSpacing(10)
        unit_form.setVerticalSpacing(8)
        unit_form.setLabelAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )

        self.sugar_cost = self._value_label("0")
        self.cat_cost = self._value_label("0")
        self.cat100_cost = self._value_label("0")

        unit_form.addRow(self._field_label("1 светящийся сахар"), self.sugar_cost)
        unit_form.addRow(self._field_label("1 катализатор"), self.cat_cost)
        unit_form.addRow(
            self._field_label(f"{TARGET_CATALYSTS} катализаторов"), self.cat100_cost
        )
        unit.body.addLayout(unit_form)
        grid.addWidget(unit, 0, 1)

        # ---- Outputs: ingredient totals for 100 catalysts ----------------
        totals = _Section(f"Сырьё на {TARGET_CATALYSTS} катализаторов")
        tot_form = QFormLayout()
        tot_form.setContentsMargins(0, 0, 0, 0)
        tot_form.setHorizontalSpacing(10)
        tot_form.setVerticalSpacing(8)
        tot_form.setLabelAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )

        self.need_pust = self._value_label("0")
        self.need_slas = self._value_label("0")
        self.need_plas = self._value_label("0")

        tot_form.addRow(self._field_label("Аномальная пыль"), self.need_pust)
        tot_form.addRow(self._field_label("Мякоть сластены"), self.need_slas)
        tot_form.addRow(self._field_label("Аномальная плазма"), self.need_plas)
        totals.body.addLayout(tot_form)

        totals_hint = QLabel(
            "Дробные значения — рецепт не делится нацело на 100 катализаторов."
        )
        totals_hint.setObjectName("Hint")
        totals_hint.setWordWrap(True)
        totals.body.addWidget(totals_hint)

        grid.addWidget(totals, 1, 0)

        # ---- Sell price + profit -----------------------------------------
        profit = _Section(f"Продажа {TARGET_CATALYSTS} катализаторов")
        profit_form = QFormLayout()
        profit_form.setContentsMargins(0, 0, 0, 0)
        profit_form.setHorizontalSpacing(10)
        profit_form.setVerticalSpacing(8)
        profit_form.setLabelAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )

        self.sell_price = _make_price_input()

        profit_form.addRow(
            self._field_label(f"Цена за {TARGET_CATALYSTS} шт"), self.sell_price
        )

        self.profit_value = QLabel("0")
        self.profit_value.setObjectName("Profit")
        self.profit_value.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )
        self.roi_value = self._value_label("0%")

        profit_form.addRow(self._field_label("Прибыль"), self.profit_value)
        profit_form.addRow(self._field_label("ROI"), self.roi_value)
        profit.body.addLayout(profit_form)

        grid.addWidget(profit, 1, 1)

        grid.setRowStretch(2, 1)

        # ---- Wire up signals ---------------------------------------------
        for sb in (
            self.pust_price,
            self.slas_price,
            self.plas_price,
            self.sell_price,
        ):
            sb.valueChanged.connect(self._recalculate)

        self._recalculate()

    # ---- Persistence ----------------------------------------------------
    def load(self, data: dict) -> None:
        self.pust_price.setValue(float(data.get("pust", 0)))
        self.slas_price.setValue(float(data.get("slas", 0)))
        self.plas_price.setValue(float(data.get("plas", 0)))
        self.sell_price.setValue(float(data.get("sell", 0)))
        self._recalculate()

    def dump(self) -> dict:
        return {
            "pust": float(self.pust_price.value()),
            "slas": float(self.slas_price.value()),
            "plas": float(self.plas_price.value()),
            "sell": float(self.sell_price.value()),
        }

    # ---- Helpers --------------------------------------------------------
    @staticmethod
    def _field_label(text: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName("Field")
        return label

    @staticmethod
    def _value_label(initial: str) -> QLabel:
        label = QLabel(initial)
        label.setObjectName("ResultValue")
        label.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )
        return label

    # ---- Logic ----------------------------------------------------------
    def _recalculate(self) -> None:
        pust = float(self.pust_price.value())
        slas = float(self.slas_price.value())
        plas = float(self.plas_price.value())
        sell = float(self.sell_price.value())

        sugar_cost = (
            SUGAR_PUST * pust + SUGAR_SLAS * slas + SUGAR_PLAS * plas
        ) / SUGAR_PER_BATCH
        cat_cost = (CAT_SUGAR * sugar_cost + CAT_PUST * pust) / CAT_PER_BATCH
        cat100_cost = cat_cost * TARGET_CATALYSTS

        # Raw ingredient counts needed for 100 catalysts.
        batches_cat = TARGET_CATALYSTS / CAT_PER_BATCH        # 5
        sugar_needed = batches_cat * CAT_SUGAR                # 75
        pust_for_cat = batches_cat * CAT_PUST                 # 500
        batches_sugar = sugar_needed / SUGAR_PER_BATCH        # 2.5
        pust_for_sugar = batches_sugar * SUGAR_PUST           # 250
        slas_total = batches_sugar * SUGAR_SLAS               # 25
        plas_total = batches_sugar * SUGAR_PLAS               # 2.5
        pust_total = pust_for_cat + pust_for_sugar            # 750

        self.sugar_cost.setText(format_number(sugar_cost, decimals=2))
        self.cat_cost.setText(format_number(cat_cost, decimals=2))
        self.cat100_cost.setText(format_number(cat100_cost))

        self.need_pust.setText(format_number(pust_total))
        self.need_slas.setText(format_number(slas_total))
        self.need_plas.setText(format_number(plas_total, decimals=1))

        profit = sell - cat100_cost
        if cat100_cost > 0:
            roi = profit / cat100_cost * 100.0
        else:
            roi = 0.0

        sign = "+" if profit >= 0 else "−"
        self.profit_value.setText(f"{sign} {format_number(abs(profit))}")
        if profit > 0:
            self.profit_value.setObjectName("ProfitPositive")
        elif profit < 0:
            self.profit_value.setObjectName("ProfitNegative")
        else:
            self.profit_value.setObjectName("Profit")
        # Force re-polish so the new object name picks up its QSS.
        style = self.profit_value.style()
        style.unpolish(self.profit_value)
        style.polish(self.profit_value)

        self.roi_value.setText(f"{format_number(roi, decimals=1)}%")

        self.state_changed.emit()
