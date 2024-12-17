import sys  
import pandas as pd
from datetime import datetime
import os

from PySide6.QtWidgets import (QApplication, QMainWindow, QTabWidget, QWidget, 
                               QVBoxLayout, QToolBar, QFileDialog, QTableView, 
                               QMessageBox, QStatusBar, QLabel, QHBoxLayout, QLineEdit, 
                               QComboBox, QPushButton, QMenuBar, QDialog, QFormLayout, QDialogButtonBox)
from PySide6.QtGui import QIcon, QAction
from PySide6.QtCore import QAbstractTableModel, Qt, QModelIndex

from PySide6.QtCharts import QChartView, QChart, QPieSeries, QPieSlice, QBarSeries, QBarSet, QCategoryAxis

#######################################
# DATI E STRUTTURE BASE
#######################################

mesi = ["Gennaio","Febbraio","Marzo","Aprile","Maggio","Giugno","Luglio","Agosto","Settembre","Ottobre","Novembre","Dicembre"]

voci_professionali_template = [
    {"Categoria": "Carburante", "IVA %": 22, "Deducibilità %":0.8, "Detraibilità IVA %":0.40},
    {"Categoria": "Manutenzione Veicolo", "IVA %": 22,"Deducibilità %":1.0,"Detraibilità IVA %":1.0},
    {"Categoria": "Assicurazione Auto","IVA %": 0, "Deducibilità %":1.0,"Detraibilità IVA %":0},
    {"Categoria": "Bollo Auto","IVA %":0,"Deducibilità %":1.0,"Detraibilità IVA %":0},
    {"Categoria": "Vitto","IVA %":10,"Deducibilità %":0.75,"Detraibilità IVA %":1.0},
    {"Categoria": "Hotel","IVA %":10,"Deducibilità %":0.75,"Detraibilità IVA %":1.0},
    {"Categoria": "Consulenze","IVA %":22,"Deducibilità %":1.0,"Detraibilità IVA %":1.0},
    {"Categoria": "Sponsorizzazioni","IVA %":0,"Deducibilità %":1.0,"Detraibilità IVA %":0}
]

voci_casa_template = [
    {"Categoria": "Affitto","IVA %":0,"Deducibilità %":1.0,"Detraibilità IVA %":0},
    {"Categoria": "Spesa Alimentare","IVA %":4,"Deducibilità %":1.0,"Detraibilità IVA %":1.0},
    {"Categoria": "Manutenzione Casa","IVA %":22,"Deducibilità %":1.0,"Detraibilità IVA %":1.0},
    {"Categoria": "Mutuo","IVA %":0,"Deducibilità %":1.0,"Detraibilità IVA %":0}
]

def data_oggi():
    return datetime.now().strftime("%d/%m/%Y")

class AddCategoryDialog(QDialog):
    def __init__(self, parent=None):
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

        buttons = QDialogButtonBox(QDialogButtonBox.Ok|QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept_data)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def accept_data(self):
        nome = self.cat_name.text().strip()
        iva_txt = self.iva_field.text().strip()
        deduc_txt = self.deduc_field.text().strip()
        detra_txt = self.detra_field.text().strip()

        if not nome:
            QMessageBox.warning(self, "Errore", "Inserisci un nome per la categoria.")
            return
        if iva_txt == "":
            iva_txt = "0.0"
        if deduc_txt == "":
            deduc_txt = "0.0"
        if detra_txt == "":
            detra_txt = "0.0"

        try:
            iva = float(iva_txt)
            deduc = float(deduc_txt)
            detra = float(detra_txt)
        except ValueError:
            QMessageBox.warning(self, "Errore", "Inserisci valori numerici validi per IVA, Deducibilità e Detraibilità.")
            return

        self.nome = nome
        self.iva = iva
        self.deduc = deduc
        self.detra = detra
        self.accept()

    def getData(self):
        return self.nome, self.iva, self.deduc, self.detra

def calcola_valori(importo, iva_perc, deduc_perc, detra_iva_perc):
    iva_scorporata = importo*(iva_perc/(100+iva_perc)) if iva_perc>0 else 0
    iva_det = round(iva_scorporata*detra_iva_perc,2)
    imp_ded = round((importo - iva_scorporata)*deduc_perc,2)
    return iva_scorporata, iva_det, imp_ded

