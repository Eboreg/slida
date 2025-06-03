import enum
import mimetypes
import os
import random
from typing import Generator


class FileOrder(enum.StrEnum):
    NAME = "name"
    CREATED = "created"
    MODIFIED = "modified"
    RANDOM = "random"


class DirScanner:
    def __init__(self, root_path: str, recursive: bool = False):
        self.root_path = root_path
        self.recursive = recursive
        self.visited_inodes: list[int] = []

    def listdir(self, order: FileOrder, reverse: bool = False) -> list[os.DirEntry]:
        entries = list(self.scandir())
        if order == FileOrder.NAME:
            return sorted(entries, key=lambda e: e.path.lower(), reverse=reverse)
        if order == FileOrder.CREATED:
            return sorted(entries, key=lambda e: e.stat().st_ctime, reverse=reverse)
        if order == FileOrder.MODIFIED:
            return sorted(entries, key=lambda e: e.stat().st_mtime, reverse=reverse)
        if order == FileOrder.RANDOM:
            random.shuffle(entries)
            return entries
        raise RuntimeError("This should not happen")

    def list(self, order: FileOrder, reverse: bool = False) -> list[str]:
        return [entry.path for entry in self.listdir(order=order, reverse=reverse)]

    def scandir(self, path: str | None = None) -> "Generator[os.DirEntry]":
        path = path or self.root_path
        for entry in os.scandir(path):
            inode = entry.stat().st_ino
            if inode in self.visited_inodes:
                continue
            self.visited_inodes.append(inode)
            if entry.is_dir() and self.recursive:
                yield from self.scandir(entry.path)
            elif entry.is_file():
                mimetype = mimetypes.guess_type(entry.path)
                if mimetype[0] is not None and mimetype[0].startswith("image/"):
                    yield entry
