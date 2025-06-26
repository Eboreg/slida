import argparse
import sys

from PySide6.QtWidgets import QApplication

from slida import __version__
from slida.dirscanner import FileOrder
from slida.slideshowview import SlideshowView


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("path", default=".", nargs="+")
    parser.add_argument("--recursive", "-R", action="store_true")
    parser.add_argument("--no-auto", action="store_true", help="Disables auto-advance.")
    parser.add_argument(
        "--interval",
        "-i",
        type=int,
        help="Auto-advance interval, in seconds. Default: 20",
        default=20,
    )
    parser.add_argument(
        "--order",
        "-o",
        type=FileOrder,
        default=FileOrder.RANDOM,
        choices=FileOrder,
        help="Default: random",
    )
    parser.add_argument("--reverse", "-r", action="store_true")
    parser.add_argument(
        "--transition-duration",
        "-td",
        type=float,
        help="In seconds. 0 = no transitions. Default: 0.5",
        default=0.5,
    )

    args = parser.parse_args()

    if args.interval < 1:
        parser.error("Minimum interval is 1 s.")
    if args.interval < args.transition_duration:
        parser.error("Interval cannot be less than transition duration.")

    app = QApplication([])
    app.setApplicationName("Slida v" + __version__)
    slida = SlideshowView(
        args.path,
        recursive=args.recursive,
        interval=args.interval,
        transition_duration=args.transition_duration,
        order=args.order,
        reverse=args.reverse,
        disable_timer=args.no_auto,
    )
    slida.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
