from PySide6.QtWidgets import (QDialog, QFormLayout, QLineEdit, QDialogButtonBox,
                               QMessageBox)

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
