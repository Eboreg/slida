from typing import TYPE_CHECKING, Generator, Iterable

from PySide6.QtCore import QRectF, QSizeF


if TYPE_CHECKING:
    from slida.ImageFile import ImageFile
    from slida.ImageFileList import ImageFileList


class ImageFileCombo:
    __images: list["ImageFile"]

    @property
    def images(self):
        return self.__images

    def __init__(self):
        self.__images = []

    def __repr__(self):
        return f"<ImageFileCombo images={repr(self.__images)}>"

    def empty(self) -> list["ImageFile"]:
        images = self.__images.copy()
        self.__images = []
        return images

    def fill(self, bounds: QSizeF, imagelist: "ImageFileList"):
        used_images: list["ImageFile"] = []
        used_area: float = 0.0

        for image in self.__images:
            area = ImageFileCombo.get_used_area(bounds, list(used_images) + [image])
            if area > used_area:
                used_images.append(image)
                used_area = area
            else:
                break

        for image in set(self.__images) - set(used_images):
            imagelist.prepend(image)

        while ImageFileCombo.can_fit_more(bounds, used_images):
            max_ratio = ImageFileCombo.get_next_max_ratio(bounds, used_images)
            image = imagelist.get_next_image(max_ratio)
            if image:
                used_images.append(image)
            else:
                break

        self.__images = used_images

    def get_placed_images(self, bounds: QSizeF) -> "Generator[tuple[ImageFile, QRectF]]":
        rect = ImageFileCombo.get_used_rect(bounds, self.__images)
        left = rect.left()
        for image in self.__images:
            image_size = image.scaled_size(rect.height())
            yield image, QRectF(left, rect.top(), image_size.width(), image_size.height())
            left += image_size.width()

    @staticmethod
    def get_used_rect(bounds: QSizeF, images: Iterable["ImageFile"]) -> QRectF:
        used_size = ImageFileCombo.get_used_size(bounds, images)
        top = 0.0
        left = 0.0
        if used_size.height() < bounds.height():
            top = (bounds.height() - used_size.height()) / 2
        if used_size.width() < bounds.width():
            left = (bounds.width() - used_size.width()) / 2
        return QRectF(left, top, used_size.width(), used_size.height())

    @staticmethod
    def can_fit_more(bounds: QSizeF, images: Iterable["ImageFile"]) -> bool:
        bounds_ratio = bounds.width() / bounds.height()
        images_size = ImageFileCombo.get_used_size(bounds, images)
        images_ratio = images_size.width() / images_size.height()
        return bounds_ratio - images_ratio >= 0.4

    @staticmethod
    def get_next_max_ratio(bounds: QSizeF, images: Iterable["ImageFile"]) -> float | None:
        max_width = bounds.width()
        current_size = ImageFileCombo.get_used_size(bounds, images)
        current_area = current_size.width() * current_size.height()

        if current_area == 0:
            return None

        if current_size.width() < max_width:
            current_ratio = current_size.width() / current_size.height()
            min_height = current_area / max_width
            resized_width = min_height * current_ratio
            remaining_width = max_width - resized_width
            return remaining_width / min_height

        return 0.0

    @staticmethod
    def get_used_area(bounds: QSizeF, images: Iterable["ImageFile"]) -> float:
        size = ImageFileCombo.get_used_size(bounds, images)
        return size.width() * size.height()

    @staticmethod
    def get_used_size(bounds: QSizeF, images: Iterable["ImageFile"]) -> QSizeF:
        height = bounds.height()
        width = sum((f.scaled_size(bounds.height()).width() for f in images), 0.0)

        if width > bounds.width():
            height = bounds.height() * (bounds.width() / width)
            width = bounds.width()

        return QSizeF(width, height)
