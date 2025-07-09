from PyQt6.QtCore import QPointF, QSizeF, Qt
from PyQt6.QtGui import QImage, QPainter


class ScaledImage:
    size: QSizeF
    columns: int = 0
    rows: int = 0
    image: QImage
    # __cached_image: QImage | None = None
    # __cached_image_no_borders: QImage | None = None

    def __init__(self, size: QSizeF, image: QImage):
        self.image = image
        self.size = size

    def get_image(self, no_borders: bool = False):
        # if no_borders and self.__cached_image_no_borders:
        #     return self.__cached_image_no_borders
        # if not no_borders and self.__cached_image:
        #     return self.__cached_image

        image = QImage(self.size.toSize(), QImage.Format.Format_ARGB32)

        if no_borders:
            image.fill(Qt.GlobalColor.transparent)
        else:
            image.fill(Qt.GlobalColor.black)

        painter = QPainter(image)
        left = (self.size.width() - self.image.width()) / 2
        top = (self.size.height() - self.image.height()) / 2
        painter.drawImage(QPointF(left, top), self.image)
        painter.end()

        # if no_borders:
        #     self.__cached_image_no_borders = image
        # else:
        #     self.__cached_image = image

        return image
