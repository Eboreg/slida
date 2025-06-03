from PySide6.QtCore import QTimer, Slot, Qt
from PySide6.QtWidgets import QDockWidget, QLabel
from PySide6.QtGui import QPalette


class Toast(QDockWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.setMinimumHeight(30)
        self.setFeatures(QDockWidget.DockWidgetFeature.NoDockWidgetFeatures)
        self.setBackgroundRole(QPalette.ColorRole.Accent)
        self.setAutoFillBackground(True)
        self.label = QLabel(self)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.hide()
        self.timer = QTimer(self, singleShot=True, interval=3000)
        self.timer.timeout.connect(self.on_timeout)

    def set_text(self, text: str):
        self.label.setText(text)
        self.show()
        self.timer.start()
        # QTimer.singleShot(3_000, self.on_timeout)

    @Slot()
    def on_timeout(self):
        self.hide()

    def resizeEvent(self, event):
        self.label.setFixedSize(self.size())
        return super().resizeEvent(event)
