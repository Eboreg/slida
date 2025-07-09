from PyQt6.QtCore import QSize, Qt, QTimer, pyqtSlot, pyqtSignal
from PyQt6.QtGui import QPalette
from PyQt6.QtWidgets import QDockWidget, QLabel


class Toast(QDockWidget):
    hidden = pyqtSignal()
    resized = pyqtSignal(QSize)
    shown = pyqtSignal()

    def __init__(self, parent, timeout: int | None = 3000, background: QPalette.ColorRole = QPalette.ColorRole.Accent):
        super().__init__(parent)
        self.setMinimumHeight(30)
        self.setFeatures(QDockWidget.DockWidgetFeature.NoDockWidgetFeatures)
        self.label = QLabel(self)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setBackgroundRole(background)
        self.label.setAutoFillBackground(True)
        self.label.setMinimumHeight(30)
        self.timeout = timeout
        super().hide()

        if self.timeout:
            self.timer = QTimer(self, singleShot=True, interval=self.timeout)
            self.timer.timeout.connect(self.on_timeout)

    def hide(self):
        super().hide()
        self.hidden.emit()

    def show(self):
        super().show()
        if self.timeout:
            self.timer.start()
        self.shown.emit()

    def set_text(self, text: str):
        rows = text.split("\n")
        self.setMinimumHeight(20 + (10 * len(rows)))
        self.label.setMinimumHeight(20 + (10 * len(rows)))
        self.label.setText(text)

    @pyqtSlot()
    def on_timeout(self):
        self.hide()

    def resizeEvent(self, event):
        self.label.setFixedWidth(self.width())
        self.resized.emit(self.size())
        return super().resizeEvent(event)
