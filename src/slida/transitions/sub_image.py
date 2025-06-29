from abc import abstractmethod

from PySide6.QtCore import QEasingCurve
from PySide6.QtGui import QPainter

from slida.ScaledImage import ScaledImage, SubImage
from slida.transitions.base import Transition


class SubImageTransition(Transition):
    parent_z = 1.0

    @abstractmethod
    def get_sub_images(self, scaled_image: ScaledImage) -> list[SubImage]:
        ...

    def on_progress(self, value: float):
        super().on_progress(value)
        if not self._scaled_image or self._scaled_image.diff(value):
            self.parent().update(self.parent().rect())

    def paint(self, painter: QPainter, scaled_image: ScaledImage):
        for sub in self.get_sub_images(scaled_image):
            painter.drawImage(sub.geometry, sub.image)


class RandomSquaresIn(SubImageTransition):
    easing = QEasingCurve.Type.InCubic

    def get_sub_images(self, scaled_image: ScaledImage) -> list[SubImage]:
        return scaled_image.fill_randomly(self._progress)


class TopLeftSquaresIn(SubImageTransition):
    def get_sub_images(self, scaled_image: ScaledImage) -> list[SubImage]:
        return scaled_image.fill_from_top_left(self._progress)


class TopSquaresIn(SubImageTransition):
    def get_sub_images(self, scaled_image: ScaledImage) -> list[SubImage]:
        return scaled_image.fill_from_top(self._progress)
