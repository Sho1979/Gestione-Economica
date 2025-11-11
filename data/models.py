"""Data models and Qt adapters used across the application."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import pandas as pd
from PySide6.QtCore import QAbstractTableModel, QModelIndex, QLocale, Qt

from .calculations import calcola_valori
from .templates import (
    default_household_categories,
    default_professional_categories,
    empty_earnings,
    empty_household_expenses,
    empty_professional_expenses,
)


@dataclass
class FinanceData:
    """Container for all the dataframes managed by the application."""

    prof_df: pd.DataFrame
    casa_df: pd.DataFrame
    incassi_df: pd.DataFrame
    categorie_prof_df: pd.DataFrame
    categorie_casa_df: pd.DataFrame

    @classmethod
    def create_defaults(cls) -> "FinanceData":
        """Return a new instance populated with the default templates."""

        return cls(
            empty_professional_expenses(),
            empty_household_expenses(),
            empty_earnings(),
            default_professional_categories(),
            default_household_categories(),
        )

    def clone(self) -> "FinanceData":
        """Return a deep copy of the current datasets."""

        return FinanceData(
            self.prof_df.copy(deep=True),
            self.casa_df.copy(deep=True),
            self.incassi_df.copy(deep=True),
            self.categorie_prof_df.copy(deep=True),
            self.categorie_casa_df.copy(deep=True),
        )


class PandasModel(QAbstractTableModel):
    def __init__(
        self,
        df: pd.DataFrame,
        categorie_prof_df: Optional[pd.DataFrame] = None,
        *,
        is_prof: bool = False,
        parent=None,
    ):
        super().__init__(parent)
        self._df = df
        self.categorie_prof_df = categorie_prof_df
        self.is_prof = is_prof
        self._locale = QLocale(QLocale.Italian, QLocale.Italy)

    def rowCount(self, parent: QModelIndex | None = None):
        return len(self._df.index)

    def columnCount(self, parent: QModelIndex | None = None):
        return len(self._df.columns)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole):
        if not index.isValid():
            return None

        row = index.row()
        column = index.column()
        value = self._df.iat[row, column]
        column_name = self._df.columns[column]

        if role == Qt.DisplayRole:
            if isinstance(value, (int, float)):
                return self._locale.toString(float(value), "f", 2)
            if isinstance(value, bool):
                return "✓" if value else ""
            return str(value)

        if role == Qt.CheckStateRole and column_name == "Seleziona":
            return Qt.Checked if bool(value) else Qt.Unchecked

        if role == Qt.TextAlignmentRole and isinstance(value, (int, float)):
            return Qt.AlignRight | Qt.AlignVCenter

        return None

    def flags(self, index):
        if not index.isValid():
            return Qt.ItemIsEnabled
        col_name = self._df.columns[index.column()]
        if col_name == "Seleziona":
            return Qt.ItemIsSelectable | Qt.ItemIsUserCheckable | Qt.ItemIsEnabled
        if col_name in ["Importo Lordo", "Note"]:
            return Qt.ItemIsSelectable | Qt.ItemIsEditable | Qt.ItemIsEnabled
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled

    def setData(self, index, value, role=Qt.EditRole):
        if not index.isValid():
            return False

        col_name = self._df.columns[index.column()]
        row = index.row()

        if col_name == "Seleziona" and role in (Qt.EditRole, Qt.CheckStateRole):
            is_checked = value in (True, Qt.Checked, "true", "True", 1)
            self._df.iat[row, index.column()] = bool(is_checked)
            self.dataChanged.emit(index, index, [Qt.CheckStateRole, Qt.DisplayRole])
            return True

        if role == Qt.EditRole:
            col_name = self._df.columns[index.column()]
            if col_name == "Importo Lordo":
                try:
                    val = float(value)
                except ValueError:
                    return False
                self._df.iat[row, index.column()] = val
                if self.is_prof and self.categorie_prof_df is not None:
                    cat_col = self._df.columns.get_loc("Categoria")
                    cat = self._df.iat[row, cat_col]
                    r = self.categorie_prof_df[self.categorie_prof_df["Categoria"] == cat]
                    if not r.empty:
                        iva_perc = r["IVA %"].values[0]
                        deduc = r["Deducibilità %"].values[0]
                        detra = r["Detraibilità IVA %"].values[0]
                        iva_scorp, iva_det, imp_ded = calcola_valori(val, iva_perc, deduc, detra)
                        iva_col = self._df.columns.get_loc("IVA")
                        iva_det_col = self._df.columns.get_loc("IVA Detraibile")
                        imp_ded_col = self._df.columns.get_loc("Importo Deducibile")
                        self._df.iat[row, iva_col] = iva_scorp
                        self._df.iat[row, iva_det_col] = iva_det
                        self._df.iat[row, imp_ded_col] = imp_ded
                        self.dataChanged.emit(self.index(row, iva_col), self.index(row, imp_ded_col), [Qt.DisplayRole])
            elif col_name == "Note":
                self._df.iat[row, index.column()] = str(value)
            elif col_name == "Seleziona":
                val_str = str(value).strip().lower()
                val_bool = val_str in ["true", "1", "✓", "si", "sì"]
                self._df.iat[row, index.column()] = val_bool
            else:
                self._df.iat[row, index.column()] = value

            self.dataChanged.emit(index, index, [Qt.DisplayRole])
            return True
        return False

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            if self._df.empty:
                return None
            if orientation == Qt.Horizontal:
                if section < 0 or section >= len(self._df.columns):
                    return None
                return self._df.columns[section]
            if section < 0 or section >= len(self._df.index):
                return None
            return str(self._df.index[section])
        return None
