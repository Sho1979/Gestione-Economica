import os
import pandas as pd

def carica_dati(default_data_dir, prof_table=None, prof_df=None, casa_df=None, incassi_df=None, categorie_prof_df=None, categorie_casa_df=None):
    prof_path = os.path.join(default_data_dir,"prof_spese.csv")
    casa_path = os.path.join(default_data_dir,"casa_spese.csv")
    inc_path = os.path.join(default_data_dir,"incassi.csv")
    prof_cat_path = os.path.join(default_data_dir,"categorie_prof.csv")
    casa_cat_path = os.path.join(default_data_dir,"categorie_casa.csv")

    loaded = False
    new_prof_df = prof_df.copy()
    new_casa_df = casa_df.copy()
    new_incassi_df = incassi_df.copy()
    new_categorie_prof_df = categorie_prof_df.copy()
    new_categorie_casa_df = categorie_casa_df.copy()

    if os.path.exists(prof_path):
        new_prof_df = pd.read_csv(prof_path)
        loaded = True
    if os.path.exists(casa_path):
        new_casa_df = pd.read_csv(casa_path)
        loaded = True
    if os.path.exists(inc_path):
        new_incassi_df = pd.read_csv(inc_path)
        loaded = True
    if os.path.exists(prof_cat_path):
        new_categorie_prof_df = pd.read_csv(prof_cat_path)
    if os.path.exists(casa_cat_path):
        new_categorie_casa_df = pd.read_csv(casa_cat_path)

    return loaded, new_prof_df, new_casa_df, new_incassi_df, new_categorie_prof_df, new_categorie_casa_df

def carica_dati_manual(parent, prof_df, casa_df, incassi_df, categorie_prof_df, categorie_casa_df):
    dir_name = QFileDialog.getExistingDirectory(parent, "Seleziona Cartella per Caricare")
    if dir_name:
        loaded = False
        prof_path = os.path.join(dir_name,"prof_spese.csv")
        casa_path = os.path.join(dir_name,"casa_spese.csv")
        inc_path = os.path.join(dir_name,"incassi.csv")
        prof_cat_path = os.path.join(dir_name,"categorie_prof.csv")
        casa_cat_path = os.path.join(dir_name,"categorie_casa.csv")

        new_prof_df = prof_df.copy()
        new_casa_df = casa_df.copy()
        new_incassi_df = incassi_df.copy()
        new_categorie_prof_df = categorie_prof_df.copy()
        new_categorie_casa_df = categorie_casa_df.copy()

        if os.path.exists(prof_path):
            new_prof_df = pd.read_csv(prof_path)
            loaded = True
        if os.path.exists(casa_path):
            new_casa_df = pd.read_csv(casa_path)
            loaded = True
        if os.path.exists(inc_path):
            new_incassi_df = pd.read_csv(inc_path)
            loaded = True
        if os.path.exists(prof_cat_path):
            new_categorie_prof_df = pd.read_csv(prof_cat_path)
        if os.path.exists(casa_cat_path):
            new_categorie_casa_df = pd.read_csv(casa_cat_path)

        if loaded:
            QMessageBox.information(parent,"Caricamento","Dati caricati con successo!")
            return new_prof_df, new_casa_df, new_incassi_df, new_categorie_prof_df, new_categorie_casa_df, True
        else:
            QMessageBox.warning(parent,"Caricamento","Nessun file trovato nella cartella selezionata.")
            return prof_df, casa_df, incassi_df, categorie_prof_df, categorie_casa_df, False
    else:
        return prof_df, casa_df, incassi_df, categorie_prof_df, categorie_casa_df, False

def salva_dati(default_data_dir, prof_df, casa_df, incassi_df, categorie_prof_df, categorie_casa_df):
    prof_df.to_csv(os.path.join(default_data_dir,"prof_spese.csv"), index=False)
    casa_df.to_csv(os.path.join(default_data_dir,"casa_spese.csv"), index=False)
    incassi_df.to_csv(os.path.join(default_data_dir,"incassi.csv"), index=False)
    categorie_prof_df.to_csv(os.path.join(default_data_dir,"categorie_prof.csv"), index=False)
    categorie_casa_df.to_csv(os.path.join(default_data_dir,"categorie_casa.csv"), index=False)

def salva_dati_manual(parent, prof_df, casa_df, incassi_df, categorie_prof_df, categorie_casa_df):
    dir_name = QFileDialog.getExistingDirectory(parent, "Seleziona Cartella per Salvare")
    if dir_name:
        prof_df.to_csv(os.path.join(dir_name,"prof_spese.csv"), index=False)
        casa_df.to_csv(os.path.join(dir_name,"casa_spese.csv"), index=False)
        incassi_df.to_csv(os.path.join(dir_name,"incassi.csv"), index=False)
        categorie_prof_df.to_csv(os.path.join(dir_name,"categorie_prof.csv"), index=False)
        categorie_casa_df.to_csv(os.path.join(dir_name,"categorie_casa.csv"), index=False)
        QMessageBox.information(parent,"Salvataggio",f"Dati salvati con successo in {dir_name}!")

def reset_dati(prof_df, casa_df, incassi_df, categorie_prof_df, categorie_casa_df):
    prof_df = pd.DataFrame(columns=["Seleziona","Data","Mese","Anno","Categoria","Importo Lordo","IVA","IVA Detraibile","Importo Deducibile","Note"])
    casa_df = pd.DataFrame(columns=["Seleziona","Data","Mese","Anno","Categoria","Importo Lordo","Note"])
    incassi_df = pd.DataFrame(columns=["Seleziona","Data","Mese","Anno","Base Provvigione","IVA","Ritenuta","Enasarco","Bonifico Finale"])
    from data.templates import voci_professionali_template, voci_casa_template
    categorie_prof_df = pd.DataFrame(voci_professionali_template)
    categorie_casa_df = pd.DataFrame(voci_casa_template)

    QMessageBox.information(None,"Reset","Tutti i dati sono stati azzerati.")
    return prof_df, casa_df, incassi_df, categorie_prof_df, categorie_casa_df
