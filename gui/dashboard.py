from PySide6.QtCharts import QChart, QChartView, QPieSeries, QBarSeries, QBarSet, QBarCategoryAxis, QLineSeries, QValueAxis
from PySide6.QtGui import QPainter
from data.calculations import ricalcola_enasarco_con_massimale, riepilogo_mensile
from data.templates import mesi
import pandas as pd

def aggiorna_dashboard(layout, info_label, prof_df, casa_df, incassi_df, anno, mese):
    # Questa è la logica presa integralmente da aggiorna_dashboard_da_filtri()
    # limitata alla parte di creazione dei grafici, senza la logica di filtraggio
    # In realtà abbiamo già tutta la logica nel codice finale fornito. La riprendiamo integralmente

    while layout.count() > 3:
        item = layout.takeAt(3)
        if item.widget():
            item.widget().deleteLater()

    if prof_df.empty and casa_df.empty and incassi_df.empty:
        info_label.setText("Nessun dato per la Dashboard")
        return
    info_label.setText("")

    if not incassi_df.empty:
        ricalcola_enasarco_con_massimale(incassi_df)

    df_mensile = riepilogo_mensile(prof_df, casa_df, incassi_df)

    if mese == "Tutti":
        if df_mensile.empty:
            info_label.setText("Nessun dato per la Dashboard")
            return
        mesi_map = {m:i for i,m in enumerate(mesi, start=1)}
        df_mensile["MeseOrd"] = df_mensile["Mese"].map(mesi_map)
        df_mensile.sort_values("MeseOrd", inplace=True)

        incassi_bs = QBarSet("Incassi")
        spese_bs = QBarSet("Totale Spese")
        mesi_labels = []
        for i, row in df_mensile.iterrows():
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
        layout.addWidget(chart_view)
    else:
        if df_mensile.empty:
            info_label.setText("Nessun dato per la Dashboard")
            return
        riepilogo_f = df_mensile.rename(columns={
            "Incassi": "Bonifico Ricevuto",
            "Spese Prof":"Importo Lordo_Prof",
            "Spese Casa":"Importo Lordo_Casa"
        })

        if riepilogo_f.empty or "Totale Spese" not in riepilogo_f.columns or "Bonifico Ricevuto" not in riepilogo_f.columns:
            info_label.setText("Nessun dato per la Dashboard")
            return

        totale_spese = riepilogo_f["Totale Spese"].sum()
        liquidita = riepilogo_f["Liquidità Residua"].sum()
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
        layout.addWidget(chart_view_torta)

        full_year_prof = prof_df[prof_df["Anno"]==anno]
        full_year_casa = casa_df[casa_df["Anno"]==anno]
        full_year_inc = incassi_df[incassi_df["Anno"]==anno]

        full_mensile = riepilogo_mensile(full_year_prof, full_year_casa, full_year_inc)
        if full_mensile.empty:
            return
        mesi_map = {m:i for i,m in enumerate(mesi)}
        full_mensile["MeseOrd"] = full_mensile["Mese"].map(mesi_map)
        full_mensile.sort_values("MeseOrd", inplace=True)

        full_mensile["IncassiCumul"] = full_mensile["Incassi"].cumsum()
        full_mensile["SpeseCumul"] = full_mensile["Totale Spese"].cumsum()

        incassi_line = QLineSeries()
        incassi_line.setName("Incassi Cumul.")
        spese_line = QLineSeries()
        spese_line.setName("Spese Cumul.")

        mesi_labels = []
        for i, row in full_mensile.iterrows():
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
        layout.addWidget(chart_view_line)
