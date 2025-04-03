import random
import sys
from pathlib import Path

from PIL import Image
from PySide6.QtCore import QSize, Qt, QTimer, Slot
from PySide6.QtGui import QKeyEvent, QMouseEvent, QPixmap, QResizeEvent
from PySide6.QtWidgets import QApplication, QGraphicsScene, QGraphicsView

from pyside.animation import TRANSITION_PAIR_CLASSES
from pyside.dirscanner import DirScanner
from pyside.pixmaplist import PixmapList
from pyside.pixmapswidget import AnimPixmapsView
from pyside.toast import Toast


def is_portrait(file: Path | str) -> bool:
    with Image.open(file) as image:
        return image.width / image.height < 0.9


class Slideshow(QGraphicsView):
    files: set[str]
    initial_files: set[str]
    history: list[PixmapList]
    _history_idx: float = 0.0
    interval: int = 20_000
    pixmaps_view: AnimPixmapsView

    def __init__(self, path: str | Path):
        super().__init__()
        self.init_files(str(path))
        self.history = []

        self.toast = Toast(self)

        self.setScene(QGraphicsScene(self))
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.draw()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.on_timeout)
        self.timer.start(self.interval)

    def get_pixmaps(self, history_idx: int) -> PixmapList:
        while len(self.history) <= history_idx:
            self.history.append(PixmapList(self.size()))
        return self.history[history_idx]

    def get_next_pixmap(self, landscape_ok: bool = True, reinited: bool = False) -> QPixmap | None:
        for file in self.files:
            if landscape_ok or is_portrait(file):
                self.files.remove(file)
                pixmap = QPixmap(file)
                return pixmap

        if not reinited:
            self.files = self.initial_files.copy()
            return self.get_next_pixmap(landscape_ok=landscape_ok, reinited=True)

        return None

    def init_files(self, root_path: str):
        scanner = DirScanner(root_path)
        entries = list(scanner.scan())
        random.shuffle(entries)
        self.initial_files = set(entries)
        self.files = self.initial_files.copy()

    def keyReleaseEvent(self, event: QKeyEvent):
        combo = event.keyCombination()
        if Qt.KeyboardModifier.NoModifier in combo.keyboardModifiers():
            if combo.key() in (Qt.Key.Key_Space, Qt.Key.Key_Right):
                self.move(1, True)
            elif combo.key() in (Qt.Key.Key_Backspace, Qt.Key.Key_Left):
                self.move(-1, True)
            elif combo.key() == Qt.Key.Key_F11:
                self.setWindowState(self.windowState() ^ Qt.WindowState.WindowFullScreen)
            elif combo.key() == Qt.Key.Key_Escape and self.isFullScreen():
                self.setWindowState(self.windowState() & ~Qt.WindowState.WindowFullScreen)
            elif combo.key() == Qt.Key.Key_S:
                self.toast.setText("blajja")
                if self.timer.isActive():
                    self.timer.stop()
                else:
                    self.timer.start(self.interval)

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.move(1, True)
        elif event.button() == Qt.MouseButton.RightButton:
            self.move(-1, True)

    @Slot()
    def on_timeout(self):
        self.history = self.history[:int(self._history_idx) + 1]
        self.move(1)

    def resizeEvent(self, event: QResizeEvent):
        self.draw()
        super().resizeEvent(event)

    def setup_pixmaps(self, history_idx: int) -> PixmapList:
        pixmaps = self.get_pixmaps(history_idx)
        pixmaps.set_bounds(self.size())

        while pixmaps.can_fit_portrait():
            pixmap = self.get_next_pixmap(landscape_ok=pixmaps.can_fit_landscape())
            if pixmap:
                pixmaps.add_pixmap(pixmap)
            else:
                break

        return pixmaps

    def draw(self):
        self.scene().setSceneRect(self.viewport().rect())
        self.scene().clear()

        history_idx = int(self._history_idx)

        self.pixmaps_view = AnimPixmapsView()
        self.pixmaps_view.setMinimumSize(self.size())
        self.scene().addWidget(self.pixmaps_view)
        self.pixmaps_view.set_current_pixmaps(self.setup_pixmaps(history_idx))

    def sizeHint(self):
        return QSize(800, 600)

    def move(self, delta: int, restart_timer: bool = False):
        history_idx = int(self._history_idx) + delta

        if history_idx >= 0 and not self.pixmaps_view.is_transitioning():
            self._history_idx = history_idx
            pixmaps = self.setup_pixmaps(history_idx)
            self.pixmaps_view.transition_to(pixmaps, random.choice(TRANSITION_PAIR_CLASSES))

            if restart_timer and self.timer.isActive():
                self.timer.start(self.interval)


def main():
    # topdir = Path("/home/klaatu/.private/Favoriter")
    topdir = Path("/home/klaatu/.private/Favoriter/collage")
    app = QApplication([])
    slida = Slideshow(topdir)
    slida.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