def ricalcola_riepilogo(prof_df, casa_df, incassi_df):
    if incassi_df.empty:
        return pd.DataFrame()
    anno = incassi_df["Anno"].mode()[0] if not incassi_df.empty else 2024
    bonifico_tot = incassi_df["Bonifico Finale"].sum()
    importo_prof = prof_df["Importo Lordo"].sum() if not prof_df.empty else 0
    importo_casa = casa_df["Importo Lordo"].sum() if not casa_df.empty else 0
    importo_deduc = prof_df["Importo Deducibile"].sum() if ("Importo Deducibile" in prof_df.columns and not prof_df.empty) else 0
    totale_spese = importo_prof + importo_casa
    liquidita = bonifico_tot - totale_spese
    base_imponibile_ridotta = bonifico_tot - importo_deduc

    riepilogo_data = {
        "Mese":["TUTTO L'ANNO"],
        "Anno":[anno],
        "Bonifico Ricevuto":[bonifico_tot],
        "Importo Lordo_Prof":[importo_prof],
        "Importo Lordo_Casa":[importo_casa],
        "Totale Spese":[totale_spese],
        "Liquidità Residua":[liquidita],
        "Importo Deducibile":[importo_deduc],
        "Base Imponibile Ridotta":[base_imponibile_ridotta]
    }
    return pd.DataFrame(riepilogo_data)

def ricalcola_previsione(riepilogo_df, prof_df, incassi_df):
    if riepilogo_df.empty or incassi_df.empty:
        return pd.DataFrame()
    base_provv_tot = incassi_df["Base Provvigione"].sum()
    ritenute_tot = incassi_df["Ritenuta"].sum()
    enasarco_tot = incassi_df["Enasarco"].sum()
    bonifico_tot = riepilogo_df.loc[0,"Bonifico Ricevuto"]
    importo_deducibile = riepilogo_df.loc[0,"Importo Deducibile"]
    base_imponibile_irpef = base_provv_tot - enasarco_tot - importo_deducibile
    if base_imponibile_irpef < 0:
        base_imponibile_irpef = 0.0
    iva_scorporata = bonifico_tot*(22/122) if bonifico_tot>0 else 0
    spese_iva_detraibile = prof_df["IVA Detraibile"].sum() if ("IVA Detraibile" in prof_df.columns and not prof_df.empty) else 0
    iva_net = iva_scorporata - spese_iva_detraibile
    if iva_net < 0:
        iva_net = 0.0
    contributi_inps = base_imponibile_irpef * 0.24
    contributi_inps_fissi = 3600
    diritti_camerali = 120

    def calcola_irpef(base):
        irpef=0
        r=base
        if r>75000:
            irpef+=(r-75000)*0.43
            r=75000
        if r>55000:
            irpef+=(r-55000)*0.41
            r=55000
        if r>28000:
            irpef+=(r-28000)*0.38
            r=28000
        if r>15000:
            irpef+=(r-15000)*0.27
            r=15000
        if r>0:
            irpef+=r*0.23
        return irpef

    irpef_lorda = calcola_irpef(base_imponibile_irpef)
    irpef_netta = irpef_lorda - ritenute_tot
    if irpef_netta < 0:
        irpef_netta = 0.0
    totale_tasse = irpef_netta + contributi_inps + iva_net + contributi_inps_fissi + diritti_camerali

    previsione_data = {
        "Mese":["TUTTO L'ANNO"],
        "Anno":[riepilogo_df.loc[0,"Anno"]],
        "Bonifico Ricevuto":[bonifico_tot],
        "Base Provvigione Totale":[base_provv_tot],
        "Enasarco":[enasarco_tot],
        "Ritenuta d'Acconto":[ritenute_tot],
        "Spese Deducibili":[importo_deducibile],
        "Base Imponibile IRPEF":[base_imponibile_irpef],
        "IRPEF Lorda":[irpef_lorda],
        "IRPEF Netta":[irpef_netta],
        "Contributi INPS":[contributi_inps],
        "Contributi INPS Fissi":[contributi_inps_fissi],
        "Diritti Camerali":[diritti_camerali],
        "IVA Scorporata":[iva_scorporata],
        "IVA Detraibile":[spese_iva_detraibile],
        "IVA Netta":[iva_net],
        "Totale Tasse":[totale_tasse]
    }
    return pd.DataFrame(previsione_data)

