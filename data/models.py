import pandas as pd
from PySide6.QtCore import QAbstractTableModel, Qt
from .calculations import calcola_valori

class PandasModel(QAbstractTableModel):
    def __init__(self, df: pd.DataFrame, categorie_prof_df=None, is_prof=False, parent=None):
        super().__init__(parent)
        self._df = df
        self.categorie_prof_df = categorie_prof_df
        self.is_prof = is_prof

    def rowCount(self, parent=None):
        return len(self._df.index)

    def columnCount(self, parent=None):
        return len(self._df.columns)

    def data(self, index, role=Qt.DisplayRole):
        if index.isValid() and role == Qt.DisplayRole:
            val = self._df.iat[index.row(), index.column()]
            if isinstance(val, (int,float)):
                return f"{val:.2f}"
            elif isinstance(val, bool):
                return "✓" if val else ""
            return str(val)
        return None

    def flags(self, index):
        if not index.isValid():
            return Qt.ItemIsEnabled
        col_name = self._df.columns[index.column()]
        if col_name in ["Importo Lordo","Note","Seleziona"]:
            return Qt.ItemIsSelectable | Qt.ItemIsEditable | Qt.ItemIsEnabled
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled

    def setData(self, index, value, role=Qt.EditRole):
        if index.isValid() and role == Qt.EditRole:
            col_name = self._df.columns[index.column()]
            row = index.row()
            if col_name == "Importo Lordo":
                try:
                    val = float(value)
                except ValueError:
                    return False
                self._df.iat[row, index.column()] = val
                if self.is_prof and self.categorie_prof_df is not None:
                    cat_col = self._df.columns.get_loc("Categoria")
                    cat = self._df.iat[row, cat_col]
                    r = self.categorie_prof_df[self.categorie_prof_df["Categoria"]==cat]
                    if not r.empty:
                        iva_perc = r["IVA %"].values[0]
                        deduc = r["Deducibilità %"].values[0]
                        detra = r["Detraibilità IVA %"].values[0]
                        iva_scorp, iva_det, imp_ded = calcola_valori(val,iva_perc,deduc,detra)
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
                val_bool = val_str in ["true","1","✓","si","sì"]
                self._df.iat[row, index.column()] = val_bool
            else:
                self._df.iat[row, index.column()] = value

            self.dataChanged.emit(index, index, [Qt.DisplayRole])
            return True
        return False

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            if self._df.empty:
                # DataFrame vuoto, nessuna colonna o riga
                return None
            if orientation == Qt.Horizontal:
                if section < 0 or section >= len(self._df.columns):
                    return None  # Evita errori se section fuori range
                return self._df.columns[section]
            else:
                if section < 0 or section >= len(self._df.index):
                    return None
                return str(self._df.index[section])
        return None

