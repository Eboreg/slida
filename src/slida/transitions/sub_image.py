from dataclasses import dataclass
from math import ceil, floor

from PySide6.QtCore import QAbstractAnimation, QEasingCurve, QRect, QSequentialAnimationGroup
from PySide6.QtGui import QImage, QPainter

import numpy as np
from slida.ScaledImage import ScaledImage
from slida.transitions.base import Transition


@dataclass
class SubImage:
    image: QImage
    geometry: QRect
    row: int
    column: int
    filled: bool = False

    def toggle_filled(self):
        self.filled = not self.filled


class SubImageTransition(Transition):
    __subs: list[SubImage] | None = None
    columns: int = 0
    rows: int = 0
    parent_z = 1.0

    @property
    def scaled_image(self) -> ScaledImage:
        assert self._scaled_image is not None
        return self._scaled_image

    @property
    def filled_subs(self) -> list[SubImage]:
        return [s for s in self.subs if s.filled]

    @property
    def unfilled_subs(self) -> list[SubImage]:
        return [s for s in self.subs if not s.filled]

    @property
    def subs(self) -> list[SubImage]:
        if self.__subs is not None:
            return self.__subs

        subs: list[SubImage] = []

        if self.scaled_image.size.width() > 0:
            self.columns = round(self.scaled_image.size.width() / 50)
            width = self.scaled_image.size.width() / self.columns
            self.rows = round(self.scaled_image.size.height() / width)
            height = self.scaled_image.size.height() / self.rows
            image = self.scaled_image.get_image()

            for y in range(self.rows):
                for x in range(self.columns):
                    geometry = QRect(floor(x * width), floor(y * height), ceil(width), ceil(height))
                    subs.append(SubImage(image=image.copy(geometry), geometry=geometry, row=y, column=x))

        self.__subs = subs
        return subs

    def get_filled_subs(self):
        if self._progress in (0.0, 1.0):
            for sub in self.subs:
                sub.filled = bool(self._progress)
            return self.subs if self._progress else []

        diff = self.__diff()

        if diff != 0:
            weights = None
            probabilities = None
            subs = self.unfilled_subs if diff > 0 else self.filled_subs
            weights = np.array([self.get_sub_image_weight(s) for s in subs])
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

    def get_sub_image_weight(self, s: SubImage) -> float:
        return 1.0

    def on_progress(self, value: float):
        super().on_progress(value)
        if self.__diff():
            self.parent().update(self.parent().rect())

    def paint(self, painter: QPainter, scaled_image: ScaledImage):
        self.set_scaled_image(scaled_image)
        for sub in self.get_filled_subs():
            painter.drawImage(sub.geometry, sub.image)

    def __diff(self):
        filled_before = len(self.filled_subs)
        filled_after = round(len(self.subs) * self._progress)
        return filled_after - filled_before


class RandomSquaresIn(SubImageTransition):
    easing = QEasingCurve.Type.InCubic


class TopLeftSquaresIn(SubImageTransition):
    def get_sub_image_weight(self, s: SubImage) -> float:
        return pow(2, (self.rows + self.columns - s.row - s.column - 2) / (self.rows + self.columns - 2) * 50)


class TopSquaresIn(SubImageTransition):
    def get_sub_image_weight(self, s: SubImage) -> float:
        return pow(2, (self.rows - s.row - 1) / (self.rows - 1) * 50)


class Fucker(SubImageTransition):
    def create_animation(self, duration: int) -> QAbstractAnimation:
        group = QSequentialAnimationGroup(self)
        taken = np.zeros((10, 8), dtype=np.int_)
        valid_targets = np.append(taken, np.ones((1, 8), dtype=np.int_), axis=0)
        valid_targets = np.roll(valid_targets, -1, 0)[:10, :]
        return super().create_animation(duration)
