import argparse
import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

from slida import __version__
from slida.DirScanner import FileOrder
from slida.SlideshowView import SlideshowView
from slida.utils import read_user_config


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("path", default=".", nargs="+")
    parser.add_argument("--recursive", "-R", action="store_const", const=True)
    parser.add_argument("--no-auto", action="store_const", help="Disables auto-advance.", const=True)
    parser.add_argument(
        "--interval",
        "-i",
        type=int,
        help="Auto-advance interval, in seconds. Default: 20",
    )
    parser.add_argument(
        "--order",
        "-o",
        type=FileOrder,
        choices=FileOrder,
        help="Default: random",
    )
    parser.add_argument("--reverse", "-r", action="store_const", const=True)
    parser.add_argument(
        "--transition-duration",
        "-td",
        type=float,
        help="In seconds. 0 = no transitions. Default: 0.5",
    )

    args = parser.parse_args()
    custom_dirs = [d for d in [Path(p) for p in args.path] if d.is_dir()]

    try:
        config = read_user_config(args, custom_dirs)
        config.check()
    except Exception as e:
        parser.error(str(e))

    app = QApplication([])
    app.setApplicationName("Slida v" + __version__)
    slida = SlideshowView(args.path, config=config)
    slida.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
