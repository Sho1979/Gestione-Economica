from datetime import datetime

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

