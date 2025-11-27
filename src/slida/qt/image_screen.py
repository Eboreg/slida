from typing import TYPE_CHECKING

from PySide6.QtCore import QPointF, QRectF, QSizeF
from PySide6.QtGui import QImage, QPainter, QPixmap, QPixmapCache

from slida.config.base import Config
from slida.qt.utils import get_centered_content_rect


if TYPE_CHECKING:
    from slida.files.image_file import ImageFile


class ImageScreen:
    area: float
    bounds: QSizeF
    can_fit_more: bool
    images: "tuple[ImageFile, ...]"
    inner_rect: QRectF

    __inner_qimage: QImage | None = None
    __outer_qimage: QImage | None = None
    __size: QSizeF

    def __init__(self, bounds: QSizeF, *images: "ImageFile"):
        self.bounds = bounds
        self.images = images
        self.__size = self.__get_size()
        self.area = self.__size.width() * self.__size.height()
        bounds_ratio = self.bounds.width() / self.bounds.height() if self.bounds.height() > 0 else 0.0
        images_ratio = self.__size.width() / self.__size.height() if self.__size.height() > 0 else 0.0
        self.can_fit_more = bounds_ratio - images_ratio >= 0.4
        self.inner_rect = get_centered_content_rect(bounds, self.__size)

    def get_outer_qimage(self) -> QImage:
        if self.__outer_qimage is None:
            self.__outer_qimage = QImage(self.bounds.toSize(), QImage.Format.Format_RGB32)
            self.__outer_qimage.fill(Config.current().background.value)
            if not self.__size.isEmpty():
                qpainter = QPainter(self.__outer_qimage)
                content = self.__get_inner_qimage()
                qpainter.drawImage(self.inner_rect.topLeft(), content)
                qpainter.end()
        return self.__outer_qimage

    def __get_inner_qimage(self) -> QImage:
        if self.__inner_qimage is None:
            config = Config.current()
            self.__inner_qimage = QImage(self.__size.toSize(), QImage.Format.Format_RGB32)
            self.__inner_qimage.fill(config.background.value)
            qpainter = QPainter(self.__inner_qimage)
            left = 0
            height = self.__size.toSize().height()

            for image in self.images:
                if config.debug.value:
                    print(f"Painting {image.path} (file size={image.stat.st_size}, image size={image.size})")
                cache_key = f"{image.path}:{height}"
                qpixmap = QPixmap()

                if not QPixmapCache.find(cache_key, qpixmap):
                    qpixmap = image.qpixmap.scaledToHeight(height)
                    QPixmapCache.insert(cache_key, qpixmap)

                qpainter.drawPixmap(QPointF(left, 0), qpixmap)
                left += qpixmap.width()

            qpainter.end()

        return self.__inner_qimage

    def __get_size(self) -> QSizeF:
        height = self.bounds.height()
        width = sum((f.scaled_width(self.bounds.height()) for f in self.images), 0.0)

        if width > self.bounds.width():
            height = self.bounds.height() * (self.bounds.width() / width)
            width = self.bounds.width()

        return QSizeF(width, height)
