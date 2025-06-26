from PySide6.QtCore import QSize

from slida.qimage import QImage
from slida.qimages import QImages


class PixmapList:
    _images: QImages
    _bounds: QSize
    _fitting_images_cache: QImages | None = None

    def __init__(self, bounds: QSize):
        self._images = QImages()
        self._bounds = bounds

    def add_image(self, image: QImage):
        self._images.add(image)
        self._fitting_images_cache = None

    def can_fit_more(self) -> bool:
        return self.get_remaining_ratio() >= 0.4

    def fitting_image_max_ratio(self) -> float | None:
        max_x = self._bounds.width()
        current_x, current_y = self._images.get_size(self._bounds)
        current_a = current_x * current_y

        if current_x == 0:
            return None

        if current_x < max_x:
            current_ratio = current_x / current_y
            min_y = current_a / max_x
            resized_x = min_y * current_ratio
            remaining_x = max_x - resized_x
            return remaining_x / min_y

        return 0.0

    def get_fitting_images(self) -> QImages:
        if self._fitting_images_cache:
            return self._fitting_images_cache

        images = QImages()

        for image in self._images.images:
            if images.get_empty_area(self._bounds) >= images.copy().add(image).get_empty_area(self._bounds):
                images.add(image)

        self._fitting_images_cache = images
        return images

    def get_remaining_ratio(self) -> float:
        bounds_ratio = self._bounds.width() / self._bounds.height()
        return bounds_ratio - self._images.aspect_ratio
