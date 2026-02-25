import mimetypes
import os
from typing import Generator

from slida.config import Config
from slida.files.image_file import ImageFile


class DirScanner:
    __visited_inodes: set[int]
    __root_paths: list[str]
    __exclude_paths: set[str]

    def __init__(self, root_paths: str | list[str], exclude_paths: list[str] | None = None):
        self.__root_paths = root_paths if isinstance(root_paths, list) else [root_paths]
        self.__visited_inodes = set()
        self.__exclude_paths = set()

        for exclude in exclude_paths or []:
            exclude = os.path.abspath(exclude)
            self.__exclude_paths.add(exclude)
            if self.__is_symlink(exclude):
                self.__exclude_paths.add(os.path.realpath(exclude))

    def scandir(self, max_size: int = 0) -> "Generator[ImageFile]":
        config = Config.current()
        for path in self.__root_paths:
            yield from self.__scandir(
                entry=os.path.abspath(path),
                is_root=True,
                max_size=max_size,
                recursive=config.recursive.value,
                hidden=config.hidden.value,
                symlinks=config.symlinks.value,
            )

    def __inode(self, entry: os.DirEntry | str):
        if isinstance(entry, os.DirEntry):
            return entry.inode() if not self.__is_symlink(entry) else os.stat(entry.path).st_ino
        return os.stat(entry).st_ino

    def __is_dir(self, entry: os.DirEntry | str):
        return entry.is_dir() if isinstance(entry, os.DirEntry) else os.path.isdir(entry)

    def __is_file(self, entry: os.DirEntry | str):
        return entry.is_file() if isinstance(entry, os.DirEntry) else os.path.isfile(entry)

    def __is_symlink(self, entry: os.DirEntry | str):
        return entry.is_symlink() if isinstance(entry, os.DirEntry) else os.path.islink(entry)

    def __name(self, entry: os.DirEntry | str) -> str:
        return entry.name if isinstance(entry, os.DirEntry) else entry.split("/")[-1]

    def __path(self, entry: os.DirEntry | str) -> str:
        return entry.path if isinstance(entry, os.DirEntry) else entry

    def __realpath(self, entry: os.DirEntry | str):
        return os.path.realpath(entry.path) if isinstance(entry, os.DirEntry) else os.path.realpath(entry)

    def __scandir(
        self,
        entry: os.DirEntry | str,
        hidden: bool,
        symlinks: bool,
        recursive: bool,
        is_root: bool = False,
        max_size: int = 0,
    ) -> "Generator[ImageFile]":
        if any(
            ex for ex in self.__exclude_paths
            if self.__path(entry).startswith(ex)
            or (is_root and self.__realpath(entry).startswith(ex))
        ):
            return

        if not is_root:
            if not hidden and self.__name(entry).startswith("."):
                return
            if not symlinks and self.__is_symlink(entry):
                return

        if self.__is_dir(entry):
            if is_root or recursive:
                inode = self.__inode(entry)
                if inode not in self.__visited_inodes:
                    self.__visited_inodes.add(inode)
                    with os.scandir(entry) as dir:
                        for subentry in dir:
                            yield from self.__scandir(
                                entry=subentry,
                                max_size=max_size,
                                hidden=hidden,
                                symlinks=symlinks,
                                recursive=recursive,
                            )

        elif self.__is_file(entry):
            mimetype = mimetypes.guess_file_type(self.__path(entry))
            if mimetype[0] is not None and mimetype[0].startswith("image/"):
                inode = self.__inode(entry)
                if inode not in self.__visited_inodes:
                    stat = self.__stat(entry)
                    self.__visited_inodes.add(inode)
                    if max_size == 0 or stat.st_size <= max_size:
                        yield ImageFile(path=self.__path(entry), stat=stat)

    def __stat(self, entry: os.DirEntry | str) -> os.stat_result:
        return entry.stat() if isinstance(entry, os.DirEntry) else os.stat(entry)
