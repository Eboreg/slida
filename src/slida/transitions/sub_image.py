from math import ceil, floor

from PySide6.QtCore import QAbstractAnimation, QEasingCurve, QObject, QRect, QSequentialAnimationGroup, QSize
from PySide6.QtGui import QImage, QPainter

import numpy as np
from slida.debug import add_live_object, remove_live_object
from slida.transitions.base import Transition


class SubImage(QObject):
    column: int
    filled: bool = False
    row: int

    def __init__(self, parent: QObject, row: int, column: int, filled: bool = False):
        super().__init__(parent)
        self.row = row
        self.column = column
        self.filled = filled
        add_live_object(id(self), self.__class__.__name__)

    def deleteLater(self):
        remove_live_object(id(self))
        super().deleteLater()

    def toggle_filled(self):
        self.filled = not self.filled


class SubImageTransition(Transition):
    __subs: list[SubImage] | None = None
    columns: int = 0
    parent_z = 1.0
    rows: int = 0

    def deleteLater(self):
        for sub in self.__subs or []:
            sub.deleteLater()
        super().deleteLater()

    def get_sub_image_weight(self, s: SubImage) -> float:
        return 1.0

    def on_progress(self, value: float):
        super().on_progress(value)
        if self.__diff():
            self.parent().update(self.parent().rect())

    def paint(self, painter: QPainter, image: QImage):
        for sub in self.__get_filled_subs(image.size()):
            geometry = self.__get_sub_geometry(image.size(), sub)
            painter.drawImage(geometry, image.copy(geometry))

    def __diff(self) -> int:
        if self.__subs:
            filled_before = len([s for s in self.__subs if s.filled])
            filled_after = round(len(self.__subs) * self._progress)
            return filled_after - filled_before
        return 0

    def __get_filled_subs(self, size: QSize) -> list[SubImage]:
        subs = self.__subs if self.__subs else self.__get_subs(size)

        if self._progress in (0.0, 1.0):
            for sub in subs:
                sub.filled = bool(self._progress)
            return subs if self._progress else []

        filled_subs = [s for s in subs if s.filled]
        filled_before = len(filled_subs)
        filled_after = round(len(subs) * self._progress)
        diff = filled_after - filled_before

        if diff != 0:
            unfilled_subs = [s for s in subs if not s.filled]
            weights = None
            probabilities = None
            subs = unfilled_subs if diff > 0 else filled_subs
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

        return filled_subs

    def __get_sub_geometry(self, size: QSize, sub: SubImage) -> QRect:
        sub_width = size.width() / self.columns
        sub_height = size.height() / self.rows
        return QRect(floor(sub.column * sub_width), floor(sub.row * sub_height), ceil(sub_width), ceil(sub_height))

    def __get_subs(self, size: QSize) -> list[SubImage]:
        subs: list[SubImage] = []

        if size.width() > 0:
            self.columns = round(size.width() / 50)
            sub_width = size.width() / self.columns
            self.rows = round(size.height() / sub_width)

            for y in range(self.rows):
                for x in range(self.columns):
                    subs.append(SubImage(parent=self, row=y, column=x))

        self.__subs = subs
        return subs


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
