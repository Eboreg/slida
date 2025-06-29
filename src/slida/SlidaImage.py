from PySide6.QtGui import QImage, QPixmap


class SlidaImage:
    def __init__(self, image: QPixmap | QImage, filename: str = ""):
        self.filename = filename
        self.__image = QPixmap(image) if isinstance(image, QImage) else image

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
