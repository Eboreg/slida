import os

from PySide6.QtCore import QSize
from PySide6.QtGui import QImageReader, QPixmap, QPixmapCache

from slida.config.base import Config


class ImageFile:
    path: str
    stat: os.stat_result
    __is_valid: bool | None = None
    __size: QSize | None = None

    def __init__(self, path: str, stat: os.stat_result):
        self.path = path
        self.stat = stat

    @property
    def is_valid(self) -> bool:
        self.__validate()
        assert self.__is_valid is not None
        return self.__is_valid

    @property
    def qpixmap(self):
        pm = QPixmap()
        if not QPixmapCache.find(self.path, pm):
            reader = QImageReader(self.path)
            reader.setAutoTransform(True)
            pm = QPixmap.fromImageReader(reader)
            QPixmapCache.insert(self.path, pm)
        return pm

    @property
    def size(self) -> QSize:
        self.__validate()
        assert self.__size is not None
        return self.__size

    def __eq__(self, other):
        return isinstance(other, self.__class__) and other.path == self.path

    def __hash__(self):
        return hash(self.path)

    def __repr__(self):
        return f"<ImageFile path={self.path}>"

    def scaled_width(self, height: float) -> float:
        return self.size.width() * (height / self.size.height())

    def __validate(self):
        if self.__is_valid is None:
            if Config.current().debug.value:
                print(f"ImageFile.validate ({self.path})")
            pm = self.qpixmap
            self.__is_valid = not pm.isNull() and pm.height() > 0 and pm.width() > 0
            if self.__is_valid:
                self.__size = pm.size()
