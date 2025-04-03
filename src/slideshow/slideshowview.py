import random
from pathlib import Path

from PySide6.QtCore import QSize, Qt, QTimer, Slot
from PySide6.QtGui import QKeyEvent, QMouseEvent, QPixmap, QResizeEvent
from PySide6.QtWidgets import QGraphicsScene, QGraphicsView

from slideshow.animpixmapsview import AnimPixmapsView
from slideshow.dirscanner import DirScanner
from slideshow.pixmaplist import PixmapList
from slideshow.toast import Toast
from slideshow.transitions import TRANSITION_PAIR_CLASSES
from slideshow.utils import is_portrait


class SlideshowView(QGraphicsView):
    files: set[str]
    initial_files: set[str]
    history: list[PixmapList]
    history_idx: int = 0
    pixmaps_view: AnimPixmapsView
    interval: int
    real_interval: int
    transition_duration: int
    timer_explicitly_stopped: bool = False

    def __init__(
        self,
        path: str | Path,
        recursive: bool = False,
        interval: int = 20_000,
        transition_duration: int = 600
    ):
        super().__init__()
        self.init_files(str(path), recursive=recursive)
        self.transition_duration = transition_duration
        self.interval = interval
        self.history = []

        self.toast = Toast(self)
        self.pixmaps_view = AnimPixmapsView(transition_duration=self.transition_duration)

        self.setScene(QGraphicsScene(self))
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.scene().addWidget(self.pixmaps_view)
        self.draw()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.on_timeout)
        self.set_durations(interval, transition_duration)

    def draw(self):
        self.pixmaps_view.set_current_pixmaps(self.setup_pixmaps(self.history_idx))

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

    def get_pixmaps(self, history_idx: int) -> PixmapList:
        while len(self.history) <= history_idx:
            self.history.append(PixmapList(self.size()))
        return self.history[history_idx]

    def init_files(self, root_path: str, recursive: bool = False):
        scanner = DirScanner(root_path, recursive=recursive)
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
                    self.timer_explicitly_stopped = True
                    self.timer.stop()
                else:
                    self.timer_explicitly_stopped = False
                    self.timer.start()

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.move(1, True)
        elif event.button() == Qt.MouseButton.RightButton:
            self.move(-1, True)

    def move(self, delta: int, restart_timer: bool = False):
        history_idx = self.history_idx + delta

        if history_idx >= 0 and not self.pixmaps_view.is_transitioning():
            self.history_idx = history_idx
            pixmaps = self.setup_pixmaps(history_idx)
            self.pixmaps_view.transition_to(pixmaps, random.choice(TRANSITION_PAIR_CLASSES))

            if restart_timer and self.timer.isActive():
                self.timer.start()

    @Slot()
    def on_timeout(self):
        self.history = self.history[:self.history_idx + 1]
        self.move(1)

    def resizeEvent(self, event: QResizeEvent):
        rect = self.viewport().rect()
        self.scene().setSceneRect(rect)
        self.pixmaps_view.setFixedSize(rect.size())
        self.toast.setFixedWidth(rect.width())
        self.draw()
        super().resizeEvent(event)

    def set_durations(self, interval: int, transition: int):
        self.interval = interval
        self.transition_duration = transition
        self.real_interval = max(interval - transition, 0)
        self.pixmaps_view.set_transition_duration(transition)

        if interval > 0:
            self.timer.setInterval(self.real_interval)
            if not self.timer.isActive() and not self.timer_explicitly_stopped:
                self.timer.start()
        else:
            self.timer.stop()

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

    def sizeHint(self):
        return QSize(800, 600)
