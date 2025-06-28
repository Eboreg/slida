from PySide6.QtCore import QSize, Qt, QTimer, Signal, Slot
from PySide6.QtGui import QPalette
from PySide6.QtWidgets import QDockWidget, QLabel


class Toast(QDockWidget):
    hidden = Signal()
    resized = Signal(QSize)
    shown = Signal()

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
        self.shown.emit()

    def set_text(self, text: str):
        self.label.setText(text)
        if self.isHidden():
            self.show()
        if self.timeout:
            self.timer.start()

    @Slot()
    def on_timeout(self):
        self.hide()

    def resizeEvent(self, event):
        self.label.setFixedWidth(self.width())
        self.resized.emit(self.size())
        return super().resizeEvent(event)
