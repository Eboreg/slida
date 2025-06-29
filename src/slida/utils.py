import argparse
import dataclasses
import warnings
from pathlib import Path
from typing import TypedDict

import platformdirs
import yaml
from PIL import Image

from slida.DirScanner import FileOrder


class TransitionsConfigDict(TypedDict, total=False):
    include: list[str]
    exclude: list[str]


@dataclasses.dataclass
class UserConfig:
    recursive: bool = False
    no_auto: bool = False
    interval: int = 20
    order: FileOrder = FileOrder.RANDOM
    reverse: bool = False
    transition_duration: float = 0.5
    transitions: TransitionsConfigDict | None = None

    @property
    def exclude_transitions(self):
        if self.transitions and "exclude" in self.transitions:
            return self.transitions["exclude"]
        return None

    @property
    def include_transitions(self):
        if self.transitions and "include" in self.transitions:
            return self.transitions["include"]
        return None

    def check(self):
        if self.interval < 1:
            raise ValueError("Minimum interval is 1 s.")
        if self.interval < self.transition_duration:
            raise ValueError("Interval cannot be less than transition duration.")

    @classmethod
    def from_dict(cls, d: dict):
        config = cls()

        for field in dataclasses.fields(config):
            arg_name = field.name.replace("_", "-")
            if arg_name in d:
                if isinstance(field.type, type) and not isinstance(d[arg_name], field.type):
                    continue
                setattr(config, field.name, d[arg_name])

        return config


def image_ratio(file: Path | str) -> float:
    with Image.open(file) as image:
        return image.width / image.height


def coerce_between(value: float, min_value: float, max_value: float) -> float:
    if value < min_value:
        return min_value
    if value > max_value:
        return max_value
    return value


def read_user_config(cli_args: argparse.Namespace | None = None, custom_dirs: list[Path] | None = None):
    config = {}
    paths: list[Path] = []
    if cli_args:
        config.update({k.replace("_", "-"): v for k, v in cli_args.__dict__.items() if v is not None})
    for custom_dir in custom_dirs or []:
        paths.append(custom_dir / "slida.yaml")
    paths.extend([
        Path("slida.yaml"),
        platformdirs.user_config_path("slida") / "slida.yaml",
    ])

    for path in paths:
        if path.is_file():
            with path.open("rt", encoding="utf8") as f:
                try:
                    file_config: dict = yaml.safe_load(f)
                    if "exclude-transitions" in config and "include-transitions" in file_config:
                        del file_config["include-transitions"]
                    config = {**file_config, **config}
                except Exception as e:
                    warnings.warn(f"Could not read YAML from {path}: {e}")

    return UserConfig.from_dict(config)
