from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Iterable

import pandas as pd

#######################################
# COSTANTI E FUNZIONI DI CALCOLO
#######################################

MASSIMALE_ENASARCO = Decimal("44727.00")
ALIQUOTA_ENASARCO = Decimal("0.085")
ALIQUOTA_INPS = Decimal("0.24")
CONTRIBUTI_INPS_FISSI = Decimal("3600.00")
DIRITTI_CAMERALI = Decimal("120.00")
ALIQUOTA_IVA_ORDINARIA = Decimal("0.22")
ALIQUOTA_RITENUTA = Decimal("0.23")
RITENUTA_COEFFICIENTE_APPLICATO = Decimal("0.5")

IRPEF_BRACKETS: tuple[tuple[Decimal, Decimal], ...] = (
    (Decimal("28000.00"), Decimal("0.23")),
    (Decimal("50000.00"), Decimal("0.35")),
    (Decimal("Infinity"), Decimal("0.43")),
)

CENT = Decimal("0.01")


def _to_decimal(value) -> Decimal:
    try:
        if isinstance(value, Decimal):
            return value
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return Decimal("0")


def _money(value: Decimal) -> float:
    return float(value.quantize(CENT, rounding=ROUND_HALF_UP))


def _normalize_percentage(value: float | Decimal) -> Decimal:
    """Return *value* as a coefficient in the range 0-1 using decimal precision.

    Gli archivi storici dell'applicazione contengono sia valori espressi in forma
    decimale (``0.4`` per il 40%) sia in percentuale intera (``40``). Per garantire
    la compatibilità con entrambi i formati convertiamo automaticamente tutto in
    coefficienti.
    """

    coeff = _to_decimal(value)
    if coeff <= 0:
        return Decimal("0")
    if coeff > 1:
        coeff /= Decimal("100")
    return coeff


def _sum_numeric(df: pd.DataFrame, column: str) -> Decimal:
    if column not in df.columns or df.empty:
        return Decimal("0")
    series = pd.to_numeric(df[column], errors="coerce").fillna(0)
    total = series.sum()
    return _to_decimal(total)


def _ensure_columns(df: pd.DataFrame, required: Iterable[str]) -> pd.DataFrame:
    missing = [col for col in required if col not in df.columns]
    if not missing:
        return df
    for col in missing:
        df[col] = 0
    return df


@dataclass(frozen=True)
class FiscalSnapshot:
    bonifico: Decimal
    base_provvigione: Decimal
    ritenute: Decimal
    enasarco: Decimal
    iva_detraibile_spese: Decimal
    spese_deducibili: Decimal


def calcola_valori(importo, iva_perc, deduc_perc, detra_iva_perc):
    """Calcola IVA scorporata, IVA detraibile e quota deducibile.

    I calcoli seguono le regole fiscali italiane per professionisti in regime
    ordinario: l'IVA detraibile si applica sull'IVA scorporata, mentre la quota
    deducibile è calcolata sulla spesa al netto dell'IVA. Tutti i risultati sono
    arrotondati a due decimali per aderire ai criteri contabili.
    """

    imponibile = _to_decimal(importo)
    if imponibile < 0:
        imponibile = Decimal("0")

    iva_perc = _to_decimal(iva_perc)
    deduc_coeff = _normalize_percentage(deduc_perc)
    detra_coeff = _normalize_percentage(detra_iva_perc)

    if iva_perc > 0:
        iva_scorporata = imponibile * (iva_perc / (Decimal("100") + iva_perc))
    else:
        iva_scorporata = Decimal("0")

    imponibile_netto = imponibile - iva_scorporata
    iva_det = iva_scorporata * detra_coeff
    imp_ded = imponibile_netto * deduc_coeff

    return _money(iva_scorporata), _money(iva_det), _money(imp_ded)


def calcola_incasso_dettagli(base_provvigione) -> dict[str, float]:
    """Calcola i componenti dell'incasso a partire dalla base provvigionale."""

    base = _to_decimal(base_provvigione)
    if base <= 0:
        return {
            "IVA": 0.0,
            "Ritenuta": 0.0,
            "Enasarco": 0.0,
            "Bonifico Finale": 0.0,
        }

    iva = base * ALIQUOTA_IVA_ORDINARIA
    ritenuta = base * ALIQUOTA_RITENUTA * RITENUTA_COEFFICIENTE_APPLICATO
    enasarco = base * ALIQUOTA_ENASARCO
    bonifico = base + iva - ritenuta - enasarco

    return {
        "IVA": _money(iva),
        "Ritenuta": _money(ritenuta),
        "Enasarco": _money(enasarco),
        "Bonifico Finale": _money(bonifico),
    }

