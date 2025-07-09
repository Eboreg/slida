from typing import Self

from PySide6.QtCore import QObject, QPoint, QSizeF, Qt
from PySide6.QtGui import QImage, QPainter

from slida.ScaledImage import ScaledImage
from slida.SlidaImage import SlidaImage


class SlidaImages(QObject):
    images: list[SlidaImage]
    # __cache: ScaledImage | None = None

    def __init__(self, parent: QObject, images: list[SlidaImage] | None = None):
        super().__init__(parent)
        self.images = images or []

    def __iter__(self):
        return self.images.__iter__()

    def __len__(self):
        return len(self.images)

    def __repr__(self):
        return f"<SlidaImages images={self.images}>"

    @property
    def aspect_ratio(self) -> float:
        return sum(i.aspect_ratio for i in self.images)

    def add(self, image: SlidaImage) -> Self:
        self.images.append(image)
        # self.__cache = None
        return self

    def copy(self) -> "SlidaImages":
        return SlidaImages(self.parent(), self.images.copy())

    def deleteLater(self):
        for image in self.images:
            image.deleteLater()
        super().deleteLater()

    def get_empty_area(self, bounds: QSizeF) -> float:
        size = self.get_size(bounds)
        return (bounds.width() * bounds.height()) - (size.width() * size.height())

    def get_scaled_image(self, bounds: QSizeF) -> ScaledImage:
        # if self.__cache and self.__cache.size == bounds:
        #     return self.__cache

        image = self.__get_combined_image(bounds)
        scaled_image = ScaledImage(parent=self, size=bounds, image=image)
        # self.__cache = scaled_image

        return scaled_image

    def get_size(self, bounds: QSizeF) -> QSizeF:
        height = bounds.height()
        width = sum(i.get_scaled_width(height) for i in self.images)

        if width:
            ratio = bounds.width() / width
            if ratio < 1:
                height = ratio * height
                width = sum(i.get_scaled_width(height) for i in self.images)

        return QSizeF(width, height)

    def __get_combined_image(self, bounds: QSizeF):
        size = self.get_size(bounds).toSize()
        image = QImage(size, QImage.Format.Format_ARGB32)
        image.fill(Qt.GlobalColor.black)
        painter = QPainter(image)
        left = 0

        for im in self.images:
            pm = im.scale(size.height())
            painter.drawPixmap(QPoint(left, 0), pm)
            left += pm.width()

        painter.end()
        return image
