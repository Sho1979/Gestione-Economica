import pandas as pd

#######################################
# COSTANTI E FUNZIONI DI CALCOLO
#######################################

MASSIMALE_ENASARCO = 44727.0
ALIQUOTA_ENASARCO = 0.085

def calcola_valori(importo, iva_perc, deduc_perc, detra_iva_perc):
    # Funzione presente nel tuo codice originale
    iva_scorporata = importo*(iva_perc/(100+iva_perc)) if iva_perc>0 else 0
    iva_det = round(iva_scorporata*detra_iva_perc,2)
    imp_ded = round((importo - iva_scorporata)*deduc_perc,2)
    return iva_scorporata, iva_det, imp_ded

def ricalcola_riepilogo(prof_df, casa_df, incassi_df):
    # Funzione presente nel tuo codice originale
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
    # Funzione presente nel tuo codice originale
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

    # Calcolo IVA netta
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
    enasarco_cumulato = 0.0
    for anno in incassi_df["Anno"].unique():
        df_anno = incassi_df[incassi_df["Anno"] == anno].copy()
        df_anno.sort_values("mese_order", inplace=True)
        for idx, row in df_anno.iterrows():
            base = row["Base Provvigione"]
            iva = row["IVA"]
            ritenuta = row["Ritenuta"]
            enas_calcolato = base * ALIQUOTA_ENASARCO
            spazio = MASSIMALE_ENASARCO - enasarco_cumulato
            if spazio <= 0:
                enas_finale = 0.0
                bonifico = round(base + iva - ritenuta, 2)
            else:
                enas_finale = min(enas_calcolato, spazio)
                if enas_finale > 0:
                    bonifico = round(base + iva - ritenuta - enas_finale, 2)
                else:
                    bonifico = round(base + iva - ritenuta, 2)
            incassi_df.at[idx, "Enasarco"] = round(enasarco_finale, 2)
            incassi_df.at[idx, "Bonifico Finale"] = bonifico
            enasarco_cumulato += enas_finale
    incassi_df.drop("mese_order", axis=1, inplace=True)
