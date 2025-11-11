"""Utilities for loading, saving and resetting application datasets."""

from __future__ import annotations

from pathlib import Path
from typing import Optional, Tuple

import pandas as pd
from PySide6.QtWidgets import QFileDialog, QMessageBox, QWidget

from data.models import FinanceData
from data.templates import data_oggi


class DataRepository:
    """Centralized access to the CSV storage used by the application."""

    FILE_MAP = {
        "prof_df": "prof_spese.csv",
        "casa_df": "casa_spese.csv",
        "incassi_df": "incassi.csv",
        "categorie_prof_df": "categorie_prof.csv",
        "categorie_casa_df": "categorie_casa.csv",
    }

    NUMERIC_COLUMNS = {
        "prof_df": ["Importo Lordo", "IVA", "IVA Detraibile", "Importo Deducibile"],
        "casa_df": ["Importo Lordo"],
        "incassi_df": ["Base Provvigione", "IVA", "Ritenuta", "Enasarco", "Bonifico Finale"],
        "categorie_prof_df": ["IVA %", "Deducibilità %", "Detraibilità IVA %"],
        "categorie_casa_df": ["IVA %", "Deducibilità %", "Detraibilità IVA %"],
    }

    def __init__(self, default_data_dir: Path):
        self.default_data_dir = Path(default_data_dir)
        self.default_data_dir.mkdir(parents=True, exist_ok=True)

    def _load_dataframe(self, directory: Path, filename: str, key: str) -> Optional[pd.DataFrame]:
        path = directory / filename
        if not path.exists():
            return None
        df = pd.read_csv(path)
        return self._coerce_numeric(df, key)

    def _coerce_numeric(self, df: pd.DataFrame, key: str) -> pd.DataFrame:
        numeric_columns = self.NUMERIC_COLUMNS.get(key, [])
        for column in numeric_columns:
            if column in df.columns:
                df[column] = (
                    df[column]
                    .astype(str)
                    .str.replace(".", "", regex=False)
                    .str.replace(",", ".", regex=False)
                )
                df[column] = pd.to_numeric(df[column], errors="coerce").fillna(0.0)
        return df

    def load(self, directory: Optional[Path] = None) -> Tuple[FinanceData, bool]:
        """Load data from *directory* or the default location.

        Returns a tuple ``(FinanceData, loaded_anything)`` where ``loaded_anything`` is
        ``True`` if at least one dataset (expenses or earnings) was found.
        """

        target_dir = Path(directory) if directory else self.default_data_dir
        data = FinanceData.create_defaults()
        loaded_any = False

        for attr, filename in self.FILE_MAP.items():
            df = self._load_dataframe(target_dir, filename, attr)
            if df is not None:
                setattr(data, attr, df)
                loaded_any = True
        return data, loaded_any

    def save(self, data: FinanceData, directory: Optional[Path] = None) -> Path:
        """Persist *data* to CSV files inside *directory*.

        The directory is created if it does not exist. The resolved path is returned.
        """

        target_dir = Path(directory) if directory else self.default_data_dir
        target_dir.mkdir(parents=True, exist_ok=True)
        for attr, filename in self.FILE_MAP.items():
            df = getattr(data, attr)
            df.to_csv(target_dir / filename, index=False)
        return target_dir

    # Dialog helpers -----------------------------------------------------------------

    def _select_directory(self, parent: QWidget, caption: str) -> Optional[Path]:
        dir_name = QFileDialog.getExistingDirectory(parent, caption, str(self.default_data_dir))
        if not dir_name:
            return None
        return Path(dir_name)

    def load_with_dialog(self, parent: QWidget) -> Tuple[FinanceData, bool]:
        directory = self._select_directory(parent, "Seleziona Cartella per Caricare")
        if directory is None:
            return FinanceData.create_defaults(), False
        data, loaded_any = self.load(directory)
        if loaded_any:
            QMessageBox.information(parent, "Caricamento", "Dati caricati con successo!")
        else:
            QMessageBox.warning(parent, "Caricamento", "Nessun file valido trovato nella cartella selezionata.")
        return data, loaded_any

    def save_with_dialog(self, parent: QWidget, data: FinanceData) -> bool:
        directory = self._select_directory(parent, "Seleziona Cartella per Salvare")
        if directory is None:
            return False
        self.save(data, directory)
        QMessageBox.information(parent, "Salvataggio", f"Dati salvati con successo in {directory}!")
        return True

    def reset(self, parent: Optional[QWidget] = None) -> FinanceData:
        data = FinanceData.create_defaults()
        if parent is not None:
            QMessageBox.information(parent, "Reset", "Tutti i dati sono stati azzerati.")
        return data


def inizializza_dataset_se_vuoto(data: FinanceData) -> FinanceData:
    """Ensure that the default rows exist for brand-new datasets."""

    if data.prof_df.empty:
        for _, row in data.categorie_prof_df.iterrows():
            data.prof_df.loc[len(data.prof_df)] = [
                False,
                data_oggi(),
                "Gennaio",
                2024,
                row["Categoria"],
                0,
                0,
                0,
                0,
                "",
            ]
    if data.casa_df.empty:
        for _, row in data.categorie_casa_df.iterrows():
            data.casa_df.loc[len(data.casa_df)] = [
                False,
                data_oggi(),
                "Gennaio",
                2024,
                row["Categoria"],
                0,
                "",
            ]
    if data.incassi_df.empty:
        data.incassi_df = data.incassi_df.copy()
    return data