def ricalcola_riepilogo(prof_df, casa_df, incassi_df):
    # Funzione presente nel tuo codice originale
    if incassi_df.empty:
        return pd.DataFrame()
    anno = int(pd.to_numeric(incassi_df.get("Anno", pd.Series([2024])), errors="coerce").mode(dropna=True).iloc[0])
    bonifico_tot = _sum_numeric(incassi_df, "Bonifico Finale")
    importo_prof = _sum_numeric(_ensure_columns(prof_df.copy(), ["Importo Lordo"]), "Importo Lordo")
    importo_casa = _sum_numeric(_ensure_columns(casa_df.copy(), ["Importo Lordo"]), "Importo Lordo")
    importo_deduc = _sum_numeric(_ensure_columns(prof_df.copy(), ["Importo Deducibile"]), "Importo Deducibile")

    totale_spese = importo_prof + importo_casa
    liquidita = bonifico_tot - totale_spese
    base_imponibile_ridotta = bonifico_tot - importo_deduc

    riepilogo_data = {
        "Mese": ["TUTTO L'ANNO"],
        "Anno": [anno],
        "Bonifico Ricevuto": [_money(bonifico_tot)],
        "Importo Lordo_Prof": [_money(importo_prof)],
        "Importo Lordo_Casa": [_money(importo_casa)],
        "Totale Spese": [_money(totale_spese)],
        "Liquidità Residua": [_money(liquidita)],
        "Importo Deducibile": [_money(importo_deduc)],
        "Base Imponibile Ridotta": [_money(base_imponibile_ridotta)],
    }
    return pd.DataFrame(riepilogo_data)

def ricalcola_previsione(riepilogo_df, prof_df, incassi_df):
    # Funzione presente nel tuo codice originale
    if riepilogo_df.empty or incassi_df.empty:
        return pd.DataFrame()
    base_provv_tot = _sum_numeric(incassi_df, "Base Provvigione")
    ritenute_tot = _sum_numeric(incassi_df, "Ritenuta")
    enasarco_tot = _sum_numeric(incassi_df, "Enasarco")

    bonifico_tot = _to_decimal(riepilogo_df.loc[0, "Bonifico Ricevuto"]) if not riepilogo_df.empty else Decimal("0")
    importo_deducibile = _to_decimal(riepilogo_df.loc[0, "Importo Deducibile"]) if not riepilogo_df.empty else Decimal("0")

    spese_iva_detraibile = _sum_numeric(_ensure_columns(prof_df.copy(), ["IVA Detraibile"]), "IVA Detraibile")

    snapshot = FiscalSnapshot(
        bonifico=bonifico_tot,
        base_provvigione=base_provv_tot,
        ritenute=ritenute_tot,
        enasarco=enasarco_tot,
        iva_detraibile_spese=spese_iva_detraibile,
        spese_deducibili=importo_deducibile,
    )

    base_imponibile_irpef = snapshot.base_provvigione - snapshot.enasarco - snapshot.spese_deducibili
    if base_imponibile_irpef < 0:
        base_imponibile_irpef = Decimal("0")

    iva_scorporata = Decimal("0")
    if snapshot.bonifico > 0:
        iva_scorporata = snapshot.bonifico * (ALIQUOTA_IVA_ORDINARIA / (Decimal("1") + ALIQUOTA_IVA_ORDINARIA))
    iva_net = iva_scorporata - snapshot.iva_detraibile_spese
    if iva_net < 0:
        iva_net = Decimal("0")

    contributi_inps = base_imponibile_irpef * ALIQUOTA_INPS

    def calcola_irpef(base_imponibile: Decimal) -> Decimal:
        imponibile_residuo = base_imponibile
        imposta = Decimal("0")
        soglia_precedente = Decimal("0")
        for soglia, aliquota in IRPEF_BRACKETS:
            if imponibile_residuo <= 0:
                break
            if soglia.is_finite():
                limite = soglia - soglia_precedente
            else:
                limite = imponibile_residuo
            imponibile_scaglione = min(imponibile_residuo, limite)
            if imponibile_scaglione > 0:
                imposta += imponibile_scaglione * aliquota
                imponibile_residuo -= imponibile_scaglione
            soglia_precedente = soglia if soglia.is_finite() else soglia_precedente
        return imposta

    irpef_lorda = calcola_irpef(base_imponibile_irpef)
    irpef_netta = irpef_lorda - snapshot.ritenute
    if irpef_netta < 0:
        irpef_netta = Decimal("0")

    totale_tasse = irpef_netta + contributi_inps + iva_net + CONTRIBUTI_INPS_FISSI + DIRITTI_CAMERALI

    previsione_data = {
        "Mese": ["TUTTO L'ANNO"],
        "Anno": [int(riepilogo_df.loc[0, "Anno"]) if not riepilogo_df.empty else 2024],
        "Bonifico Ricevuto": [_money(snapshot.bonifico)],
        "Base Provvigione Totale": [_money(snapshot.base_provvigione)],
        "Enasarco": [_money(snapshot.enasarco)],
        "Ritenuta d'Acconto": [_money(snapshot.ritenute)],
        "Spese Deducibili": [_money(snapshot.spese_deducibili)],
        "Base Imponibile IRPEF": [_money(base_imponibile_irpef)],
        "IRPEF Lorda": [_money(irpef_lorda)],
        "IRPEF Netta": [_money(irpef_netta)],
        "Contributi INPS": [_money(contributi_inps)],
        "Contributi INPS Fissi": [_money(CONTRIBUTI_INPS_FISSI)],
        "Diritti Camerali": [_money(DIRITTI_CAMERALI)],
        "IVA Scorporata": [_money(iva_scorporata)],
        "IVA Detraibile": [_money(spese_iva_detraibile)],
        "IVA Netta": [_money(iva_net)],
        "Totale Tasse": [_money(totale_tasse)],
    }
    return pd.DataFrame(previsione_data)

