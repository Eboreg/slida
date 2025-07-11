import argparse
import functools
import warnings
from pathlib import Path
from typing import Callable, Generic, NotRequired, Self, Sequence, TypedDict, TypeVar

import platformdirs
import yaml

from slida.DirScanner import FileOrder


_T = TypeVar("_T")


class TransitionConfig(TypedDict):
    exclude: NotRequired[list[str]]
    include: NotRequired[list[str]]


class UserConfigField(Generic[_T]):
    __default: _T

    def __init__(self, type: type[_T], default: _T | Callable[[], _T], value: _T | None = None):
        if isinstance(default, Callable):
            self.__default = default()
        else:
            self.__default = default
        self.__type = type
        self.__explicit_value = value

    def __add__(self, other):
        if isinstance(other, self.__class__):
            return self.__class__(
                type=self.__type,
                default=self.default,
                value=other.explicit_value if other.explicit_value is not None else self.explicit_value,
            )
        return NotImplemented

    def __repr__(self):
        return str(self.value)

    @property
    def default(self) -> _T:
        return self.__default

    @property
    def explicit_value(self) -> _T | None:
        return self.__explicit_value

    @property
    def type(self) -> type[_T]:
        return self.__type

    @property
    def value(self) -> _T:
        return self.__explicit_value if self.__explicit_value is not None else self.__default

    @value.setter
    def value(self, v: _T):
        if not issubclass(self.__type, type(v)):
            raise TypeError(f"{v} is not of type '{self.__type}'")
        self.__explicit_value = v

    def copy(self):
        return self.__class__(type=self.__type, default=self.__default, value=self.__explicit_value)


class UserConfig:
    source: str | None

    auto = UserConfigField(bool, True)
    interval = UserConfigField(int, 20)
    tiling = UserConfigField(bool, True)
    order = UserConfigField(FileOrder, FileOrder.RANDOM)
    recursive = UserConfigField(bool, False)
    reverse = UserConfigField(bool, False)
    transition_duration = UserConfigField(float, 0.3)
    transitions = UserConfigField(TransitionConfig, dict)

    def __init__(self, source: str | None = None):
        self.source = source
        for fieldname, field in self.get_fields().items():
            setattr(self, fieldname, field.copy())

    def __repr__(self):
        return self.repr()

    def repr(self, indent: int = 0, prefix: str = ""):
        if len(prefix) < indent:
            prefix = f"{prefix:{indent}s}"
        changed = {k.replace("_", "-"): v for k, v in self.get_fields().items() if v.explicit_value is not None}
        result = [f"{prefix}{self.__class__.__name__}(" + (self.source or "") + ")"]
        for k, v in changed.items():
            result.append((" " * indent) + f"  {k}: {v}")
        return "\n".join(result)

    def check(self):
        if self.interval.value < 1:
            raise ValueError("Minimum interval is 1 s.")
        if self.interval.value < self.transition_duration.value:
            raise ValueError("Interval cannot be less than transition duration.")

    def get_fields(self) -> dict[str, UserConfigField]:
        fields = {}
        for attrname in dir(self):
            attr = getattr(self, attrname)
            if isinstance(attr, UserConfigField):
                fields[attrname] = attr
        return fields

    @classmethod
    def from_cli_args(cls, args: argparse.Namespace):
        config_dict = {}
        cli_dict = {k.replace("_", "-"): v for k, v in args.__dict__.items() if v is not None}

        if "transitions" in cli_dict:
            config_dict["transitions"] = {"include": cli_dict["transitions"]}
            del cli_dict["transitions"]

        if "exclude-transitions" in cli_dict:
            config_dict["transitions"] = config_dict.get("transitions", {})
            config_dict["transitions"]["exclude"] = cli_dict["exclude-transitions"]
            del cli_dict["exclude-transitions"]

        config_dict.update(cli_dict)
        return cls.from_dict(config_dict, "CLI")

    @classmethod
    def from_dict(cls, d: dict, source: str | None = None):
        config = cls(source=source)

        for field_name, field in config.get_fields().items():
            arg_name = field_name.replace("_", "-")
            if arg_name in d and issubclass(field.type, type(d[arg_name])):
                field.value = d[arg_name]
            elif field.type == bool:
                no_arg_name = "no-" + arg_name
                if no_arg_name in d and isinstance(d[no_arg_name], bool):
                    field.value = not d[no_arg_name]

        return config

    @classmethod
    def from_file(cls, path: Path):
        with path.open("rt", encoding="utf8") as f:
            config_dict: dict = yaml.safe_load(f)
            return cls.from_dict(config_dict, str(path))


class DefaultUserConfig(UserConfig):
    def __init__(self, source: str | None = None):
        super().__init__(source)
        for field in self.get_fields().values():
            field.value = field.default


class CombinedUserConfig(UserConfig):
    subconfigs: Sequence["UserConfig"]

    def __init__(self, source: str | None = None):
        super().__init__(source)
        self.subconfigs = []
        # for field in self.get_fields().values():
        #     field.value = field.default

    def __repr__(self):
        result = self.repr()
        for index, sub in enumerate(self.subconfigs):
            result += "\n" + sub.repr(indent=2, prefix="=" if index == 0 else "+")
        return result

    def update(self, other: "UserConfig"):
        # RHS (other) takes precedence
        self_fields = self.get_fields()
        other_fields = other.get_fields()
        for fieldname, field in self_fields.items():
            setattr(self, fieldname, field + other_fields[fieldname])
        self.subconfigs = list(self.subconfigs) + [other]

    @classmethod
    def read(cls, cli_args: argparse.Namespace | None = None, custom_dirs: list[Path] | None = None):
        config = cls("FINAL")
        paths: list[Path] = [
            platformdirs.user_config_path("slida") / "slida.yaml",
            Path("slida.yaml"),
        ]

        config.update(DefaultUserConfig())

        for custom_dir in custom_dirs or []:
            paths.append(custom_dir / "slida.yaml")

        for path in paths:
            if path.is_file():
                try:
                    config.update(UserConfig.from_file(path))
                except Exception as e:
                    warnings.warn(f"Could not read YAML from {path}: {e}")

        if cli_args:
            config.update(UserConfig.from_cli_args(cli_args))

        return config