def riepilogo_mensile(prof_df, casa_df, incassi_df):
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
            if orientation == Qt.Horizontal:
                return self._df.columns[section]
            else:
                return str(self._df.index[section])
        return None

def crea_dashboard_tab(prof_df, casa_df, incassi_df, riepilogo_df):
    widget = QWidget()
    layout = QVBoxLayout(widget)
    label = QLabel("Dashboard")
    label.setStyleSheet("font-size:14pt; font-weight:bold;")
    layout.addWidget(label)
    # Lasciamo così o aggiungi eventuale logica
    return widget

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Gestione Economica Agente di Commercio")

        self.prof_df = pd.DataFrame(columns=["Seleziona","Data","Mese","Anno","Categoria","Importo Lordo","IVA","IVA Detraibile","Importo Deducibile","Note"])
        self.casa_df = pd.DataFrame(columns=["Seleziona","Data","Mese","Anno","Categoria","Importo Lordo","Note"])
        self.incassi_df = pd.DataFrame(columns=["Seleziona","Data","Mese","Anno","Base Provvigione","IVA","Ritenuta","Enasarco","Bonifico Finale"])

        self.categorie_prof_df = pd.DataFrame(voci_professionali_template)
        self.categorie_casa_df = pd.DataFrame(voci_casa_template)

        self.riepilogo_df = pd.DataFrame()
        self.previsione_df = pd.DataFrame()
        self.riepilogo_mensile_df = pd.DataFrame()

        menubar = QMenuBar(self)
        file_menu = menubar.addMenu("File")

        exit_action = QAction("Esci", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        carica_action = QAction("Carica Dati", self)
        carica_action.triggered.connect(self.carica_dati)
        file_menu.addAction(carica_action)

        salva_action = QAction("Salva Dati", self)
        salva_action.triggered.connect(self.salva_dati)
        file_menu.addAction(salva_action)

        self.setMenuBar(menubar)

        self.toolbar = QToolBar("Main Toolbar")
        self.addToolBar(self.toolbar)

        aggiorna_action = QAction("Ricalcola", self)
        aggiorna_action.setIcon(QIcon.fromTheme("view-refresh"))
        aggiorna_action.triggered.connect(self.ricalcola_totale)
        self.toolbar.addAction(aggiorna_action)

        elimina_action = QAction("Elimina Selezione", self)
        elimina_action.setIcon(QIcon.fromTheme("edit-delete"))
        elimina_action.triggered.connect(self.elimina_voce)
        self.toolbar.addAction(elimina_action)

        salva_button = QAction("Salva", self)
        salva_button.setIcon(QIcon.fromTheme("document-save"))
        salva_button.triggered.connect(self.salva_dati)
        self.toolbar.addAction(salva_button)

        self.setStatusBar(QStatusBar(self))
        self.statusBar().showMessage("Pronto")

        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        self.dashboard_tab = crea_dashboard_tab(self.prof_df.drop(columns="Seleziona"), self.casa_df.drop(columns="Seleziona"), self.incassi_df.drop(columns="Seleziona"), self.riepilogo_df)
        self.tabs.addTab(self.dashboard_tab, "Dashboard")

        self.prof_tab = self.crea_tab_spese_prof()
        self.tabs.addTab(self.prof_tab, "Spese Professionali")

        self.casa_tab = self.crea_tab_spese_casa()
        self.tabs.addTab(self.casa_tab, "Spese Casa")

        self.incassi_tab = self.crea_tab_incassi()
        self.tabs.addTab(self.incassi_tab, "Incassi Mensili")

        self.riepilogo_tab = self.crea_tabella_df(self.riepilogo_df, "Riepilogo")
        self.tabs.addTab(self.riepilogo_tab, "Riepilogo")

        self.previsione_tab = self.crea_tabella_df(self.previsione_df, "Previsione Tasse")
        self.tabs.addTab(self.previsione_tab, "Previsione Tasse")

        # Stile pastello
        self.setStyleSheet("""
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
            }
            QComboBox:hover, QLineEdit:hover, QPushButton:hover {
                border-color: #AAAAAA;
            }
        """)

    def carica_dati(self):
        dir_name = QFileDialog.getExistingDirectory(self, "Seleziona Cartella per Caricare")
        if dir_name:
            loaded = False
            prof_path = os.path.join(dir_name,"prof_spese.csv")
            casa_path = os.path.join(dir_name,"casa_spese.csv")
            inc_path = os.path.join(dir_name,"incassi.csv")
            prof_cat_path = os.path.join(dir_name,"categorie_prof.csv")
            casa_cat_path = os.path.join(dir_name,"categorie_casa.csv")

            if os.path.exists(prof_path):
                self.prof_df = pd.read_csv(prof_path)
                self.aggiorna_tabella_con_df(self.prof_table, self.prof_df, is_prof=True)
                loaded = True
            if os.path.exists(casa_path):
                self.casa_df = pd.read_csv(casa_path)
                self.aggiorna_tabella_con_df(self.casa_table, self.casa_df)
                loaded = True
            if os.path.exists(inc_path):
                self.incassi_df = pd.read_csv(inc_path)
                self.aggiorna_tabella_con_df(self.inc_table, self.incassi_df)
                loaded = True
            if os.path.exists(prof_cat_path):
                self.categorie_prof_df = pd.read_csv(prof_cat_path)
                if hasattr(self, 'cat_spesa_prof'):
                    self.cat_spesa_prof.clear()
                    self.cat_spesa_prof.addItems(self.categorie_prof_df["Categoria"].tolist())
            if os.path.exists(casa_cat_path):
                self.categorie_casa_df = pd.read_csv(casa_cat_path)
                if hasattr(self, 'cat_spesa_casa'):
                    self.cat_spesa_casa.clear()
                    self.cat_spesa_casa.addItems(self.categorie_casa_df["Categoria"].tolist())

            if loaded:
                self.ricalcola_totale()
                QMessageBox.information(self,"Caricamento","Dati caricati con successo!")
            else:
                QMessageBox.warning(self,"Caricamento","Nessun file trovato nella cartella selezionata.")

    def crea_tabella_df(self, df, titolo):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        label = QLabel(titolo)
        label.setStyleSheet("font-size:14pt; font-weight:bold;")
        layout.addWidget(label)
        table_view = QTableView()
        layout.addWidget(table_view)
        return widget

    def aggiorna_tabella_con_df(self, table_view:QTableView, df:pd.DataFrame, is_prof=False):
        model = PandasModel(df, self.categorie_prof_df, is_prof=is_prof)
        model.dataChanged.connect(self.ricalcola_totale)
        table_view.setModel(model)

    def crea_tab_spese_prof(self):
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
        self.anno_spesa_prof.addItems([str(y) for y in range(2024,2031)])
        h_layout.addWidget(self.anno_spesa_prof)

        h_layout.addWidget(QLabel("Categoria:"))
        self.cat_spesa_prof = QComboBox()
        self.cat_spesa_prof.addItems(self.categorie_prof_df["Categoria"].tolist())
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

    def crea_tab_spese_casa(self):
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
        self.anno_spesa_casa.addItems([str(y) for y in range(2024,2031)])
        h_layout.addWidget(self.anno_spesa_casa)

        h_layout.addWidget(QLabel("Categoria:"))
        self.cat_spesa_casa = QComboBox()
        self.cat_spesa_casa.addItems(self.categorie_casa_df["Categoria"].tolist())
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

    def crea_tab_incassi(self):
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
        self.anno_inc.addItems([str(y) for y in range(2024,2031)])
        h_layout.addWidget(self.anno_inc)

        h_layout.addWidget(QLabel("Provvigione:"))
        self.imp_incasso = QLineEdit("0")
        h_layout.addWidget(self.imp_incasso)

        btn_incasso = QPushButton("Aggiungi Incasso")
        btn_incasso.clicked.connect(self.aggiungi_incasso)
        h_layout.addWidget(btn_incasso)

        layout.addWidget(controls)
        return widget

    def ricalcola_totale(self):
        p_df = self.prof_df.drop(columns="Seleziona") if "Seleziona" in self.prof_df.columns else self.prof_df
        c_df = self.casa_df.drop(columns="Seleziona") if "Seleziona" in self.casa_df.columns else self.casa_df
        i_df = self.incassi_df.drop(columns="Seleziona") if "Seleziona" in self.incassi_df.columns else self.incassi_df

        riepilogo_tot = ricalcola_riepilogo(p_df, c_df, i_df)
        self.riepilogo_df = riepilogo_tot

        prev = ricalcola_previsione(riepilogo_tot,
                                    p_df if not p_df.empty else pd.DataFrame(),
                                    i_df)
        self.previsione_df = prev  # Corretta indentazione

        # Aggiorna riepilogo
        riepilogo_table = self.riepilogo_tab.findChild(QTableView)
        if riepilogo_table:
            model_riep = PandasModel(self.riepilogo_df)
            model_riep.dataChanged.connect(self.ricalcola_totale)
            riepilogo_table.setModel(model_riep)

        # Aggiorna previsione
        previsione_table = self.previsione_tab.findChild(QTableView)
        if previsione_table:
            model_prev = PandasModel(self.previsione_df)
            model_prev.dataChanged.connect(self.ricalcola_totale)
            previsione_table.setModel(model_prev)

        # Aggiorna dashboard
        dashboard_index = self.tabs.indexOf(self.dashboard_tab)
        if dashboard_index != -1:
            self.tabs.removeTab(dashboard_index)
        self.dashboard_tab = crea_dashboard_tab(p_df, c_df, i_df, self.riepilogo_df)
        self.tabs.insertTab(dashboard_index if dashboard_index!=-1 else 0, self.dashboard_tab, "Dashboard")
        self.tabs.setCurrentIndex(dashboard_index if dashboard_index!=-1 else 0)
        self.statusBar().showMessage("Ricalcolo completato")

    def elimina_voce(self):
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
            QMessageBox.warning(self,"Avviso","Seleziona una tab Spese o Incassi per eliminare voci.")
            return

        df.drop(df[df["Seleziona"]==True].index, inplace=True)
        df.reset_index(drop=True, inplace=True)
        self.aggiorna_tabella_con_df(table, df, is_prof=is_prof)
        self.ricalcola_totale()
        QMessageBox.information(self,"Info","Voci eliminate con successo.")

    def salva_dati(self):
        dir_name = QFileDialog.getExistingDirectory(self, "Seleziona Cartella per Salvare")
        if dir_name:
            self.prof_df.to_csv(os.path.join(dir_name,"prof_spese.csv"), index=False)
            self.casa_df.to_csv(os.path.join(dir_name,"casa_spese.csv"), index=False)
            self.incassi_df.to_csv(os.path.join(dir_name,"incassi.csv"), index=False)
            self.categorie_prof_df.to_csv(os.path.join(dir_name,"categorie_prof.csv"), index=False)
            self.categorie_casa_df.to_csv(os.path.join(dir_name,"categorie_casa.csv"), index=False)
            QMessageBox.information(self,"Salvataggio","Dati salvati con successo!")

    def showEvent(self, event):
        super().showEvent(event)
        self.carica_spese_per_mese_anno()

    def carica_spese_per_mese_anno(self):
        mese = "Gennaio"
        anno = 2024
        if self.prof_df.empty:
            for i, row in self.categorie_prof_df.iterrows():
                imp=0
                iva_perc = row["IVA %"]
                deduc = row["Deducibilità %"]
                detra = row["Detraibilità IVA %"]
                iva_scorp, iva_det, imp_ded = calcola_valori(imp,iva_perc,deduc,detra)
                self.prof_df.loc[len(self.prof_df)] = [False,data_oggi(), mese, anno, row["Categoria"], imp, iva_scorp, iva_det, imp_ded, ""]
            self.aggiorna_tabella_con_df(self.prof_table, self.prof_df, is_prof=True)

        if self.casa_df.empty:
            for i, row in self.categorie_casa_df.iterrows():
                imp = 0
                self.casa_df.loc[len(self.casa_df)] = [False,data_oggi(),mese,anno,row["Categoria"], imp,""]
            self.aggiorna_tabella_con_df(self.casa_table, self.casa_df)

        self.ricalcola_totale()

    def aggiungi_categoria_prof(self):
        dialog = AddCategoryDialog(self)
        if dialog.exec() == QDialog.Accepted:
            nome, iva, deduc, detra = dialog.getData()
            new_row = {"Categoria":nome,"IVA %":iva,"Deducibilità %":deduc,"Detraibilità IVA %":detra}
            self.categorie_prof_df = pd.concat([self.categorie_prof_df, pd.DataFrame([new_row])], ignore_index=True)
            self.cat_spesa_prof.clear()
            self.cat_spesa_prof.addItems(self.categorie_prof_df["Categoria"].tolist())
            QMessageBox.information(self,"Info","Categoria aggiunta con successo!")

    def aggiungi_spesa_prof(self):
        mese = self.mese_spesa_prof.currentText()
        anno = int(self.anno_spesa_prof.currentText())
        cat = self.cat_spesa_prof.currentText()
        try:
            imp = float(self.imp_spesa_prof.text())
        except ValueError:
            QMessageBox.warning(self,"Errore","Inserisci un valore numerico valido per l'importo")
            return
        note = self.note_spesa_prof.text()

        row = self.categorie_prof_df[self.categorie_prof_df["Categoria"]==cat]
        if row.empty:
            QMessageBox.warning(self,"Errore","Categoria non trovata")
            return
        iva_perc = row["IVA %"].values[0]
        deduc_perc = row["Deducibilità %"].values[0]
        detra_perc = row["Detraibilità IVA %"].values[0]

        iva_scorp, iva_det, imp_ded = calcola_valori(imp, iva_perc, deduc_perc, detra_perc)
        self.prof_df.loc[len(self.prof_df)] = [False, data_oggi(),mese,anno,cat,imp,iva_scorp,iva_det,imp_ded,note]
        self.aggiorna_tabella_con_df(self.prof_table, self.prof_df, is_prof=True)
        self.ricalcola_totale()

    def aggiungi_categoria_casa(self):
        dialog = AddCategoryDialog(self)
        if dialog.exec() == dialog.Accepted:
            nome, iva, deduc, detra = dialog.getData()
            new_row = {"Categoria":nome,"IVA %":iva,"Deducibilità %":deduc,"Detraibilità IVA %":detra}
            self.categorie_casa_df = pd.concat([self.categorie_casa_df, pd.DataFrame([new_row])], ignore_index=True)
            self.cat_spesa_casa.clear()
            self.cat_spesa_casa.addItems(self.categorie_casa_df["Categoria"].tolist())
            QMessageBox.information(self,"Info","Categoria aggiunta con successo!")

    def aggiungi_spesa_casa(self):
        mese = self.mese_spesa_casa.currentText()
        anno = int(self.anno_spesa_casa.currentText())
        cat = self.cat_spesa_casa.currentText()
        try:
            imp = float(self.imp_spesa_casa.text())
        except ValueError:
            QMessageBox.warning(self,"Errore","Inserisci un valore numerico")
            return
        note = self.note_spesa_casa.text()

        self.casa_df.loc[len(self.casa_df)] = [False, data_oggi(),mese,anno,cat,imp,note]
        self.aggiorna_tabella_con_df(self.casa_table, self.casa_df)
        self.ricalcola_totale()

    def aggiungi_incasso(self):
        mese = self.mese_inc.currentText()
        anno = int(self.anno_inc.currentText())
        try:
            base = float(self.imp_incasso.text())
        except ValueError:
            QMessageBox.warning(self,"Errore","Inserisci un valore numerico")
            return
        data_inc = data_oggi()
        iva = round(base*0.22,2)
        ritenuta = round(base*0.23*0.5,2) # aggiornato a 23% del 50%
        enasarco = round(base*0.085,2)
        bonifico = round(base+iva-ritenuta-enasarco,2)

        self.incassi_df.loc[len(self.incassi_df)] = [False, data_oggi(),mese,anno,base,iva,ritenuta,enasarco,bonifico]
        self.aggiorna_tabella_con_df(self.inc_table, self.incassi_df)
        self.ricalcola_totale()

    def elimina_voce(self):
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
            QMessageBox.warning(self,"Avviso","Seleziona una tab Spese o Incassi per eliminare voci.")
            return

        df.drop(df[df["Seleziona"]==True].index, inplace=True)
        df.reset_index(drop=True, inplace=True)
        self.aggiorna_tabella_con_df(table, df, is_prof=is_prof)
        self.ricalcola_totale()
        QMessageBox.information(self,"Info","Voci eliminate con successo.")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
