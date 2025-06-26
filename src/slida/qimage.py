from PySide6.QtGui import QPixmap


class QImage:
    def __init__(self, filename: str):
        self.filename = filename
        self.pixmap = QPixmap(filename)
        try:
            self.aspect_ratio = self.pixmap.width() / self.pixmap.height()
        except ZeroDivisionError:
            self.aspect_ratio = 1.0

    def get_scaled_width(self, height: float) -> int:
        return int(self.aspect_ratio * height)

    def scale(self, height: int) -> QPixmap:
        width = self.get_scaled_width(height)
        if self.pixmap.height() != height or self.pixmap.width() != width:
            return self.pixmap.scaled(width, height)
        return self.pixmap
