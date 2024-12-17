# gui/chat_delegate.py
from PySide6.QtWidgets import QStyledItemDelegate, QStyleOptionViewItem, QApplication
from PySide6.QtGui import QPainter, QColor, QPixmap
from PySide6.QtCore import QRect, Qt

class ChatDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)

    def paint(self, painter:QPainter, option:QStyleOptionViewItem, index):
        data = index.data(Qt.DisplayRole)
        if not data:
            return
        # data nel formato: ("ruolo", "testo")
        # ruolo: "utente" o "assistente"
        # testo: stringa
        ruolo, testo = data

        rect = option.rect
        painter.save()

        # Impostazioni base
        padding = 10
        avatar_size = 32
        max_width = rect.width()*0.7

        font = option.font
        painter.setFont(font)
        metrics = painter.fontMetrics()
        text_width = metrics.boundingRect(0,0,int(max_width),10000,Qt.TextWordWrap, testo).width()
        text_height = metrics.boundingRect(0,0,int(max_width),10000,Qt.TextWordWrap, testo).height()

        balloon_width = text_width + padding*2
        balloon_height = text_height + padding*2

        # Avatar
        if ruolo == "utente":
            # Utente a destra
            balloon_x = rect.right() - balloon_width - avatar_size - padding*2
            balloon_y = rect.y() + padding
            avatar_x = rect.right() - avatar_size - padding
            avatar_y = balloon_y
            balloon_color = QColor("#D0ECFF")
            align = Qt.AlignLeft | Qt.TextWordWrap
            text_x = balloon_x + padding
            text_y = balloon_y + padding
            avatar_pix = QPixmap("resources/user.png")
        else:
            # Assistente a sinistra
            balloon_x = rect.x() + avatar_size + padding*2
            balloon_y = rect.y() + padding
            avatar_x = rect.x() + padding
            avatar_y = balloon_y
            balloon_color = QColor("#D1F2C7")
            align = Qt.AlignLeft | Qt.TextWordWrap
            text_x = balloon_x + padding
            text_y = balloon_y + padding
            avatar_pix = QPixmap("resources/assistant.png")

        # Disegno avatar
        if not avatar_pix.isNull():
            painter.drawPixmap(QRect(avatar_x, avatar_y, avatar_size, avatar_size), avatar_pix.scaled(avatar_size, avatar_size, Qt.KeepAspectRatio, Qt.SmoothTransformation))

        # Disegno balloon
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setBrush(balloon_color)
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(balloon_x, balloon_y, balloon_width, balloon_height, 10, 10)

        # Disegno testo
        painter.setPen(Qt.black)
        painter.drawText(QRect(text_x, text_y, text_width, text_height), align, testo)

        painter.restore()

    def sizeHint(self, option, index):
        data = index.data(Qt.DisplayRole)
        if data:
            ruolo, testo = data
            metrics = option.fontMetrics
            max_width = option.rect.width()*0.7
            text_rect = metrics.boundingRect(0,0,int(max_width),10000,Qt.TextWordWrap,testo)
            height = text_rect.height() + 20 # padding
            height = max(height, 52) # almeno altezza avatar
            return text_rect.size().expandedTo(QRect(0,0,text_rect.width(),height).size())
        return super().sizeHint(option, index)
