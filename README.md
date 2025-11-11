# Gestione Economica – Guida rapida ai test

Questi comandi ti consentono di eseguire la suite di test su Windows, macOS e
Linux partendo da qualsiasi posizione del terminale.

## 1. Preparazione
Assicurati di avere Python 3.10 o superiore e installa le dipendenze minime:

```powershell
python -m pip install --upgrade pip
pip install pandas PySide6
```

> **Suggerimento Windows:** se hai estratto il progetto in una cartella come
> `C:\Users\<nome>\Desktop\progetto_gestione_economica\Gestione-Economica.git`,
> apri PowerShell e usa `cd "C:\\Users\\<nome>\\Desktop\\progetto_gestione_economica\\Gestione-Economica.git"`
> per spostarti nella cartella del repository.

## 2. Esecuzione rapida (Windows)
Dalla cartella del progetto fai doppio clic su `run_tests.bat` oppure lancia il
seguente comando da PowerShell o Prompt dei comandi:

```powershell
"C:\percorso\alla\cartella\Gestione-Economica.git\run_tests.bat"
```

Lo script cambia automaticamente directory e avvia la suite di test.

## 3. Esecuzione su qualunque piattaforma
Puoi avviare i test direttamente con Python richiamando lo script
`run_tests.py`. Anche in questo caso non importa in quale directory si trovi il
terminale:

```bash
python "C:/percorso/alla/cartella/Gestione-Economica.git/run_tests.py"
```

Il runner verifica la presenza dei pacchetti richiesti e, se mancanti, ti
mostra il comando `pip` da eseguire.

## 4. Test mirati
Per eseguire solo i test fiscali:

```bash
python -m unittest Tests.test_calculations
```

Accertati in questo caso di lanciare il comando dal root del repository oppure
usa i percorsi completi come mostrato sopra.

## 5. Avvio dell'applicazione
Terminati i test, puoi avviare l'interfaccia Qt con uno di questi metodi:

- **Windows (doppio clic o terminale):**
  ```powershell
  "C:\percorso\alla\cartella\Gestione-Economica.git\run_app.bat"
  ```
  Lo script verifica le dipendenze, si sposta nella cartella corretta e lancia l'app.

- **Qualsiasi piattaforma:**
  ```bash
  python "C:/percorso/alla/cartella/Gestione-Economica.git/run_app.py"
  ```
  Anche questo helper controlla le dipendenze (`pandas`, `PySide6`) prima di eseguire
  `main.py`.

  Se hai già aperto il terminale direttamente nella cartella del progetto puoi
  digitare semplicemente:

  ```bash
  python run_app.py
  ```
  (oppure `python main.py` se preferisci avviare lo script originale senza i
  controlli aggiuntivi).

Buon lavoro!
