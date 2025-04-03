from PySide6.QtCore import QPropertyAnimation
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import QWidget

from pyside.pixmaplist import PixmapList


class PixmapWidget(QWidget):
    def __init__(self, pixmaps: PixmapList, parent: QWidget):
        super().__init__(parent)
        self.pixmaps = pixmaps

    def paintEvent(self, event):
        with QPainter(self) as painter:
            anim = QPropertyAnimation(self, b"windowOpacity")
            anim.setDuration(1_000)
            anim.setStartValue(1.0)
            anim.setEndValue(0.0)
            anim.start()
            self.pixmaps.draw(painter)
