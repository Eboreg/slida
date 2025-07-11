from PySide6.QtCore import QSizeF, Qt
from PySide6.QtGui import QImage, QPainter, QPixmap
from PySide6.QtWidgets import (
    QGraphicsSceneResizeEvent,
    QGraphicsWidget,
    QStyleOptionGraphicsItem,
    QWidget,
)

from slida.ImageFileCombo import ImageFileCombo
from slida.debug import add_live_object, remove_live_object
from slida.transitions import Transition


class AnimPixmapsWidget(QGraphicsWidget):
    __combo: ImageFileCombo

    __qimage: QImage | None = None
    __transition: Transition | None = None

    def __init__(self, combo: ImageFileCombo, size: QSizeF):
        super().__init__(size=size)
        self.__combo = combo
        add_live_object(id(self), self.__class__.__name__)

    def deleteLater(self):
        if self.__transition:
            self.__transition.deleteLater()
        remove_live_object(id(self))
        super().deleteLater()

    def get_current_filenames(self):
        return [i.filename for i in self.__combo.images]

    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: QWidget | None = None):
        qimage = self.__get_qimage()

        if self.__transition:
            self.__transition.paint(painter, qimage)
        else:
            painter.drawImage(self.rect(), qimage)

    def resizeEvent(self, event: QGraphicsSceneResizeEvent):
        super().resizeEvent(event)
        self.__qimage = None

    def set_transition(self, transition: Transition | None):
        if self.__transition:
            self.__transition.deleteLater()
        if transition:
            transition.setParent(self)
        self.__transition = transition

    def __get_qimage(self) -> QImage:
        if self.__qimage:
            return self.__qimage

        size = self.size()
        qimage = QImage(size.toSize(), QImage.Format.Format_ARGB32)
        qimage.fill(Qt.GlobalColor.black)
        painter = QPainter(qimage)

        for image, rect in self.__combo.get_placed_images(size):
            pixmap = QPixmap(image.filename).scaled(rect.size().toSize())
            painter.drawPixmap(rect.topLeft(), pixmap)

        painter.end()
        self.__qimage = qimage

        return qimage
