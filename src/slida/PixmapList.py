from PySide6.QtCore import QSizeF

from slida.SlidaImage import SlidaImage
from slida.SlidaImages import ScaledImage, SlidaImages


class PixmapList:
    __images: SlidaImages
    __bounds: QSizeF
    __fitting_images_cache: SlidaImages | None = None

    def __init__(self, bounds: QSizeF):
        self.__images = SlidaImages()
        self.__bounds = bounds

    def __repr__(self):
        return f"<PixmapList images={repr(self.__images)}, bounds={self.__bounds}>"

    def add_image(self, image: SlidaImage):
        self.__images.add(image)
        self.__fitting_images_cache = None

    def can_fit_more(self) -> bool:
        bounds_ratio = self.__bounds.width() / self.__bounds.height()
        return bounds_ratio - self.__images.aspect_ratio >= 0.4

    def fitting_image_max_ratio(self) -> float | None:
        max_x = self.__bounds.width()
        current_x, current_y = self.__images.get_size(self.__bounds)
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

    def get_scaled_image(self, bounds: QSizeF) -> ScaledImage:
        images = self.__get_fitting_images()
        return images.get_scaled_image(bounds)

    def __get_fitting_images(self) -> SlidaImages:
        if self.__fitting_images_cache:
            return self.__fitting_images_cache

        images = SlidaImages()

        for image in self.__images.images:
            if images.get_empty_area(self.__bounds) >= images.copy().add(image).get_empty_area(self.__bounds):
                images.add(image)

        self.__fitting_images_cache = images
        return images
