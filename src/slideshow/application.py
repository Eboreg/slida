import argparse
import sys

from PySide6.QtWidgets import QApplication

from slideshow.slideshowview import SlideshowView


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("path", default=".", nargs="?")
    parser.add_argument("--recursive", "-r", action="store_true")
    parser.add_argument("--interval", "-i", type=int, help="In ms. 0 = disable auto-advance.", default=20_000)
    parser.add_argument("--transition-duration", "-td", type=int, help="In ms. 0 = no transitions.", default=600)
    args = parser.parse_args()
    app = QApplication([])
    slida = SlideshowView(
        args.path,
        recursive=args.recursive,
        interval=args.interval,
        transition_duration=args.transition_duration,
    )
    slida.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
