import mimetypes
import os
from typing import Generator


class DirScanner:
    def __init__(self, root_path: str):
        self.root_path = root_path
        self.visited_inodes = []

    def scan(self, path: str | None = None) -> "Generator[str]":
        path = path or self.root_path
        for entry in os.scandir(path):
            inode = entry.stat().st_ino
            if inode in self.visited_inodes:
                continue
            self.visited_inodes.append(inode)
            if entry.is_dir():
                yield from self.scan(entry.path)
            elif entry.is_file():
                mimetype = mimetypes.guess_type(entry.path)
                if mimetype[0] is not None and mimetype[0].startswith("image/"):
                    yield entry.path
