"""Main window for the Gestione Economica application."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

import pandas as pd
from PySide6.QtCore import QLocale
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMenuBar,
    QMessageBox,
    QPushButton,
    QStatusBar,
    QTabWidget,
    QTableView,
    QHeaderView,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from data.calculations import (
    calcola_valori,
    calcola_incasso_dettagli,
    ricalcola_previsione,
    ricalcola_riepilogo,
    ricalcola_enasarco_con_massimale,
)
from data.models import PandasModel
from data.templates import data_oggi, mesi
from gui.dashboard import aggiorna_dashboard as render_dashboard
from services.data_io import DataRepository, inizializza_dataset_se_vuoto


class AddCategoryDialog(QDialog):
    """Dialog used to collect new category information."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setWindowTitle("Aggiungi Categoria")
        layout = QFormLayout(self)

        self.cat_name = QLineEdit()
        self.iva_field = QLineEdit("22")
        self.deduc_field = QLineEdit("1.0")
        self.detra_field = QLineEdit("1.0")

        layout.addRow("Nome Categoria:", self.cat_name)
        layout.addRow("IVA %:", self.iva_field)
        layout.addRow("Deducibilità %:", self.deduc_field)
        layout.addRow("Detraibilità IVA %:", self.detra_field)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept_data)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def accept_data(self) -> None:
        nome = self.cat_name.text().strip()
        iva_txt = self.iva_field.text().strip() or "0"
        deduc_txt = self.deduc_field.text().strip() or "0"
        detra_txt = self.detra_field.text().strip() or "0"

        if not nome:
            QMessageBox.warning(self, "Errore", "Inserisci un nome per la categoria.")
            return

        try:
            self.nome = nome
            self.iva = float(iva_txt)
            self.deduc = float(deduc_txt)
            self.detra = float(detra_txt)
        except ValueError:
            QMessageBox.warning(self, "Errore", "Inserisci valori numerici validi per IVA, Deducibilità e Detraibilità.")
            return

        self.accept()

    def getData(self) -> tuple[str, float, float, float]:
        return self.nome, self.iva, self.deduc, self.detra


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Gestione Economica Agente di Commercio")
        self.resize(1280, 800)
        self._locale = QLocale(QLocale.Italian, QLocale.Italy)

        default_data_dir = Path(__file__).resolve().parent.parent / "data_store"
        self.data_repo = DataRepository(default_data_dir)
        data, _ = self.data_repo.load()
        self.finance = inizializza_dataset_se_vuoto(data)

        self._build_ui()
        self._bind_models()
        self._apply_styles()

        self.statusBar().showMessage("Pronto")
        self.ricalcola_totale()

    # Convenience accessors ---------------------------------------------------------

    @property
    def prof_df(self) -> pd.DataFrame:
        return self.finance.prof_df

    @prof_df.setter
    def prof_df(self, value: pd.DataFrame) -> None:
        self.finance.prof_df = value

    @property
    def casa_df(self) -> pd.DataFrame:
        return self.finance.casa_df

    @casa_df.setter
    def casa_df(self, value: pd.DataFrame) -> None:
        self.finance.casa_df = value

    @property
    def incassi_df(self) -> pd.DataFrame:
        return self.finance.incassi_df

    @incassi_df.setter
    def incassi_df(self, value: pd.DataFrame) -> None:
        self.finance.incassi_df = value

    @property
    def categorie_prof_df(self) -> pd.DataFrame:
        return self.finance.categorie_prof_df

    @categorie_prof_df.setter
    def categorie_prof_df(self, value: pd.DataFrame) -> None:
        self.finance.categorie_prof_df = value

    @property
    def categorie_casa_df(self) -> pd.DataFrame:
        return self.finance.categorie_casa_df

    @categorie_casa_df.setter
    def categorie_casa_df(self, value: pd.DataFrame) -> None:
        self.finance.categorie_casa_df = value

    # UI setup ----------------------------------------------------------------------

    def _build_ui(self) -> None:
        menubar = QMenuBar(self)
        file_menu = menubar.addMenu("File")

        carica_action = QAction("Carica Dati", self)
        carica_action.triggered.connect(self.carica_dati)
        file_menu.addAction(carica_action)

        salva_action = QAction("Salva Dati", self)
        salva_action.triggered.connect(self.salva_dati)
        file_menu.addAction(salva_action)

        exit_action = QAction("Esci", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        self.setMenuBar(menubar)

        self.toolbar = QToolBar("Main Toolbar")
        self.addToolBar(self.toolbar)

        aggiorna_action = QAction(QIcon.fromTheme("view-refresh"), "Ricalcola", self)
        aggiorna_action.triggered.connect(self.ricalcola_totale)
        self.toolbar.addAction(aggiorna_action)

        elimina_action = QAction(QIcon.fromTheme("edit-delete"), "Elimina Selezione", self)
        elimina_action.triggered.connect(self.elimina_voce)
        self.toolbar.addAction(elimina_action)

        salva_toolbar_action = QAction(QIcon.fromTheme("document-save"), "Salva", self)
        salva_toolbar_action.triggered.connect(self.salva_dati)
        self.toolbar.addAction(salva_toolbar_action)

        self.setStatusBar(QStatusBar(self))

        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        self.dashboard_tab = self._create_dashboard_tab()
        self.tabs.addTab(self.dashboard_tab, "Dashboard")

        self.prof_tab = self._create_tab_spese_prof()
        self.tabs.addTab(self.prof_tab, "Spese Professionali")

        self.casa_tab = self._create_tab_spese_casa()
        self.tabs.addTab(self.casa_tab, "Spese Casa")

        self.incassi_tab = self._create_tab_incassi()
        self.tabs.addTab(self.incassi_tab, "Incassi Mensili")

        self.riepilogo_tab = self._create_table_tab("Riepilogo")
        self.tabs.addTab(self.riepilogo_tab, "Riepilogo")

        self.previsione_tab = self._create_table_tab("Previsione Tasse")
        self.tabs.addTab(self.previsione_tab, "Previsione Tasse")

    def _apply_styles(self) -> None:
        self.setStyleSheet(
            """
            QMainWindow {
                background: #FAF9F6;
            }
            QTabWidget::pane {
                border: 1px solid #C8C6C6;
                background: #FAF9F6;
            }
            QLabel {
                color: #444444;
            }
            QTableView {
                background: #FFFFFF;
                alternate-background-color: #F0F0F0;
                gridline-color: #CCCCCC;
            }
            QToolBar {
                background: #E8E6E6;
            }
            QMenuBar {
                background: #EDEDED;
            }
            QMenu {
                background: #FFFFFF;
            }
            QComboBox, QLineEdit, QPushButton {
                background: #FFFFFF;
                border: 1px solid #CCCCCC;
                padding: 4px;
                border-radius: 4px;
            }
            QComboBox:hover, QLineEdit:hover, QPushButton:hover {
                border-color: #AAAAAA;
            }
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #f7f7f7, stop:1 #e0e0e0);
            }
            QPushButton:pressed {
                background: #d6d6d6;
            }
        """
        )

    def _create_dashboard_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)

        label = QLabel("Dashboard")
        label.setStyleSheet("font-size:14pt; font-weight:bold;")
        layout.addWidget(label)

        filters = QHBoxLayout()
        filters.addWidget(QLabel("Anno:"))
        self.dashboard_anno = QComboBox()
        filters.addWidget(self.dashboard_anno)

        filters.addWidget(QLabel("Mese:"))
        self.dashboard_mese = QComboBox()
        self.dashboard_mese.addItems(["Tutti", *mesi])
        filters.addWidget(self.dashboard_mese)

        self.dashboard_refresh = QPushButton("Aggiorna")
        self.dashboard_refresh.clicked.connect(self.aggiorna_dashboard)
        filters.addWidget(self.dashboard_refresh)

        filters.addStretch()
        layout.addLayout(filters)

        self.dashboard_info = QLabel("")
        layout.addWidget(self.dashboard_info)

        self.dashboard_chart_container = QVBoxLayout()
        layout.addLayout(self.dashboard_chart_container)

        self.dashboard_anno.currentIndexChanged.connect(self.aggiorna_dashboard)
        self.dashboard_mese.currentIndexChanged.connect(self.aggiorna_dashboard)
        return widget

    def _create_tab_spese_prof(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)

        label = QLabel("Spese Professionali")
        label.setStyleSheet("font-size:14pt; font-weight:bold;")
        layout.addWidget(label)

        self.prof_table = QTableView()
        layout.addWidget(self.prof_table)

        controls = QWidget()
        h_layout = QHBoxLayout(controls)
        h_layout.addWidget(QLabel("Mese:"))
        self.mese_spesa_prof = QComboBox()
        self.mese_spesa_prof.addItems(mesi)
        h_layout.addWidget(self.mese_spesa_prof)

        h_layout.addWidget(QLabel("Anno:"))
        self.anno_spesa_prof = QComboBox()
        self.anno_spesa_prof.addItems([str(y) for y in range(2024, 2031)])
        h_layout.addWidget(self.anno_spesa_prof)

        h_layout.addWidget(QLabel("Categoria:"))
        self.cat_spesa_prof = QComboBox()
        h_layout.addWidget(self.cat_spesa_prof)

        h_layout.addWidget(QLabel("Importo Lordo:"))
        self.imp_spesa_prof = QLineEdit("0")
        h_layout.addWidget(self.imp_spesa_prof)

        h_layout.addWidget(QLabel("Note:"))
        self.note_spesa_prof = QLineEdit("")
        h_layout.addWidget(self.note_spesa_prof)

        btn_aggiungi = QPushButton("Aggiungi Spesa")
        btn_aggiungi.clicked.connect(self.aggiungi_spesa_prof)
        h_layout.addWidget(btn_aggiungi)

        btn_cat = QPushButton("Aggiungi Categoria")
        btn_cat.clicked.connect(self.aggiungi_categoria_prof)
        h_layout.addWidget(btn_cat)

        layout.addWidget(controls)
        return widget

    def _create_tab_spese_casa(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)

        label = QLabel("Spese Casa")
        label.setStyleSheet("font-size:14pt; font-weight:bold;")
        layout.addWidget(label)

        self.casa_table = QTableView()
        layout.addWidget(self.casa_table)

        controls = QWidget()
        h_layout = QHBoxLayout(controls)
        h_layout.addWidget(QLabel("Mese:"))
        self.mese_spesa_casa = QComboBox()
        self.mese_spesa_casa.addItems(mesi)
        h_layout.addWidget(self.mese_spesa_casa)

        h_layout.addWidget(QLabel("Anno:"))
        self.anno_spesa_casa = QComboBox()
        self.anno_spesa_casa.addItems([str(y) for y in range(2024, 2031)])
        h_layout.addWidget(self.anno_spesa_casa)

        h_layout.addWidget(QLabel("Categoria:"))
        self.cat_spesa_casa = QComboBox()
        h_layout.addWidget(self.cat_spesa_casa)

        h_layout.addWidget(QLabel("Importo Lordo:"))
        self.imp_spesa_casa = QLineEdit("0")
        h_layout.addWidget(self.imp_spesa_casa)

        h_layout.addWidget(QLabel("Note:"))
        self.note_spesa_casa = QLineEdit("")
        h_layout.addWidget(self.note_spesa_casa)

        btn_aggiungi = QPushButton("Aggiungi Spesa")
        btn_aggiungi.clicked.connect(self.aggiungi_spesa_casa)
        h_layout.addWidget(btn_aggiungi)

        btn_cat = QPushButton("Aggiungi Categoria")
        btn_cat.clicked.connect(self.aggiungi_categoria_casa)
        h_layout.addWidget(btn_cat)

        layout.addWidget(controls)
        return widget

    def _create_tab_incassi(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)

        label = QLabel("Incassi (Provvigioni)")
        label.setStyleSheet("font-size:14pt; font-weight:bold;")
        layout.addWidget(label)

        self.inc_table = QTableView()
        layout.addWidget(self.inc_table)

        controls = QWidget()
        h_layout = QHBoxLayout(controls)
        h_layout.addWidget(QLabel("Mese:"))
        self.mese_inc = QComboBox()
        self.mese_inc.addItems(mesi)
        h_layout.addWidget(self.mese_inc)

        h_layout.addWidget(QLabel("Anno:"))
        self.anno_inc = QComboBox()
        self.anno_inc.addItems([str(y) for y in range(2024, 2031)])
        h_layout.addWidget(self.anno_inc)

        h_layout.addWidget(QLabel("Provvigione:"))
        self.imp_incasso = QLineEdit("0")
        h_layout.addWidget(self.imp_incasso)

        btn_incasso = QPushButton("Aggiungi Incasso")
        btn_incasso.clicked.connect(self.aggiungi_incasso)
        h_layout.addWidget(btn_incasso)

        layout.addWidget(controls)
        return widget

    def _create_table_tab(self, titolo: str) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        label = QLabel(titolo)
        label.setStyleSheet("font-size:14pt; font-weight:bold;")
        layout.addWidget(label)
        table_view = QTableView()
        layout.addWidget(table_view)
        return widget

    # Data binding ------------------------------------------------------------------

    def _bind_models(self) -> None:
        self._refresh_category_combos()
        self.aggiorna_tabella_con_df(self.prof_table, self.prof_df, is_prof=True)
        self.aggiorna_tabella_con_df(self.casa_table, self.casa_df)
        self.aggiorna_tabella_con_df(self.inc_table, self.incassi_df)
        self._refresh_dashboard_filters()

    def aggiorna_tabella_con_df(self, table_view: QTableView, df: pd.DataFrame, *, is_prof: bool = False) -> None:
        model = PandasModel(df, self.categorie_prof_df, is_prof=is_prof)
        model.dataChanged.connect(self.ricalcola_totale)
        table_view.setModel(model)
        self._configure_table(table_view)

    def _configure_table(self, table_view: QTableView) -> None:
        table_view.setAlternatingRowColors(True)
        table_view.setSelectionBehavior(QTableView.SelectRows)
        table_view.setSortingEnabled(True)
        table_view.verticalHeader().setVisible(False)
        header = table_view.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeToContents)
        header.setStretchLastSection(True)

    def _refresh_category_combos(self) -> None:
        categorie_prof = self.categorie_prof_df["Categoria"].tolist()
        categorie_casa = self.categorie_casa_df["Categoria"].tolist()
        self._populate_combo(self.cat_spesa_prof, categorie_prof)
        self._populate_combo(self.cat_spesa_casa, categorie_casa)

    def _refresh_dashboard_filters(self) -> None:
        anni = set(self.incassi_df["Anno"].tolist()) if not self.incassi_df.empty else {2024}
        anni_list = sorted(anni)
        self._populate_combo(self.dashboard_anno, [str(a) for a in anni_list])

    @staticmethod
    def _populate_combo(combo: QComboBox, values: Iterable[str]) -> None:
        combo.blockSignals(True)
        combo.clear()
        combo.addItems(list(values))
        combo.blockSignals(False)

    # Actions -----------------------------------------------------------------------

    def carica_dati(self) -> None:
        data, loaded = self.data_repo.load_with_dialog(self)
        if not loaded:
            return
        self.finance = inizializza_dataset_se_vuoto(data)
        self._bind_models()
        self.ricalcola_totale()

    def salva_dati(self) -> None:
        self.data_repo.save_with_dialog(self, self.finance)

    def aggiungi_categoria_prof(self) -> None:
        dialog = AddCategoryDialog(self)
        if dialog.exec() == QDialog.Accepted:
            nome, iva, deduc, detra = dialog.getData()
            new_row = {
                "Categoria": nome,
                "IVA %": iva,
                "Deducibilità %": deduc,
                "Detraibilità IVA %": detra,
            }
            self.categorie_prof_df = pd.concat([
                self.categorie_prof_df,
                pd.DataFrame([new_row]),
            ], ignore_index=True)
            self._refresh_category_combos()
            QMessageBox.information(self, "Info", "Categoria aggiunta con successo!")

    def aggiungi_categoria_casa(self) -> None:
        dialog = AddCategoryDialog(self)
        if dialog.exec() == QDialog.Accepted:
            nome, iva, deduc, detra = dialog.getData()
            new_row = {
                "Categoria": nome,
                "IVA %": iva,
                "Deducibilità %": deduc,
                "Detraibilità IVA %": detra,
            }
            self.categorie_casa_df = pd.concat([
                self.categorie_casa_df,
                pd.DataFrame([new_row]),
            ], ignore_index=True)
            self._refresh_category_combos()
            QMessageBox.information(self, "Info", "Categoria aggiunta con successo!")

    def aggiungi_spesa_prof(self) -> None:
        mese = self.mese_spesa_prof.currentText()
        anno = int(self.anno_spesa_prof.currentText())
        cat = self.cat_spesa_prof.currentText()
        note = self.note_spesa_prof.text()
        try:
            imp = float(self.imp_spesa_prof.text())
        except ValueError:
            QMessageBox.warning(self, "Errore", "Inserisci un valore numerico valido per l'importo")
            return

        row = self.categorie_prof_df[self.categorie_prof_df["Categoria"] == cat]
        if row.empty:
            QMessageBox.warning(self, "Errore", "Categoria non trovata")
            return
        iva_perc = row["IVA %"].values[0]
        deduc_perc = row["Deducibilità %"].values[0]
        detra_perc = row["Detraibilità IVA %"].values[0]

        iva_scorp, iva_det, imp_ded = calcola_valori(imp, iva_perc, deduc_perc, detra_perc)
        self.prof_df.loc[len(self.prof_df)] = [False, data_oggi(), mese, anno, cat, imp, iva_scorp, iva_det, imp_ded, note]
        self.aggiorna_tabella_con_df(self.prof_table, self.prof_df, is_prof=True)
        self.ricalcola_totale()

    def aggiungi_spesa_casa(self) -> None:
        mese = self.mese_spesa_casa.currentText()
        anno = int(self.anno_spesa_casa.currentText())
        cat = self.cat_spesa_casa.currentText()
        note = self.note_spesa_casa.text()
        try:
            imp = float(self.imp_spesa_casa.text())
        except ValueError:
            QMessageBox.warning(self, "Errore", "Inserisci un valore numerico")
            return

        self.casa_df.loc[len(self.casa_df)] = [False, data_oggi(), mese, anno, cat, imp, note]
        self.aggiorna_tabella_con_df(self.casa_table, self.casa_df)
        self.ricalcola_totale()

    def aggiungi_incasso(self) -> None:
        mese = self.mese_inc.currentText()
        anno = int(self.anno_inc.currentText())
        try:
            base = float(self.imp_incasso.text())
        except ValueError:
            QMessageBox.warning(self, "Errore", "Inserisci un valore numerico")
            return

        if base <= 0:
            QMessageBox.warning(self, "Errore", "Inserisci un importo maggiore di zero")
            return

        dettagli_incasso = calcola_incasso_dettagli(base)

        self.incassi_df.loc[len(self.incassi_df)] = [
            False,
            data_oggi(),
            mese,
            anno,
            base,
            dettagli_incasso["IVA"],
            dettagli_incasso["Ritenuta"],
            dettagli_incasso["Enasarco"],
            dettagli_incasso["Bonifico Finale"],
        ]
        self.aggiorna_tabella_con_df(self.inc_table, self.incassi_df)
        self._refresh_dashboard_filters()
        self.ricalcola_totale()

    def elimina_voce(self) -> None:
        current_tab_text = self.tabs.tabText(self.tabs.currentIndex())
        if current_tab_text == "Spese Professionali":
            df = self.prof_df
            table = self.prof_table
            is_prof = True
        elif current_tab_text == "Spese Casa":
            df = self.casa_df
            table = self.casa_table
            is_prof = False
        elif current_tab_text == "Incassi Mensili":
            df = self.incassi_df
            table = self.inc_table
            is_prof = False
        else:
            QMessageBox.warning(self, "Avviso", "Seleziona una tab Spese o Incassi per eliminare voci.")
            return

        df.drop(df[df["Seleziona"] == True].index, inplace=True)  # noqa: E712
        df.reset_index(drop=True, inplace=True)
        self.aggiorna_tabella_con_df(table, df, is_prof=is_prof)
        self.ricalcola_totale()
        QMessageBox.information(self, "Info", "Voci eliminate con successo.")

    # Recalculation -----------------------------------------------------------------

    def ricalcola_totale(self) -> None:
        if not self.incassi_df.empty:
            ricalcola_enasarco_con_massimale(self.incassi_df)

        p_df = self.prof_df.drop(columns="Seleziona", errors="ignore")
        c_df = self.casa_df.drop(columns="Seleziona", errors="ignore")
        i_df = self.incassi_df.drop(columns="Seleziona", errors="ignore")

        self.riepilogo_df = ricalcola_riepilogo(p_df, c_df, i_df)
        self.previsione_df = ricalcola_previsione(self.riepilogo_df, p_df, i_df)

        riepilogo_table = self.riepilogo_tab.findChild(QTableView)
        if riepilogo_table is not None:
            riepilogo_table.setModel(PandasModel(self.riepilogo_df))

        previsione_table = self.previsione_tab.findChild(QTableView)
        if previsione_table is not None:
            previsione_table.setModel(PandasModel(self.previsione_df))

        self.aggiorna_dashboard()
        if not self.riepilogo_df.empty:
            bonifico = self._format_currency(self.riepilogo_df.loc[0, "Bonifico Ricevuto"])
            spese = self._format_currency(self.riepilogo_df.loc[0, "Totale Spese"])
            liquidita = self._format_currency(self.riepilogo_df.loc[0, "Liquidità Residua"])
            self.statusBar().showMessage(
                f"Ricalcolo completato • Incassi: {bonifico} • Spese: {spese} • Liquidità: {liquidita}"
            )
        else:
            self.statusBar().showMessage("Ricalcolo completato")

    def aggiorna_dashboard(self) -> None:
        if self.dashboard_anno.count() == 0:
            self._refresh_dashboard_filters()
        try:
            anno = int(self.dashboard_anno.currentText())
        except ValueError:
            anno = 2024
        mese = self.dashboard_mese.currentText()

        p_df = self.prof_df.drop(columns="Seleziona", errors="ignore").copy()
        c_df = self.casa_df.drop(columns="Seleziona", errors="ignore").copy()
        i_df = self.incassi_df.drop(columns="Seleziona", errors="ignore").copy()

        render_dashboard(
            self.dashboard_chart_container,
            self.dashboard_info,
            p_df,
            c_df,
            i_df,
            anno,
            mese,
        )

    def _format_currency(self, value: float) -> str:
        return self._locale.toCurrencyString(float(value), "€")


if __name__ == "__main__":
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec()
