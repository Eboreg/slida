import dataclasses
import enum
import mimetypes
import os
import random
from typing import TYPE_CHECKING, Generator


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

    def listdir(self) -> list[File]:
        entries: list[File] = []

        for path in self.root_paths:
            entries.extend(list(self.scandir(path)))

        if self.config.order == FileOrder.NAME:
            return sorted(entries, key=lambda e: e.path.lower(), reverse=self.config.reverse)
        if self.config.order == FileOrder.CREATED:
            return sorted(entries, key=lambda e: e.ctime, reverse=self.config.reverse)
        if self.config.order == FileOrder.MODIFIED:
            return sorted(entries, key=lambda e: e.mtime, reverse=self.config.reverse)
        if self.config.order == FileOrder.RANDOM:
            random.shuffle(entries)
            return entries
        raise RuntimeError("This should not happen")

    def list(self) -> list[str]:
        return [entry.path for entry in self.listdir()]

    def scandir(self, path: str) -> "Generator[File]":
        if os.path.isfile(path):
            stat = os.stat(path)
            if stat.st_ino not in self.visited_inodes:
                mimetype = mimetypes.guess_type(path)
                self.visited_inodes.append(stat.st_ino)
                if mimetype[0] is not None and mimetype[0].startswith("image/"):
                    yield File(path=path, stat=stat)
        elif os.path.isdir(path):
            for entry in os.scandir(path):
                stat = entry.stat()
                if stat.st_ino in self.visited_inodes:
                    continue
                self.visited_inodes.append(stat.st_ino)
                if entry.is_dir() and self.config.recursive:
                    yield from self.scandir(entry.path)
                elif entry.is_file():
                    mimetype = mimetypes.guess_type(entry.path)
                    if mimetype[0] is not None and mimetype[0].startswith("image/"):
                        yield File(path=entry.path, stat=stat)
