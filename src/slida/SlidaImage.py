from PySide6.QtCore import QObject
from PySide6.QtGui import QImage, QPixmap


class SlidaImage(QObject):
    # def __init__(self, image: QPixmap | QImage, filename: str = ""):
    def __init__(self, parent: QObject, filename: str = ""):
        super().__init__(parent)
        self.filename = filename
        # self.__image = QPixmap(image) if isinstance(image, QImage) else image
        self.__image = QPixmap(filename)

        if self.__image.isNull():
            raise ValueError(f"{filename} is a null pixmap")

        self.aspect_ratio = self.__image.width() / self.__image.height()

    def __repr__(self):
        return f"<SlidaImage filename={self.filename}>"

    def get_scaled_width(self, height: float) -> float:
        return self.aspect_ratio * height

    def scale(self, height: int) -> QPixmap:
        width = round(self.get_scaled_width(height))
        if self.__image.height() != height or self.__image.width() != width:
            self.__image = self.__image.scaled(width, height)

        return self.__image
