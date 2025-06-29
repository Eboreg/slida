import argparse
import dataclasses
import warnings
from pathlib import Path

import platformdirs
import yaml

from slida.DirScanner import FileOrder


@dataclasses.dataclass
class UserConfig:
    recursive: bool = False
    no_auto: bool = False
    no_tiling: bool = False
    interval: int = 20
    order: FileOrder = FileOrder.RANDOM
    reverse: bool = False
    transition_duration: float = 0.3
    transitions: list[str] | None = None
    exclude_transitions: list[str] | None = None

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

    @classmethod
    def read(cls, cli_args: argparse.Namespace | None = None, custom_dirs: list[Path] | None = None):
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
                        if "exclude-transitions" in file_config and "transitions" in config:
                            del file_config["exclude-transitions"]
                        if "transitions" in file_config and "all" in file_config["transitions"]:
                            file_config["transitions"] = [t for t in file_config["transitions"] if t != "all"]
                        config = {**file_config, **config}
                    except Exception as e:
                        warnings.warn(f"Could not read YAML from {path}: {e}")

        return cls.from_dict(config)
