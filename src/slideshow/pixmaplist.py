from PySide6.QtCore import QSize
from PySide6.QtGui import QPixmap

from slideshow.qimage import QImage
from slideshow.qimages import QImages


class PixmapList:
    _images: QImages
    _bounds: QSize
    _fitting_images_cache: QImages | None = None

    def __init__(self, bounds: QSize):
        self._images = QImages()
        self._bounds = bounds

    def add_pixmap(self, pixmap: QPixmap):
        self._images.add(QImage(pixmap))
        self._fitting_images_cache = None

    def can_fit_landscape(self):
        return self.get_remaining_ratio() >= 1.3

    def can_fit_portrait(self):
        return self.get_remaining_ratio() >= 0.4

    def get_fitting_images(self):
        if self._fitting_images_cache:
            return self._fitting_images_cache

        images = QImages()

        for image in self._images.images:
            if images.get_empty_area(self._bounds) >= images.copy().add(image).get_empty_area(self._bounds):
                images.add(image)

        self._fitting_images_cache = images
        return images

    def get_remaining_ratio(self):
        bounds_ratio = self._bounds.width() / self._bounds.height()
        return bounds_ratio - self._images.aspect_ratio

    def set_bounds(self, bounds: QSize):
        self._bounds = bounds
        self._fitting_images_cache = None
