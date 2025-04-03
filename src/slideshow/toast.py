from PySide6.QtCore import QTimer, Slot
from PySide6.QtWidgets import QLabel


class Toast(QLabel):
    def setText(self, arg__1):
        super().setText(arg__1)
        self.setWindowOpacity(1.0)
        QTimer.singleShot(5_000, self.on_timeout)

    @Slot()
    def on_timeout(self):
        self.setWindowOpacity(0.0)
