from PySide6.QtGui import QPixmap


class QImage:
    def __init__(self, pixmap: QPixmap):
        self.pixmap = pixmap
        self.aspect_ratio = pixmap.width() / pixmap.height()

    def get_scaled_width(self, height: int):
        return int(self.aspect_ratio * height)

    def scale(self, height: int):
        width = self.get_scaled_width(height)
        if self.pixmap.height() != height or self.pixmap.width() != width:
            return self.pixmap.scaled(width, height)
        return self.pixmap
