import re
from pathlib import Path
from typing import TypeVar

from PIL import Image


_NT = TypeVar("_NT", int, float)


class CaseType:
    @staticmethod
    def split(value: str) -> list[str]:
        ...

    @staticmethod
    def join(parts: list[str]) -> str:
        ...


class CamelCase(CaseType):
    @staticmethod
    def split(value: str) -> list[str]:
        return [m.group() for m in re.finditer(r"(^[a-z]*)|([A-Z][a-z]*)", value)]

    @staticmethod
    def join(parts: list[str]) -> str:
        if len(parts) == 0:
            return ""
        return parts[0].lower() + "".join(p.capitalize() for p in parts[1:])


class ConstantCase(CaseType):
    @staticmethod
    def split(value: str) -> list[str]:
        return value.split("_")

    @staticmethod
    def join(parts: list[str]) -> str:
        return "_".join(p.upper() for p in parts)


class KebabCase(CaseType):
    @staticmethod
    def split(value: str) -> list[str]:
        return value.split("-")

    @staticmethod
    def join(parts: list[str]) -> str:
        return "-".join(p.lower() for p in parts)


class PascalCase(CaseType):
    @staticmethod
    def split(value: str) -> list[str]:
        return [m.group() for m in re.finditer(r"(^[a-z]*)|([A-Z][a-z]*)", value)]

    @staticmethod
    def join(parts: list[str]) -> str:
        return "".join(p.capitalize() for p in parts)


class SnakeCase(CaseType):
    @staticmethod
    def split(value: str) -> list[str]:
        return value.split("_")

    @staticmethod
    def join(parts: list[str]) -> str:
        return "_".join(p.lower() for p in parts)


def image_ratio(file: Path | str) -> float:
    with Image.open(file) as image:
        return image.width / image.height


def coerce_between(value: _NT, min_value: _NT, max_value: _NT) -> _NT:
    if value < min_value:
        return min_value
    if value > max_value:
        return max_value
    return value


def convert_case(value: str, source: type[CaseType], target: type[CaseType]) -> str:
    return target.join(source.split(value))
