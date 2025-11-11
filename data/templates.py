"""Collection of default templates and helper factories for the application."""

from __future__ import annotations

from datetime import datetime
from typing import List

import pandas as pd

mesi = [
    "Gennaio",
    "Febbraio",
    "Marzo",
    "Aprile",
    "Maggio",
    "Giugno",
    "Luglio",
    "Agosto",
    "Settembre",
    "Ottobre",
    "Novembre",
    "Dicembre",
]

PROFESSIONAL_EXPENSE_COLUMNS: List[str] = [
    "Seleziona",
    "Data",
    "Mese",
    "Anno",
    "Categoria",
    "Importo Lordo",
    "IVA",
    "IVA Detraibile",
    "Importo Deducibile",
    "Note",
]

HOUSEHOLD_EXPENSE_COLUMNS: List[str] = [
    "Seleziona",
    "Data",
    "Mese",
    "Anno",
    "Categoria",
    "Importo Lordo",
    "Note",
]

EARNINGS_COLUMNS: List[str] = [
    "Seleziona",
    "Data",
    "Mese",
    "Anno",
    "Base Provvigione",
    "IVA",
    "Ritenuta",
    "Enasarco",
    "Bonifico Finale",
]

CATEGORY_COLUMNS: List[str] = [
    "Categoria",
    "IVA %",
    "Deducibilità %",
    "Detraibilità IVA %",
]

voci_professionali_template = [
    {"Categoria": "Carburante", "IVA %": 22, "Deducibilità %": 0.8, "Detraibilità IVA %": 0.40},
    {"Categoria": "Manutenzione Veicolo", "IVA %": 22, "Deducibilità %": 1.0, "Detraibilità IVA %": 1.0},
    {"Categoria": "Assicurazione Auto", "IVA %": 0, "Deducibilità %": 1.0, "Detraibilità IVA %": 0},
    {"Categoria": "Bollo Auto", "IVA %": 0, "Deducibilità %": 1.0, "Detraibilità IVA %": 0},
    {"Categoria": "Vitto", "IVA %": 10, "Deducibilità %": 0.75, "Detraibilità IVA %": 1.0},
    {"Categoria": "Hotel", "IVA %": 10, "Deducibilità %": 0.75, "Detraibilità IVA %": 1.0},
    {"Categoria": "Consulenze", "IVA %": 22, "Deducibilità %": 1.0, "Detraibilità IVA %": 1.0},
    {"Categoria": "Sponsorizzazioni", "IVA %": 0, "Deducibilità %": 1.0, "Detraibilità IVA %": 0},
]

voci_casa_template = [
    {"Categoria": "Affitto", "IVA %": 0, "Deducibilità %": 1.0, "Detraibilità IVA %": 0},
    {"Categoria": "Spesa Alimentare", "IVA %": 4, "Deducibilità %": 1.0, "Detraibilità IVA %": 1.0},
    {"Categoria": "Manutenzione Casa", "IVA %": 22, "Deducibilità %": 1.0, "Detraibilità IVA %": 1.0},
    {"Categoria": "Mutuo", "IVA %": 0, "Deducibilità %": 1.0, "Detraibilità IVA %": 0},
]


def data_oggi() -> str:
    """Return today's date formatted for the UI."""

    return datetime.now().strftime("%d/%m/%Y")


def empty_professional_expenses() -> pd.DataFrame:
    """Create an empty dataframe with the professional expenses schema."""

    return pd.DataFrame(columns=PROFESSIONAL_EXPENSE_COLUMNS)


def empty_household_expenses() -> pd.DataFrame:
    """Create an empty dataframe with the household expenses schema."""

    return pd.DataFrame(columns=HOUSEHOLD_EXPENSE_COLUMNS)


def empty_earnings() -> pd.DataFrame:
    """Create an empty dataframe with the expected earnings schema."""

    return pd.DataFrame(columns=EARNINGS_COLUMNS)


def default_professional_categories() -> pd.DataFrame:
    """Return the default professional categories as a dataframe."""

    return pd.DataFrame(voci_professionali_template, columns=CATEGORY_COLUMNS)


def default_household_categories() -> pd.DataFrame:
    """Return the default household categories as a dataframe."""

    return pd.DataFrame(voci_casa_template, columns=CATEGORY_COLUMNS)
