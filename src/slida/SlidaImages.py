from dataclasses import dataclass
from math import ceil, floor
from typing import Callable, Self

import numpy as np
from PySide6.QtCore import QPointF, QRect, QRectF, QSizeF, Qt
from PySide6.QtGui import QImage, QPainter, QPixmap

from slida.SlidaImage import SlidaImage


@dataclass
class SubImage:
    image: QImage
    geometry: QRect
    row: int
    column: int
    filled: bool = False

    def toggle_filled(self):
        self.filled = not self.filled


class ScaledImage:
    image: QImage
    size: QSizeF
    columns: int = 0
    rows: int = 0
    _subs: list[SubImage] | None = None

    def __init__(self, image: QImage, size: QSizeF):
        self.image = image
        self.size = size

    @property
    def subs(self) -> list[SubImage]:
        if self._subs is not None:
            return self._subs

        subs: list[SubImage] = []

        if self.size.width() > 0:
            self.columns = round(self.size.width() / 50)
            width = self.size.width() / self.columns
            self.rows = round(self.size.height() / width)
            height = self.size.height() / self.rows

            for y in range(self.rows):
                for x in range(self.columns):
                    geometry = QRect(floor(x * width), floor(y * height), ceil(width), ceil(height))
                    subs.append(SubImage(image=self.image.copy(geometry), geometry=geometry, row=y, column=x))

        self._subs = subs
        return subs

    @property
    def filled_subs(self) -> list[SubImage]:
        return [s for s in self.subs if s.filled]

    @property
    def unfilled_subs(self) -> list[SubImage]:
        return [s for s in self.subs if not s.filled]

    def diff(self, probability: float):
        filled_before = len(self.filled_subs)
        filled_after = round(len(self.subs) * probability)
        return filled_after - filled_before

    def fill_all_or_none(self, fill: bool) -> list[SubImage]:
        for sub in self.subs:
            sub.filled = fill
        return self.subs if fill else []

    def fill_from_top(self, probability: float) -> list[SubImage]:
        return self.__fill(probability, lambda s: pow(2, (self.rows - s.row - 1) / (self.rows - 1) * 50))
        # return self.__fill(probability, lambda s: pow((self.rows - s.row) * 0.1, self.rows - s.row))

    def fill_from_top_left(self, probability: float) -> list[SubImage]:
        return self.__fill(
            probability,
            lambda s: pow(2, (self.rows + self.columns - s.row - s.column - 2) / (self.rows + self.columns - 2) * 50),
        )

    def fill_randomly(self, probability: float) -> list[SubImage]:
        return self.__fill(probability)

    def __fill(self, probability: float, weight: Callable[[SubImage], float] | None = None):
        if probability in (0.0, 1.0):
            return self.fill_all_or_none(bool(probability))

        diff = self.diff(probability)

        if diff != 0:
            weights = None
            probabilities = None
            subs = self.unfilled_subs if diff > 0 else self.filled_subs

            if weight:
                # weights = [weight(s) for s in subs]
                weights = np.array([weight(s) for s in subs])
                if diff < 0:
                    weights = 1 / weights
                    # weights = [1 / w for w in weights]
                # weight_sum = sum(weights)
                weight_sum = weights.sum()
                probabilities = weights / weight_sum
                # probabilities = [w / weight_sum for w in weights]

            try:
                for index in np.random.choice(range(len(subs)), size=abs(diff), replace=False, p=probabilities):
                    subs[index].toggle_filled()
            except Exception as e:
                print(e)
                print(probabilities)

        return self.filled_subs


class SlidaImages:
    images: list[SlidaImage]
    __cache: ScaledImage | None = None

    def __init__(self, images: list[SlidaImage] | None = None):
        self.images = images or []

    def __iter__(self):
        return self.images.__iter__()

    def __repr__(self):
        return f"<SlidaImages images={self.images}>"

    @property
    def aspect_ratio(self) -> float:
        return sum(i.aspect_ratio for i in self.images)

    def add(self, image: SlidaImage) -> Self:
        self.images.append(image)
        self.__cache = None
        return self

    def copy(self) -> "SlidaImages":
        return SlidaImages(self.images.copy())

    def get_empty_area(self, bounds: QSizeF) -> float:
        width, height = self.get_size(bounds)
        return (bounds.width() * bounds.height()) - (width * height)

    def get_scaled_image(self, bounds: QSizeF) -> ScaledImage:
        if self.__cache and self.__cache.size == bounds:
            return self.__cache

        rect = self.__get_rect(bounds)
        image = QImage(bounds.toSize(), QImage.Format.Format_ARGB32)
        image.fill(Qt.GlobalColor.black)
        painter = QPainter(image)
        left = rect.left()

        for pixmap in self.__get_scaled_pixmaps(bounds):
            painter.drawPixmap(QPointF(left, rect.top()), pixmap)
            left += pixmap.width()

        painter.end()

        scaled_image = ScaledImage(image=image, size=bounds)
        self.__cache = scaled_image

        return scaled_image

    def get_size(self, bounds: QSizeF) -> tuple[float, float]:
        height = self.__get_height(bounds)
        width = self.__get_scaled_width(height)
        return width, height

    def __get_height(self, bounds: QSizeF) -> float:
        max_height = bounds.height()
        max_width = self.__get_scaled_width(max_height)

        if max_width:
            ratio = bounds.width() / max_width
            if ratio < 1:
                return ratio * max_height

        return max_height

    def __get_rect(self, bounds: QSizeF) -> QRectF:
        width, height = self.get_size(bounds)
        left = (bounds.width() - width) / 2
        top = (bounds.height() - height) / 2
        return QRectF(QPointF(left, top), QPointF(width, height))

    def __get_scaled_pixmaps(self, bounds: QSizeF) -> list[QPixmap | QImage]:
        pixmaps = []
        height = self.__get_height(bounds)

        for image in self.images:
            pixmaps.append(image.scale(int(height)))

        return pixmaps

    def __get_scaled_width(self, height: float) -> float:
        return sum(i.get_scaled_width(height) for i in self.images)
