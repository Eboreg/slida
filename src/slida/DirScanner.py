import dataclasses
import enum
import mimetypes
import os
import random
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from slida.UserConfig import UserConfig


class FileOrder(enum.StrEnum):
    NAME = "name"
    CREATED = "created"
    MODIFIED = "modified"
    RANDOM = "random"


@dataclasses.dataclass
class File:
    path: str
    stat: dataclasses.InitVar[os.stat_result]
    ctime: float = dataclasses.field(init=False)
    mtime: float = dataclasses.field(init=False)
    ino: int = dataclasses.field(init=False)

    def __post_init__(self, stat: os.stat_result):
        self.ctime = stat.st_ctime
        self.mtime = stat.st_mtime
        self.ino = stat.st_ino


class DirScanner:
    def __init__(self, root_paths: str | list[str], config: "UserConfig | None" = None):
        from slida.UserConfig import UserConfig

        self.root_paths = root_paths if isinstance(root_paths, list) else [root_paths]
        self.config = config or UserConfig()
        self.visited_inodes: list[int] = []

    def list(self) -> list[str]:
        return [entry.path for entry in self.__listdir()]

    def __inode(self, entry: os.DirEntry | str):
        return entry.inode() if isinstance(entry, os.DirEntry) else os.stat(entry).st_ino

    def __is_dir(self, entry: os.DirEntry | str):
        return entry.is_dir() if isinstance(entry, os.DirEntry) else os.path.isdir(entry)

    def __is_file(self, entry: os.DirEntry | str):
        return entry.is_file() if isinstance(entry, os.DirEntry) else os.path.isfile(entry)

    def __listdir(self) -> "list[File]":
        entries: list[File] = []

        for path in self.root_paths:
            entries.extend(list(self.__scandir(path, is_root=True)))

        if self.config.order.value == FileOrder.NAME:
            return sorted(entries, key=lambda e: e.path.lower(), reverse=self.config.reverse.value)
        if self.config.order.value == FileOrder.CREATED:
            return sorted(entries, key=lambda e: e.ctime, reverse=self.config.reverse.value)
        if self.config.order.value == FileOrder.MODIFIED:
            return sorted(entries, key=lambda e: e.mtime, reverse=self.config.reverse.value)
        if self.config.order.value == FileOrder.RANDOM:
            random.shuffle(entries)
            return entries
        raise RuntimeError("This should not happen")

    def __path(self, entry: os.DirEntry | str):
        return entry.path if isinstance(entry, os.DirEntry) else entry

    def __scandir(self, entry: os.DirEntry | str, is_root: bool = False):
        if self.__is_dir(entry):
            if is_root or self.config.recursive.value:
                inode = self.__inode(entry)
                if inode not in self.visited_inodes:
                    self.visited_inodes.append(inode)
                    with os.scandir(entry) as dir:
                        for subentry in dir:
                            yield from self.__scandir(subentry)

        elif self.__is_file(entry):
            mimetype = mimetypes.guess_type(self.__path(entry))
            if mimetype[0] is not None and mimetype[0].startswith("image/"):
                stat = self.__stat(entry)
                if stat.st_ino not in self.visited_inodes:
                    self.visited_inodes.append(stat.st_ino)
                    yield File(path=self.__path(entry), stat=stat)

    def __stat(self, entry: os.DirEntry | str):
        return entry.stat() if isinstance(entry, os.DirEntry) else os.stat(entry)
