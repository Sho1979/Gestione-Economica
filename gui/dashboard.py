"""Dashboard rendering helpers."""

from __future__ import annotations

import pandas as pd
from PySide6.QtCharts import (
    QBarCategoryAxis,
    QBarSeries,
    QBarSet,
    QChart,
    QChartView,
    QLineSeries,
    QPieSeries,
    QValueAxis,
)
from PySide6.QtCore import Qt, QLocale
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import QVBoxLayout, QWidget

from data.calculations import ricalcola_enasarco_con_massimale, riepilogo_mensile
from data.templates import mesi


LOCALE = QLocale(QLocale.Italian, QLocale.Italy)


def _fmt_currency(value: float) -> str:
    return LOCALE.toCurrencyString(float(value), "€")


def _clear_layout(layout: QVBoxLayout) -> None:
    while layout.count():
        item = layout.takeAt(0)
        widget = item.widget()
        if widget is not None:
            widget.deleteLater()


def aggiorna_dashboard(
    chart_container: QVBoxLayout,
    info_widget: QWidget,
    prof_df: pd.DataFrame,
    casa_df: pd.DataFrame,
    incassi_df: pd.DataFrame,
    anno: int,
    mese: str,
) -> None:
    """Render the dashboard charts inside *chart_container*."""

    _clear_layout(chart_container)

    if prof_df.empty and casa_df.empty and incassi_df.empty:
        info_widget.setText("Nessun dato per la Dashboard")
        return

    info_widget.setText("")

    prof_df = prof_df.copy()
    casa_df = casa_df.copy()
    incassi_df = incassi_df.copy()

    if not incassi_df.empty:
        ricalcola_enasarco_con_massimale(incassi_df)

    df_mensile = riepilogo_mensile(prof_df, casa_df, incassi_df)

    if mese == "Tutti":
        if df_mensile.empty:
            info_widget.setText("Nessun dato per la Dashboard")
            return
        mesi_map = {m: i for i, m in enumerate(mesi, start=1)}
        df_mensile["MeseOrd"] = df_mensile["Mese"].map(mesi_map)
        df_mensile.sort_values("MeseOrd", inplace=True)

        totale_incassi = df_mensile["Incassi"].sum()
        totale_spese = df_mensile["Totale Spese"].sum()
        liquidita = df_mensile["Liquidità Residua"].sum()
        info_widget.setText(
            f"<b>{anno}</b> • Incassi: {_fmt_currency(totale_incassi)} • Spese: {_fmt_currency(totale_spese)} • Liquidità: {_fmt_currency(liquidita)}"
        )

        incassi_bs = QBarSet("Incassi")
        spese_bs = QBarSet("Totale Spese")
        mesi_labels = []
        for _, row in df_mensile.iterrows():
            mesi_labels.append(row["Mese"])
            incassi_bs.append(row["Incassi"])
            spese_bs.append(row["Totale Spese"])

        series = QBarSeries()
        series.append(incassi_bs)
        series.append(spese_bs)

        chart = QChart()
        chart.addSeries(series)
        chart.setTitle("Confronto Mensile Incassi vs Spese (Anno)")
        chart.legend().setVisible(True)
        chart.legend().setAlignment(Qt.AlignBottom)

        axisX = QBarCategoryAxis()
        axisX.append(mesi_labels)
        chart.addAxis(axisX, Qt.AlignBottom)
        series.attachAxis(axisX)

        chart.createDefaultAxes()
        chart_view = QChartView(chart)
        chart_view.setRenderHint(QPainter.Antialiasing, True)
        chart_container.addWidget(chart_view)
        return

    if df_mensile.empty:
        info_widget.setText("Nessun dato per la Dashboard")
        return

    mese_df = df_mensile[(df_mensile["Anno"] == anno) & (df_mensile["Mese"] == mese)]
    if mese_df.empty:
        info_widget.setText("Nessun dato per la Dashboard")
        return

    riepilogo_f = mese_df.rename(
        columns={
            "Incassi": "Bonifico Ricevuto",
            "Spese Prof": "Importo Lordo_Prof",
            "Spese Casa": "Importo Lordo_Casa",
        }
    )

    if (
        riepilogo_f.empty
        or "Totale Spese" not in riepilogo_f.columns
        or "Bonifico Ricevuto" not in riepilogo_f.columns
    ):
        info_widget.setText("Nessun dato per la Dashboard")
        return

    totale_spese = riepilogo_f["Totale Spese"].sum()
    liquidita = riepilogo_f["Liquidità Residua"].sum()
    incassi_totali = riepilogo_f["Bonifico Ricevuto"].sum()
    info_widget.setText(
        f"<b>{mese} {anno}</b> • Incassi: {_fmt_currency(incassi_totali)} • Spese: {_fmt_currency(totale_spese)} • Liquidità: {_fmt_currency(liquidita)}"
    )
    series = QPieSeries()
    series.append("Spese", totale_spese)
    series.append("Liquidità", liquidita)

    chart_torta = QChart()
    chart_torta.addSeries(series)
    chart_torta.setTitle("Spese vs Liquidità (Mese)")
    chart_torta.legend().setVisible(True)
    chart_torta.legend().setAlignment(Qt.AlignBottom)

    chart_view_torta = QChartView(chart_torta)
    chart_view_torta.setRenderHint(QPainter.Antialiasing, True)
    chart_container.addWidget(chart_view_torta)

    full_year_prof = prof_df[prof_df["Anno"] == anno]
    full_year_casa = casa_df[casa_df["Anno"] == anno]
    full_year_inc = incassi_df[incassi_df["Anno"] == anno]

    full_mensile = riepilogo_mensile(full_year_prof, full_year_casa, full_year_inc)
    if full_mensile.empty:
        return
    mesi_map = {m: i for i, m in enumerate(mesi)}
    full_mensile["MeseOrd"] = full_mensile["Mese"].map(mesi_map)
    full_mensile.sort_values("MeseOrd", inplace=True)

    full_mensile["IncassiCumul"] = full_mensile["Incassi"].cumsum()
    full_mensile["SpeseCumul"] = full_mensile["Totale Spese"].cumsum()

    incassi_line = QLineSeries()
    incassi_line.setName("Incassi Cumul.")
    spese_line = QLineSeries()
    spese_line.setName("Spese Cumul.")

    mesi_labels = []
    for _, row in full_mensile.iterrows():
        x = row["MeseOrd"]
        incassi_line.append(x, row["IncassiCumul"])
        spese_line.append(x, row["SpeseCumul"])
        mesi_labels.append(row["Mese"])

    chart_line = QChart()
    chart_line.addSeries(incassi_line)
    chart_line.addSeries(spese_line)
    chart_line.setTitle("Andamento Cumulativo Incassi vs Spese (Anno)")
    chart_line.legend().setVisible(True)
    chart_line.legend().setAlignment(Qt.AlignBottom)

    axisX = QBarCategoryAxis()
    axisX.append(mesi_labels)
    chart_line.addAxis(axisX, Qt.AlignBottom)
    incassi_line.attachAxis(axisX)
    spese_line.attachAxis(axisX)

    axisY = QValueAxis()
    chart_line.addAxis(axisY, Qt.AlignLeft)
    incassi_line.attachAxis(axisY)
    spese_line.attachAxis(axisY)

    chart_view_line = QChartView(chart_line)
    chart_view_line.setRenderHint(QPainter.Antialiasing, True)
    chart_container.addWidget(chart_view_line)
