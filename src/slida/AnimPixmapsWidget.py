import random
from PySide6.QtCore import Property, QPoint, QPointF, Qt
from PySide6.QtGui import QConicalGradient, QGradient, QLinearGradient, QPainter, QRadialGradient
from PySide6.QtWidgets import (
    QGraphicsBlurEffect,
    QGraphicsOpacityEffect,
    QGraphicsWidget,
    QStyleOptionGraphicsItem,
    QWidget,
)

from slida.PixmapList import PixmapList
from slida.transitions import Transition
from slida.utils import coerce_between


class AnimPixmapsWidget(QGraphicsWidget):
    __pixmaps: PixmapList | None = None
    __transition: Transition | None = None
    __blur: float = 0.0
    __marquee: float = 1.0
    __random_squares: float = 1.0
    __clockface: float = 1.0
    __radial: float = 1.0
    __radial_center_offset: tuple[float, float] | None = None

    @Property(float) # type: ignore
    def blur(self):  # type: ignore # pylint: disable=method-hidden
        return self.__blur

    @blur.setter
    def blur(self, value: float):
        self.__blur = value
        effect = self.graphicsEffect()

        if not isinstance(effect, QGraphicsBlurEffect):
            effect = QGraphicsBlurEffect(self, blurHints=QGraphicsBlurEffect.BlurHint.AnimationHint)
            self.setGraphicsEffect(effect)

        if value > 0.0:
            effect.setEnabled(True)
            effect.setBlurRadius(value)
        else:
            effect.setEnabled(False)

    @Property(float) # type: ignore
    def clockface(self):  # type: ignore # pylint: disable=method-hidden
        return self.__clockface

    @clockface.setter
    def clockface(self, value: float):
        self.__clockface = value
        effect = self.graphicsEffect()
        brush = QConicalGradient(self.rect().center(), 0)

        if not isinstance(effect, QGraphicsOpacityEffect):
            effect = QGraphicsOpacityEffect(self)
            self.setGraphicsEffect(effect)

        if value < 1.0:
            effect.setEnabled(True)
            effect.setOpacity(1.0)
            v1 = coerce_between(value, 0.0, 1.0)
            v2 = coerce_between(value + 0.02, 0.0, 1.0)
            brush.setColorAt(v1, Qt.GlobalColor.transparent)
            brush.setColorAt(v2, Qt.GlobalColor.black)
            effect.setOpacityMask(brush)
        else:
            effect.setEnabled(False)

    @Property(float) # type: ignore
    def marquee(self):  # type: ignore # pylint: disable=method-hidden
        return self.__marquee

    @marquee.setter
    def marquee(self, value: float):
        self.__marquee = value
        effect = self.graphicsEffect()
        brush = QLinearGradient(QPoint(0, 0), QPoint(50, 0))
        brush.setSpread(QGradient.Spread.RepeatSpread)

        if not isinstance(effect, QGraphicsOpacityEffect):
            effect = QGraphicsOpacityEffect(self)
            self.setGraphicsEffect(effect)

        if value < 1.0:
            effect.setEnabled(True)
            effect.setOpacity(1.0)
            v1 = coerce_between(value, 0.0, 1.0)
            v2 = coerce_between(value + 0.01, 0.0, 1.0)
            brush.setColorAt(v1, Qt.GlobalColor.transparent)
            brush.setColorAt(v2, Qt.GlobalColor.black)
            effect.setOpacityMask(brush)
        else:
            effect.setEnabled(False)

    @Property(float) # type: ignore
    def radial(self):  # type: ignore # pylint: disable=method-hidden
        return self.__radial

    @radial.setter
    def radial(self, value: float):
        self.__radial = value
        effect = self.graphicsEffect()

        if not isinstance(effect, QGraphicsOpacityEffect):
            effect = QGraphicsOpacityEffect(self)
            self.setGraphicsEffect(effect)

        if value < 1.0:
            offset = self.__radial_center_offset

            if not offset:
                offset = random.random(), random.random()
                self.__radial_center_offset = offset

            rect = self.rect()
            center = QPointF(rect.width() * offset[0], rect.height() * offset[1])
            brush = QRadialGradient(center, 25)
            brush.setSpread(QGradient.Spread.ReflectSpread)
            effect.setEnabled(True)
            effect.setOpacity(1.0)
            v1 = coerce_between(value, 0.0, 1.0)
            v2 = coerce_between(value + 0.1, 0.0, 1.0)
            brush.setColorAt(v1, Qt.GlobalColor.transparent)
            brush.setColorAt(v2, Qt.GlobalColor.black)
            effect.setOpacityMask(brush)
        else:
            effect.setEnabled(False)
            self.__radial_center_offset = None

    @Property(float) # type: ignore
    def random_squares(self):  # type: ignore # pylint: disable=method-hidden
        return self.__random_squares

    @random_squares.setter
    def random_squares(self, value: float):
        if value != self.__random_squares:
            self.__random_squares = value
            scaled_image = self.__get_scaled_image()
            if scaled_image and scaled_image.diff(value):
                self.update(self.rect())

    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: QWidget | None = None):
        scaled_image = self.__get_scaled_image()
        transition_name = self.__transition.name if self.__transition else None

        if scaled_image:
            if transition_name == "random_squares":
                for sub in scaled_image.fill_randomly(self.__random_squares):
                    painter.drawImage(sub.geometry, sub.image)
            elif transition_name == "top_squares":
                for sub in scaled_image.fill_from_top(self.__random_squares):
                    painter.drawImage(sub.geometry, sub.image)
            elif transition_name == "topleft_squares":
                for sub in scaled_image.fill_from_top_left(self.__random_squares):
                    painter.drawImage(sub.geometry, sub.image)
            else:
                painter.drawImage(self.rect(), scaled_image.image)

    def reset_transition_properties(self):
        self.setX(0.0)
        self.setY(0.0)
        self.setScale(1.0)
        self.setOpacity(1.0)
        self.setZValue(0.0)
        self.blur = 0.0 # type: ignore
        self.marquee = 1.0 # type: ignore
        self.random_squares = 1.0 # type: ignore
        self.clockface = 1.0 # type: ignore

    def resizeEvent(self, event):
        size = self.size()
        self.setTransformOriginPoint(size.width() / 2, size.height() / 2)
        super().resizeEvent(event)

    def set_pixmaps(self, pixmaps: PixmapList):
        self.__pixmaps = pixmaps

    def set_transition(self, transition: Transition):
        self.__transition = transition

    def __get_scaled_image(self):
        if self.__pixmaps:
            return self.__pixmaps.get_scaled_image(self.size())
        return None
