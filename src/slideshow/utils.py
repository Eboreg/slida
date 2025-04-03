from pathlib import Path

from PIL import Image


def is_portrait(file: Path | str) -> bool:
    with Image.open(file) as image:
        return image.width / image.height < 0.9


def coerce_between(value: float, min_value: float, max_value: float) -> float:
    if value < min_value:
        return min_value
    if value > max_value:
        return max_value
    return value
