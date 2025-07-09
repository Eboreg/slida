from PySide6.QtCore import QObject, QSizeF

from slida.ScaledImage import ScaledImage
from slida.SlidaImage import SlidaImage
from slida.SlidaImages import SlidaImages


class PixmapList(QObject):
    __images: SlidaImages
    __bounds: QSizeF

    def __init__(self, parent: QObject, bounds: QSizeF):
        super().__init__(parent)
        self.__images = SlidaImages(self)
        self.__bounds = bounds

    def __len__(self):
        return len(self.__images)

    def __repr__(self):
        return f"<PixmapList images={repr(self.__images)}, bounds={self.__bounds}>"

    def add_image(self, image: SlidaImage):
        self.__images.add(image)
        # self.__fitting_images_cache = None

    def can_fit_more(self) -> bool:
        bounds_ratio = self.__bounds.width() / self.__bounds.height()
        return bounds_ratio - self.__images.aspect_ratio >= 0.4

    def deleteLater(self):
        self.__images.deleteLater()
        super().deleteLater()

    def fitting_image_max_ratio(self) -> float | None:
        max_width = self.__bounds.width()
        current_size = self.__images.get_size(self.__bounds)
        current_area = current_size.width() * current_size.height()

        if current_size.width() == 0:
            return None

        if current_size.width() < max_width:
            current_ratio = current_size.width() / current_size.height()
            min_height = current_area / max_width
            resized_width = min_height * current_ratio
            remaining_width = max_width - resized_width
            return remaining_width / min_height

        return 0.0

    def get_scaled_image(self, bounds: QSizeF) -> ScaledImage:
        images = SlidaImages(self)

        for image in self.__images.images:
            if images.get_empty_area(self.__bounds) >= images.copy().add(image).get_empty_area(self.__bounds):
                images.add(image)

        return images.get_scaled_image(bounds)
