from typing import Iterable, TYPE_CHECKING
import PIL
from PySide6.QtCore import QSizeF

if TYPE_CHECKING:
    from slida.ImageFile import ImageFile
    from slida.ImageFileCombo import ImageFileCombo


class ImageFileList:
    __history: list["ImageFileCombo"]
    __images: list["ImageFile"]
    __initial_images: list["ImageFile"]

    def __init__(self, filenames: Iterable[str]):
        from slida.ImageFile import ImageFile

        self.__images = [ImageFile(f) for f in filenames]
        self.__initial_images = self.__images.copy()
        self.__history = []

    def get_history_entry(self, index: int, bounds: QSizeF):
        from slida.ImageFileCombo import ImageFileCombo

        while len(self.__history) <= index:
            self.__history.append(ImageFileCombo())
        entry = self.__history[index]
        for next_entry in reversed(self.__history[index + 1:]):
            for image in reversed(next_entry.empty()):
                self.prepend(image)
        entry.fill(bounds, self)
        return entry

    def get_next_image(self, max_ratio: float | None, reinited: bool = False) -> "ImageFile | None":
        images = self.__images.copy()

        for image in images:
            try:
                if max_ratio is None or image.aspect_ratio <= max_ratio:
                    self.__remove(image)
                    return image
            except PIL.UnidentifiedImageError:
                self.__remove(image, initial=True)

        if not reinited:
            self.__images = self.__initial_images.copy()
            return self.get_next_image(max_ratio, reinited=True)

        return None

    def prepend(self, image: "ImageFile"):
        self.__images.insert(0, image)

    def __remove(self, image: "ImageFile", initial: bool = False):
        while image in self.__images:
            self.__images.remove(image)
        if initial:
            while image in self.__initial_images:
                self.__initial_images.remove(image)
