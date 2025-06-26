import random
from pathlib import Path

from PySide6.QtCore import QProcess, QSize, Qt, QTimer, Slot
from PySide6.QtGui import (
    QContextMenuEvent,
    QKeyEvent,
    QMouseEvent,
    QResizeEvent,
)
from PySide6.QtWidgets import QGraphicsScene, QGraphicsView, QMenu

from slideshow.animpixmapsview import AnimPixmapsView
from slideshow.dirscanner import DirScanner, FileOrder
from slideshow.pixmaplist import PixmapList
from slideshow.qimage import QImage
from slideshow.toast import Toast
from slideshow.transitions import TRANSITION_PAIR_CLASSES
from slideshow.utils import image_ratio


class HistoryEntry:
    files: list[str]

    def __init__(self):
        self.files = []


class SlideshowView(QGraphicsView):
    debug_toast: Toast | None = None
    files: list[str]
    history_idx: int = 0
    history: list[HistoryEntry]
    initial_files: list[str]
    remaining_time_tmp: int | None = None
    show_debug_toast: bool = False
    toasts: list[Toast]

    def __init__(
        self,
        path: str | Path,
        recursive: bool = False,
        interval: int = 20,
        transition_duration: float = 0.5,
        order: FileOrder = FileOrder.RANDOM,
        reverse: bool = False,
        disable_timer: bool = False,
    ):
        super().__init__()
        self.__init_files(str(path), recursive=recursive, order=order, reverse=reverse)
        self.transition_duration = transition_duration
        self.interval = interval
        self.disable_timer = disable_timer
        self.history = []
        self.toasts = []

        if self.show_debug_toast:
            self.debug_toast = self.show_toast("", None)
        self.pixmaps_view = AnimPixmapsView(transition_duration=self.transition_duration)

        self.setScene(QGraphicsScene(self))
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.DefaultContextMenu)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.scene().addWidget(self.pixmaps_view)
        self.draw()

        if self.show_debug_toast:
            self.debug_timer = QTimer(self, interval=200)
            self.debug_timer.timeout.connect(self.__on_debug_timeout)
            self.debug_timer.start()
        self.timer = QTimer(self, interval=self.real_interval_ms)
        self.timer.timeout.connect(self.__on_timeout)
        self.pixmaps_view.set_transition_duration(transition_duration)

        if not disable_timer:
            self.timer.start()

    @property
    def real_interval_ms(self) -> int:
        return max(int((self.interval - self.transition_duration) * 1000), 0)

    def change_interval(self, delta: int):
        if self.interval + delta > 0 and self.interval + delta - self.transition_duration >= 0:
            self.interval += delta
            self.show_toast(f"Interval: {self.interval} s")
            if self.timer.isActive():
                self.timer.start(max(self.timer.remainingTime() + (delta * 1000), 0))

    def contextMenuEvent(self, event: QContextMenuEvent):
        menu = QMenu(self)
        timer_was_active = self.pause_slideshow()

        def on_hide():
            if timer_was_active:
                self.unpause_slideshow()

        menu.addAction("Previous", lambda: self.move_by(-1))
        if timer_was_active:
            menu.addAction("Stop slideshow", lambda: self.pause_slideshow(True))
        else:
            menu.addAction("Start slideshow", lambda: self.unpause_slideshow(True))

        menu.addSeparator()

        for path in self.__get_current_filenames():
            if "/" not in path:
                path = f"./{path}"
            directory, basename = path.rsplit("/", 1)
            menu.addSection(basename)
            gimp_action = menu.addAction("Open in GIMP")
            gimp_action.triggered.connect(lambda _, p=path: self.__open_ext("/usr/bin/gimp", p))
            gwenview_action = menu.addAction("Open in Gwenview")
            gwenview_action.triggered.connect(lambda _, p=path: self.__open_ext("/usr/bin/gwenview", p))
            fm_action = menu.addAction("Open parent dir")
            fm_action.triggered.connect(lambda _, p=directory: self.__open_ext("/usr/bin/xdg-open", p))

        menu.aboutToHide.connect(on_hide)
        menu.exec(event.globalPos())

    def draw(self):
        self.pixmaps_view.set_current_pixmaps(self.__setup_pixmaps(self.history_idx))

    def keyReleaseEvent(self, event: QKeyEvent):
        combo = event.keyCombination()
        if Qt.KeyboardModifier.NoModifier in combo.keyboardModifiers():
            if combo.key() in (Qt.Key.Key_Space, Qt.Key.Key_Right):
                self.move_by(1)
            elif combo.key() in (Qt.Key.Key_Backspace, Qt.Key.Key_Left):
                self.move_by(-1)
            elif combo.key() == Qt.Key.Key_F11:
                self.setWindowState(self.windowState() ^ Qt.WindowState.WindowFullScreen)
            elif combo.key() == Qt.Key.Key_Escape and self.isFullScreen():
                self.setWindowState(self.windowState() & ~Qt.WindowState.WindowFullScreen)
            elif combo.key() == Qt.Key.Key_S:
                self.toggle_slideshow()
            elif combo.key() == Qt.Key.Key_Plus:
                self.change_interval(1)
            elif combo.key() == Qt.Key.Key_Minus:
                self.change_interval(-1)

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.move_by(1)

    def move_by(self, delta: int):
        history_idx = self.history_idx + delta
        self.remaining_time_tmp = None

        if history_idx >= 0 and not self.pixmaps_view.is_transitioning():
            self.history_idx = history_idx
            pixmaps = self.__setup_pixmaps(history_idx)
            self.pixmaps_view.transition_to(pixmaps, random.choice(TRANSITION_PAIR_CLASSES))

            if self.timer.isActive():
                self.timer.start(self.real_interval_ms)

    def pause_slideshow(self, show_toast: bool = False) -> bool:
        if self.timer.isActive():
            self.remaining_time_tmp = self.timer.remainingTime()
            self.timer.stop()
            if show_toast:
                self.show_toast("Slideshow paused")
            return True
        return False

    def resizeEvent(self, event: QResizeEvent):
        rect = self.viewport().rect()
        self.scene().setSceneRect(rect)
        self.pixmaps_view.setFixedSize(rect.size())
        for toast in self.toasts:
            toast.setFixedWidth(rect.width())
        self.__place_toasts()
        self.draw()
        super().resizeEvent(event)

    def show_toast(self, text: str, timeout: int | None = 3000):
        toast = Toast(self, timeout)
        self.toasts.append(toast)

        def on_hidden():
            self.toasts.remove(toast)
            self.__place_toasts()

        def on_resized():
            self.__place_toasts()

        def on_shown():
            self.__place_toasts()

        toast.hidden.connect(on_hidden)
        toast.shown.connect(on_shown)
        toast.resized.connect(on_resized)
        toast.setFixedWidth(self.width())
        toast.set_text(text)

        return toast

    def sizeHint(self) -> QSize:
        return QSize(800, 600)

    def toggle_slideshow(self):
        if self.timer.isActive():
            self.pause_slideshow(True)
        else:
            self.unpause_slideshow(True)

    def unpause_slideshow(self, show_toast: bool = False):
        if not self.timer.isActive():
            if self.remaining_time_tmp:
                self.timer.start(self.remaining_time_tmp)
            else:
                if self.remaining_time_tmp == 0:
                    self.move_by(1)
                self.timer.start()
            if show_toast:
                self.show_toast("Slideshow started")

    def __get_current_filenames(self) -> list[str]:
        entry = self.__get_history_entry(self.history_idx)
        return entry.files

    def __get_history_entry(self, history_idx: int) -> HistoryEntry:
        while len(self.history) <= history_idx:
            self.history.append(HistoryEntry())
        return self.history[history_idx]

    def __get_next_image(self, max_ratio: float | None, reinited: bool = False) -> QImage | None:
        for file in self.files:
            if max_ratio is None or image_ratio(file) <= max_ratio:
                self.files.remove(file)
                return QImage(file)

        if not reinited:
            self.files = self.initial_files.copy()
            return self.__get_next_image(max_ratio=max_ratio, reinited=True)

        return None

    def __init_files(
        self,
        root_path: str,
        recursive: bool = False,
        order: FileOrder = FileOrder.NAME,
        reverse: bool = False,
    ):
        scanner = DirScanner(root_path, recursive=recursive)
        entries = scanner.list(order=order, reverse=reverse)
        self.initial_files = entries
        self.files = self.initial_files.copy()

    @Slot()
    def __on_debug_timeout(self):
        if self.debug_toast:
            self.debug_toast.set_text(
                f"timer.isActive={self.timer.isActive()}, timer.remainingTime={self.timer.remainingTime()}"
            )

    @Slot()
    def __on_timeout(self):
        self.history = self.history[:self.history_idx + 1]
        self.move_by(1)

    def __open_ext(self, program: str, path: str):
        process = QProcess(self)
        process.setProgram(program)
        process.setArguments([path])
        process.startDetached()

    def __place_toasts(self):
        offset = 0
        for toast in reversed(self.toasts):
            if not toast.isHidden():
                toast.move(0, offset)
                offset += toast.label.height()

    def __setup_pixmaps(self, history_idx: int) -> PixmapList:
        entry = self.__get_history_entry(history_idx)
        pixmaps = PixmapList(self.size())
        filenames = iter(entry.files)

        while pixmaps.can_fit_more():
            file = next(filenames, None)
            if file:
                image = QImage(file)
            else:
                image = self.__get_next_image(max_ratio=pixmaps.fitting_image_max_ratio())
                if image:
                    entry.files.append(image.filename)
            if image:
                pixmaps.add_image(image)
            else:
                break

        return pixmaps
