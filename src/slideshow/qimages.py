from typing import Self

from PySide6.QtCore import QPoint, QRect, QSize
from PySide6.QtGui import QPixmap

from slideshow.qimage import QImage


class QImages:
    images: list[QImage]

    def __init__(self, images: list[QImage] | None = None):
        self.images = images or []

    def __iter__(self):
        return self.images.__iter__()

    @property
    def aspect_ratio(self) -> float:
        return sum(i.aspect_ratio for i in self.images)

    def add(self, image: QImage) -> Self:
        self.images.append(image)
        return self

    def copy(self) -> "QImages":
        return QImages(self.images.copy())

    def get_empty_area(self, bounds: QSize) -> int:
        width, height = self.get_size(bounds)
        return (bounds.width() * bounds.height()) - (width * height)

    def get_height(self, bounds: QSize) -> int:
        max_height = bounds.height()
        max_width = self.get_scaled_width(max_height)

        if max_width:
            ratio = bounds.width() / max_width
            if ratio < 1:
                return int(ratio * max_height)

        return max_height

    def get_rect(self, bounds: QSize) -> QRect:
        width, height = self.get_size(bounds)
        left = int((bounds.width() - width) / 2)
        top = int((bounds.height() - height) / 2)
        return QRect(QPoint(left, top), QPoint(width, height))

    def get_scaled_pixmaps(self, bounds: QSize) -> list[QPixmap]:
        pixmaps = []
        height = self.get_height(bounds)

        for image in self.images:
            pixmaps.append(image.scale(height))

        return pixmaps

    def get_scaled_width(self, height: int) -> int:
        return sum(i.get_scaled_width(height) for i in self.images)

    def get_size(self, bounds: QSize) -> tuple[int, int]:
        height = self.get_height(bounds)
        width = self.get_scaled_width(height)
        return width, height