def riepilogo_mensile(prof_df, casa_df, incassi_df):
    # Funzione presente nel tuo codice originale
    if incassi_df.empty:
        return pd.DataFrame()
    incassi_mens = incassi_df.groupby(["Mese","Anno"])["Bonifico Finale"].sum().reset_index().rename(columns={"Bonifico Finale":"Incassi"})
    prof_mens = prof_df.groupby(["Mese","Anno"]).agg({"Importo Lordo":"sum","Importo Deducibile":"sum"}).reset_index().rename(columns={"Importo Lordo":"Spese Prof"})
    casa_mens = casa_df.groupby(["Mese","Anno"])["Importo Lordo"].sum().reset_index().rename(columns={"Importo Lordo":"Spese Casa"})

    df_mens = pd.merge(incassi_mens, prof_mens, on=["Mese","Anno"], how="left")
    df_mens = pd.merge(df_mens, casa_mens, on=["Mese","Anno"], how="left")

    df_mens["Spese Prof"] = df_mens["Spese Prof"].fillna(0)
    df_mens["Spese Casa"] = df_mens["Spese Casa"].fillna(0)
    df_mens["Importo Deducibile"] = df_mens["Importo Deducibile"].fillna(0)

    df_mens["Totale Spese"] = df_mens["Spese Prof"] + df_mens["Spese Casa"]
    df_mens["Liquidità Residua"] = df_mens["Incassi"] - df_mens["Totale Spese"]
    df_mens["Base Imponibile Ridotta"] = df_mens["Incassi"] - df_mens["Importo Deducibile"]

    return df_mens

def ricalcola_enasarco_con_massimale(incassi_df):
    # Funzione presente nel tuo codice originale (prima nel main_window)
    if incassi_df.empty or "Mese" not in incassi_df.columns or "Anno" not in incassi_df.columns:
        return
    if "Base Provvigione" not in incassi_df.columns or "IVA" not in incassi_df.columns or "Ritenuta" not in incassi_df.columns:
        return

    mese_map = {
        "Gennaio":1, "Febbraio":2, "Marzo":3, "Aprile":4, "Maggio":5, "Giugno":6,
        "Luglio":7, "Agosto":8, "Settembre":9, "Ottobre":10, "Novembre":11, "Dicembre":12
    }

    incassi_df["mese_order"] = incassi_df["Mese"].map(mese_map)
    for anno in incassi_df["Anno"].unique():
        enasarco_cumulato = Decimal("0")
        df_anno = incassi_df[incassi_df["Anno"] == anno].copy()
        df_anno.sort_values("mese_order", inplace=True)
        for idx, row in df_anno.iterrows():
            base = _to_decimal(row["Base Provvigione"])
            iva = _to_decimal(row["IVA"])
            ritenuta = _to_decimal(row["Ritenuta"])
            enas_calcolato = base * ALIQUOTA_ENASARCO
            spazio = MASSIMALE_ENASARCO - enasarco_cumulato
            if spazio <= 0:
                enas_finale = Decimal("0")
                bonifico = base + iva - ritenuta
            else:
                enas_finale = min(enas_calcolato, spazio)
                bonifico = base + iva - ritenuta - enas_finale
            incassi_df.at[idx, "Enasarco"] = _money(enas_finale)
            incassi_df.at[idx, "Bonifico Finale"] = _money(bonifico)
            enasarco_cumulato += enas_finale
    incassi_df.drop("mese_order", axis=1, inplace=True)
