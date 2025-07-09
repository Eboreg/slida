from PyQt6.QtGui import QPainter
from PyQt6.QtWidgets import (
    QGraphicsWidget,
    QStyleOptionGraphicsItem,
    QWidget,
)

from slida.PixmapList import PixmapList
from slida.ScaledImage import ScaledImage
from slida.transitions import Transition


class AnimPixmapsWidget(QGraphicsWidget):
    __pixmaps: PixmapList | None = None
    __transition: Transition | None = None

    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: QWidget | None = None):
        scaled_image = self.__get_scaled_image()

        if scaled_image:
            if self.__transition:
                self.__transition.paint(painter, scaled_image)
            else:
                painter.drawImage(self.rect(), scaled_image.get_image())

    def set_pixmaps(self, pixmaps: PixmapList):
        self.__pixmaps = pixmaps

    def set_transition(self, transition: Transition):
        if self.__transition:
            self.__transition.deleteLater()
        self.__transition = transition
        scaled_image = self.__get_scaled_image()
        if scaled_image:
            transition.set_scaled_image(scaled_image)

    def __get_scaled_image(self) -> ScaledImage | None:
        if self.__pixmaps:
            return self.__pixmaps.get_scaled_image(self.size())
        return None
