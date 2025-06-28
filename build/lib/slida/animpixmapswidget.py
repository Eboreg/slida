import dataclasses
from typing import cast

from PySide6.QtCore import (
    Property,
    QEasingCurve,
    QPoint,
    QPropertyAnimation,
    QRectF,
    QSize,
    Qt,
)
from PySide6.QtGui import (
    QColor,
    QColorConstants,
    QGradient,
    QLinearGradient,
    QPainter,
    qAlpha,
    qBlue,
    qGreen,
    qRed,
    qRgba,
)
from PySide6.QtWidgets import (
    QGraphicsBlurEffect,
    QGraphicsOpacityEffect,
    QGraphicsView,
    QGraphicsWidget,
    QWidget,
)

from slida.PixmapList import PixmapList
from slida.transitions import Transition
from slida.utils import coerce_between


@dataclasses.dataclass
class Square:
    geometry: QRectF
    filled: bool = True


class AnimPixmapsWidget(QGraphicsWidget):
    animation: QPropertyAnimation
    pixmaps: PixmapList | None = None
    squares: list[Square]
    _blur: float = 0.0
    _marquee: float = 1.0
    _noop: float = 0.0
    _random_squares: float = 1.0

    def __init__(self, view: QGraphicsView, transition_duration: float = 0.5, **kwargs):
        super().__init__(**kwargs)
        self.setAutoFillBackground(True)
        self.animation = QPropertyAnimation(parent=view, targetObject=self)
        self.animation.setDuration(int(transition_duration * 1000))
        self.animation.setEasingCurve(QEasingCurve.Type.InOutSine)
        self.squares = []
        self.init_squares()

    @Property(float) # type: ignore
    def blur(self):  # type: ignore # pylint: disable=method-hidden
        return self._blur

    @blur.setter
    def blur(self, value: float):
        self._blur = value
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
    def random_squares(self):  # type: ignore # pylint: disable=method-hidden
        return self._random_squares

    @random_squares.setter
    def random_squares(self, value: float):
        self._random_squares = value

    @Property(float) # type: ignore
    def marquee(self):  # type: ignore # pylint: disable=method-hidden
        return self._marquee

    @marquee.setter
    def marquee(self, value: float):
        self._marquee = value
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
    def noop(self): # type: ignore
        return self._noop

    @noop.setter
    def noop(self, value: float):
        self._noop = value

    def init_squares(self):
        size = self.size()
        self.squares = []
        x_squares = 10

        if size.width() > 0:
            width = size.width() / x_squares
            y_squares = round(size.height() / width)
            height = size.height() / y_squares

            for y in range(y_squares):
                for x in range(x_squares):
                    self.squares.append(Square(geometry=QRectF(x * width, y * height, width, height)))

    def paint(self, painter: QPainter, option, widget: QWidget | None = None):
        if self.pixmaps:
            images = self.pixmaps.__get_fitting_images()
            rect = images.__get_rect(self.qsize())
            left = rect.left()
            # print(left)

            for pixmap in images.__get_scaled_pixmaps(self.qsize()):
                """
                image = pixmap.toImage()
                for y in range(100):
                    line = cast(memoryview, image.scanLine(y))
                    # print(y, len(line), line.shape, line)
                    for x in range(100):
                        pixel = image.pixel(x, y)
                        pixel2 = qRgba(qRed(pixel), qGreen(0), qBlue(pixel), qAlpha(pixel))
                        image.setPixel(x, y, pixel2)
                painter.drawImage(left, rect.top(), image)
                """
                painter.drawPixmap(left, rect.top(), pixmap)
                left += pixmap.width()

            # painter.fillRect(self.squares[0].geometry, QColorConstants.Blue)

    def qsize(self) -> QSize:
        qsizef = self.size()
        return QSize(int(qsizef.width()), int(qsizef.height()))

    def reset_transition_properties(self):
        self.setX(0.0)
        self.setY(0.0)
        self.setScale(1.0)
        self.setOpacity(1.0)
        self.blur = 0.0 # type: ignore
        self.marquee = 1.0 # type: ignore

    def resizeEvent(self, event):
        size = self.size()
        self.setTransformOriginPoint(size.width() / 2, size.height() / 2)
        self.init_squares()
        super().resizeEvent(event)

    def set_pixmaps(self, pixmaps: PixmapList):
        self.pixmaps = pixmaps

    def set_transition_duration(self, value: float):
        self.animation.setDuration(int(value * 1000))

    def update_animation(self, transition: Transition):
        self.animation.setPropertyName(transition.property_name.encode())
        self.animation.setStartValue(transition.get_start_value())
        self.animation.setEndValue(transition.get_end_value())
        self.setProperty(transition.property_name, transition.get_start_value())
