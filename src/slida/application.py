import argparse
import sys
from pathlib import Path

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from slida import __version__
from slida.DirScanner import FileOrder
from slida.SlideshowView import SlideshowView
from slida.UserConfig import CombinedUserConfig, DefaultUserConfig
from slida.transitions import TRANSITION_PAIRS


def main():
    parser = argparse.ArgumentParser()
    default_config = DefaultUserConfig()

    parser.add_argument("path", default=".", nargs="*")
    parser.add_argument(
        "--interval",
        "-i",
        type=int,
        help=f"Auto-advance interval, in seconds (default: {default_config.interval.value})",
    )
    parser.add_argument(
        "--order",
        "-o",
        type=FileOrder,
        choices=FileOrder,
        help=f"Default: {default_config.order.value}",
    )
    parser.add_argument(
        "--transition-duration",
        "-td",
        type=float,
        help=f"In seconds; 0 = no transitions (default: {default_config.transition_duration.value})",
    )
    parser.add_argument("--transitions", nargs="+", help="One or more transitions to use (default: use them all)")
    parser.add_argument("--exclude-transitions", nargs="+", help="One or more transitions NOT to use")
    parser.add_argument("--list-transitions", action="store_true", help="List available transitions and exit")
    parser.add_argument("--print-config", action="store_true", help="Also print debug info about the current config")

    auto = parser.add_mutually_exclusive_group()
    auto.add_argument(
        "--auto",
        action="store_const",
        help="Enable auto-advance" + (" (default)" if default_config.auto.value else ""),
        const=True,
    )
    auto.add_argument(
        "--no-auto",
        action="store_const",
        help="Disable auto-advance" + (" (default)" if not default_config.auto.value else ""),
        const=False,
        dest="auto",
    )

    recursive = parser.add_mutually_exclusive_group()
    recursive.add_argument(
        "--recursive",
        "-R",
        action="store_const",
        const=True,
        help="Iterate through subdirectories" + (" (default)" if default_config.recursive.value else ""),
    )
    recursive.add_argument(
        "--no-recursive",
        action="store_const",
        const=False,
        dest="recursive",
        help="Do not iterate through subdirectories" + (" (default)" if not default_config.recursive.value else ""),
    )

    reverse = parser.add_mutually_exclusive_group()
    reverse.add_argument(
        "--reverse",
        "-r",
        action="store_const",
        const=True,
        help="Reverse the image order" + (" (default)" if default_config.reverse.value else ""),
    )
    reverse.add_argument(
        "--no-reverse",
        action="store_const",
        const=False,
        dest="reverse",
        help="Do not reverse the image order" + (" (default)" if not default_config.reverse.value else ""),
    )

    tiling = parser.add_mutually_exclusive_group()
    tiling.add_argument(
        "--tiling",
        action="store_const",
        const=True,
        help="Tile images horizontally" + (" (default)" if default_config.tiling.value else ""),
    )
    tiling.add_argument(
        "--no-tiling",
        action="store_const",
        const=False,
        dest="tiling",
        help="Do not tile images horizontally" + (" (default)" if not default_config.tiling.value else ""),
    )

    args = parser.parse_args()
    custom_dirs = [d for d in [Path(p) for p in args.path] if d.is_dir()]

    if args.list_transitions:
        transition_names = sorted(p.name for p in TRANSITION_PAIRS)
        print("Available transitions:")
        for name in transition_names:
            print(f"  {name}")
        sys.exit()

    try:
        config = CombinedUserConfig.read(args, custom_dirs)
        config.check()
    except Exception as e:
        parser.error(str(e))

    if args.print_config:
        print(config)

    app = QApplication([])
    app.setWindowIcon(QIcon(str(Path(__file__).parent / "slida.png")))
    app.setApplicationName("Slida v" + __version__)
    slida = SlideshowView(args.path, config=config)
    slida.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
