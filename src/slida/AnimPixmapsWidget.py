from PySide6.QtCore import QRectF, QSizeF, Qt
from PySide6.QtGui import QImage, QPainter, QPixmap
from PySide6.QtWidgets import (
    QGraphicsSceneResizeEvent,
    QGraphicsWidget,
    QStyleOptionGraphicsItem,
    QWidget,
)

from slida.debug import add_live_object, remove_live_object
from slida.ImageFileCombo import ImageFileCombo
from slida.transitions import Transition


class AnimPixmapsWidget(QGraphicsWidget):
    __combo: ImageFileCombo

    __qimage: QImage | None = None
    __qimage_rect: QRectF | None = None
    __transition: Transition | None = None

    def __init__(self, combo: ImageFileCombo, size: QSizeF):
        super().__init__(size=size)
        self.__combo = combo
        add_live_object(id(self), self.__class__.__name__)

    @property
    def combo(self):
        return self.__combo

    def deleteLater(self):
        if self.__transition:
            self.__transition.deleteLater()
        remove_live_object(id(self))
        super().deleteLater()

    def get_current_filenames(self):
        return [i.filename for i in self.__combo.images]

    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: QWidget | None = None):
        qimage, rect = self.__get_qimage()

        if self.__transition:
            self.__transition.paint(painter, qimage, rect)
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

    def __get_qimage(self) -> tuple[QImage, QRectF]:
        if self.__qimage and self.__qimage_rect:
            return self.__qimage, self.__qimage_rect

        size = self.size()
        qimage = QImage(size.toSize(), QImage.Format.Format_RGB32)
        qimage.fill(Qt.GlobalColor.black)
        painter = QPainter(qimage)
        image_rects: list[QRectF] = []
        self.__qimage_rect = QRectF()

        for image, image_rect in self.__combo.get_placed_images(size):
            pixmap = QPixmap(image.filename).scaled(image_rect.size().toSize())
            painter.drawPixmap(image_rect.topLeft(), pixmap)
            image_rects.append(image_rect)

        if image_rects:
            self.__qimage_rect.setTopLeft(image_rects[0].topLeft())
            self.__qimage_rect.setBottomRight(image_rects[-1].bottomRight())
        painter.end()
        self.__qimage = qimage

        return qimage, self.__qimage_rect
