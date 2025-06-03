import random
from pathlib import Path

from PySide6.QtCore import QSize, Qt, QTimer, Slot, QProcess
from PySide6.QtGui import QKeyEvent, QMouseEvent, QResizeEvent, QContextMenuEvent
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
    files: list[str]
    initial_files: list[str]
    history: list[HistoryEntry]
    history_idx: int = 0
    remaining_time_tmp: int | None = None

    def __init__(
        self,
        path: str | Path,
        recursive: bool = False,
        interval: int = 20,
        transition_duration: float = 0.5,
        order: FileOrder = FileOrder.NAME,
        reverse: bool = False,
        disable_timer: bool = False,
    ):
        super().__init__()
        self.init_files(str(path), recursive=recursive, order=order, reverse=reverse)
        self.transition_duration = transition_duration
        self.interval = interval
        self.disable_timer = disable_timer
        self.history = []

        self.toast = Toast(self)
        self.pixmaps_view = AnimPixmapsView(transition_duration=self.transition_duration)

        self.setScene(QGraphicsScene(self))
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.DefaultContextMenu)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.scene().addWidget(self.pixmaps_view)
        self.draw()

        self.timer = QTimer(self, interval=self.real_interval_ms)
        self.timer.timeout.connect(self.on_timeout)
        self.pixmaps_view.set_transition_duration(transition_duration)

        if not disable_timer:
            self.timer.start()

    @property
    def real_interval_ms(self) -> int:
        return max(int((self.interval - self.transition_duration) * 1000), 0)

    def change_interval(self, delta: int):
        if self.interval + delta > 0 and self.interval + delta - self.transition_duration >= 0:
            timer_was_active = self.pause_slideshow()
            self.interval += delta
            if self.remaining_time_tmp is not None:
                self.remaining_time_tmp = max(self.remaining_time_tmp + delta, 0)
            self.timer.setInterval(self.real_interval_ms)
            self.toast.set_text(f"Interval: {self.interval} s")
            if timer_was_active:
                self.unpause_slideshow()

    def pause_slideshow(self, show_toast: bool = False) -> bool:
        if self.timer.isActive():
            self.remaining_time_tmp = self.timer.remainingTime()
            self.timer.stop()
            if show_toast:
                self.toast.set_text("Slideshow stopped")
            return True
        return False

    def unpause_slideshow(self, show_toast: bool = False):
        def move_and_restart():
            self.timer.start()
            self.move(1, True)

        if not self.timer.isActive():
            if self.remaining_time_tmp:
                oneshot = QTimer(self, singleShot=True, interval=self.remaining_time_tmp)
                oneshot.timeout.connect(move_and_restart)
                oneshot.start()
            else:
                if self.remaining_time_tmp == 0:
                    self.move(1, True)
                self.timer.start()
            if show_toast:
                self.toast.set_text("Slideshow started")

    def contextMenuEvent(self, event: QContextMenuEvent):
        menu = QMenu(self)
        timer_was_active = self.pause_slideshow()

        def on_hide():
            if timer_was_active:
                self.unpause_slideshow()

        for path in self.get_current_filenames():
            if "/" not in path:
                path = f"./{path}"
            directory, basename = path.rsplit("/", 1)
            menu.addSection(basename)
            gimp_action = menu.addAction("Open in GIMP")
            gimp_action.triggered.connect(lambda _, p=path: self.open_ext("/usr/bin/gimp", p))
            gwenview_action = menu.addAction("Open in Gwenview")
            gwenview_action.triggered.connect(lambda _, p=path: self.open_ext("/usr/bin/gwenview", p))
            fm_action = menu.addAction("Open parent dir")
            fm_action.triggered.connect(lambda _, p=directory: self.open_ext("/usr/bin/xdg-open", p))

        menu.addSeparator()

        if timer_was_active:
            menu.addAction("Stop slideshow", lambda: self.pause_slideshow(True))
        else:
            menu.addAction("Start slideshow", lambda: self.unpause_slideshow(True))

        menu.aboutToHide.connect(on_hide)
        menu.exec(event.globalPos())

    def open_ext(self, program: str, path: str):
        process = QProcess(self)
        process.setProgram(program)
        process.setArguments([path])
        process.startDetached()

    def draw(self):
        self.pixmaps_view.set_current_pixmaps(self.setup_pixmaps(self.history_idx))

    def get_current_filenames(self) -> list[str]:
        entry = self.get_history_entry(self.history_idx)
        return entry.files

    def get_next_image(self, max_ratio: float | None, reinited: bool = False) -> QImage | None:
        for file in self.files:
            if max_ratio is None or image_ratio(file) <= max_ratio:
                self.files.remove(file)
                return QImage(file)

        if not reinited:
            self.files = self.initial_files.copy()
            return self.get_next_image(max_ratio=max_ratio, reinited=True)

        return None

    def get_history_entry(self, history_idx: int) -> HistoryEntry:
        while len(self.history) <= history_idx:
            self.history.append(HistoryEntry())
        return self.history[history_idx]

    def init_files(
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
                self.toggle_slideshow()
            elif combo.key() == Qt.Key.Key_Plus:
                self.change_interval(1)
            elif combo.key() == Qt.Key.Key_Minus:
                self.change_interval(-1)

    def toggle_slideshow(self):
        if self.timer.isActive():
            self.pause_slideshow(True)
        else:
            self.unpause_slideshow(True)

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.move(1, True)

    def move(self, delta: int, restart_timer: bool = False): # type: ignore
        history_idx = self.history_idx + delta
        self.remaining_time_tmp = None

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

    def setup_pixmaps(self, history_idx: int) -> PixmapList:
        entry = self.get_history_entry(history_idx)
        pixmaps = PixmapList(self.size())
        filenames = iter(entry.files)

        while pixmaps.can_fit_more():
            file = next(filenames, None)
            if file:
                image = QImage(file)
            else:
                image = self.get_next_image(max_ratio=pixmaps.fitting_image_max_ratio())
                if image:
                    entry.files.append(image.filename)
            if image:
                pixmaps.add_image(image)
            else:
                break

        return pixmaps

    def sizeHint(self) -> QSize:
        return QSize(800, 600)
