from PIL import Image
from PySide6.QtCore import QSizeF


class ImageFile:
    __filename: str
    __size: QSizeF | None = None

    @property
    def aspect_ratio(self) -> float:
        size = self.size
        return size.width() / size.height()

    @property
    def filename(self):
        return self.__filename

    @property
    def size(self) -> QSizeF:
        if self.__size is None:
            with Image.open(self.__filename) as im:
                self.__size = QSizeF(im.width, im.height)
        return self.__size

    def __init__(self, filename: str):
        self.__filename = filename

    def __eq__(self, other):
        return isinstance(other, self.__class__) and other.filename == self.__filename

    def __hash__(self):
        return hash(self.__filename)

    def __repr__(self):
        return f"<ImageFile filename={self.__filename}>"

    def scaled_size(self, height: float) -> QSizeF:
        size = self.size
        return QSizeF(size.width() * (height / size.height()), height)
