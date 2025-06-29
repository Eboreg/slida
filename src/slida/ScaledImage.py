from dataclasses import dataclass
from math import ceil, floor
from typing import Callable

import numpy as np
from PySide6.QtCore import QPointF, QRect, QSizeF, Qt
from PySide6.QtGui import QImage, QPainter


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
    size: QSizeF
    columns: int = 0
    rows: int = 0
    image: QImage
    __subs: list[SubImage] | None = None
    __cached_image: QImage | None = None
    __cached_image_no_borders: QImage | None = None

    def __init__(self, size: QSizeF, image: QImage):
        self.image = image
        self.size = size

    @property
    def subs(self) -> list[SubImage]:
        if self.__subs is not None:
            return self.__subs

        subs: list[SubImage] = []

        if self.size.width() > 0:
            self.columns = round(self.size.width() / 50)
            width = self.size.width() / self.columns
            self.rows = round(self.size.height() / width)
            height = self.size.height() / self.rows
            image = self.get_image()

            for y in range(self.rows):
                for x in range(self.columns):
                    geometry = QRect(floor(x * width), floor(y * height), ceil(width), ceil(height))
                    subs.append(SubImage(image=image.copy(geometry), geometry=geometry, row=y, column=x))

        self.__subs = subs
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

    def get_image(self, no_borders: bool = False):
        if no_borders and self.__cached_image_no_borders:
            return self.__cached_image_no_borders
        if not no_borders and self.__cached_image:
            return self.__cached_image

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

        if no_borders:
            self.__cached_image_no_borders = image
        else:
            self.__cached_image = image

        return image

    def fill_all_or_none(self, fill: bool) -> list[SubImage]:
        for sub in self.subs:
            sub.filled = fill
        return self.subs if fill else []

    def fill_from_top(self, probability: float) -> list[SubImage]:
        return self.__fill(probability, lambda s: pow(2, (self.rows - s.row - 1) / (self.rows - 1) * 50))

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
                weights = np.array([weight(s) for s in subs])
                if diff < 0:
                    weights = 1 / weights
                weight_sum = weights.sum()
                probabilities = weights / weight_sum

            try:
                for index in np.random.choice(range(len(subs)), size=abs(diff), replace=False, p=probabilities):
                    subs[index].toggle_filled()
            except Exception as e:
                print(e)
                print(probabilities)

        return self.filled_subs
