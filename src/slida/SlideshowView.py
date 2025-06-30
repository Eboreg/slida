import random

import PIL
from PySide6.QtCore import QProcess, QSize, Qt, QTimer, Slot
from PySide6.QtGui import (
    QContextMenuEvent,
    QKeyEvent,
    QMouseEvent,
    QPainter,
    QPixmap,
    QResizeEvent,
)
from PySide6.QtWidgets import QGraphicsScene, QGraphicsView, QMenu

from slida.AnimPixmapsView import AnimPixmapsView
from slida.DirScanner import DirScanner
from slida.PixmapList import PixmapList
from slida.SlidaImage import SlidaImage
from slida.Toast import Toast
from slida.transitions import TRANSITION_PAIRS
from slida.UserConfig import UserConfig
from slida.utils import coerce_between, image_ratio


class SlideshowView(QGraphicsView):
    __config: UserConfig
    __debug_toast: Toast | None = None
    __files: list[str]
    __history_idx: int = 0
    __history: list[list[str]]
    __initial_files: list[str]
    __remaining_time_tmp: int | None = None
    __show_debug_toast: bool = False
    __toasts: list[Toast]

    def __init__(self, path: str | list[str], config: UserConfig | None = None):
        super().__init__()

        self.__config = config or UserConfig()

        entries = DirScanner(path, config=self.__config).list()
        self.__initial_files = entries
        self.__files = entries.copy()

        self.__transition_duration = self.__config.transition_duration
        self.__interval = self.__config.interval
        self.__history = []
        self.__toasts = []

        if self.__show_debug_toast:
            self.__debug_toast = self.create_toast(None, True)

        self.__help_toast = self.create_toast(None, True)
        self.__help_toast.set_text(
            "[Space]/[->] Move forward  |  [Backspace]/[<-] Move backward  |  [F11] Toggle fullscreen\n" + \
            "[Esc] Leave fullscreen  |  [?] Toggle help  |  [+] Increase interval  |  [-] Decrease interval\n" + \
            "[S] Toggle auto-advance"
        )

        self.__pixmaps_view = AnimPixmapsView()

        self.setScene(QGraphicsScene(self))
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.DefaultContextMenu)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scene().addWidget(self.__pixmaps_view)

        if self.__show_debug_toast:
            debug_timer = QTimer(self, interval=200)
            debug_timer.timeout.connect(self.__on_debug_timeout)
            debug_timer.start()

        self.__timer = QTimer(self, interval=self.real_interval_ms)
        self.__timer.timeout.connect(self.__on_timeout)

        if not self.__config.no_auto:
            self.__timer.start()

        self.draw()

    @property
    def real_interval_ms(self) -> int:
        return max(int((self.__interval - self.__transition_duration) * 1000), 0)

    def contextMenuEvent(self, event: QContextMenuEvent):
        menu = QMenu(self)
        timer_was_active = self.pause_slideshow()
        files = self.__get_history_entry(self.__history_idx)

        def on_hide():
            if timer_was_active:
                self.unpause_slideshow()

        if self.__history_idx > 0:
            menu.addAction("Previous", lambda: self.move_by(-1))
        if timer_was_active:
            menu.addAction("Stop slideshow", lambda: self.pause_slideshow(True))
        else:
            menu.addAction("Start slideshow", lambda: self.unpause_slideshow(True))
        menu.addAction("Exit", self.close)

        menu.addSeparator()

        for path in files:
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

    def create_toast(self, timeout: int | None = 3000, keep: bool = False):
        toast = Toast(self, timeout)
        self.__toasts.append(toast)

        def on_hidden():
            if not keep:
                self.__toasts.remove(toast)
            self.__place_toasts()

        def on_resized():
            self.__place_toasts()

        def on_shown():
            self.__place_toasts()

        toast.hidden.connect(on_hidden)
        toast.shown.connect(on_shown)
        toast.resized.connect(on_resized)
        toast.setFixedWidth(self.width())

        return toast

    def draw(self):
        self.__pixmaps_view.set_current_pixmaps(self.__setup_pixmaps(self.__history_idx))

    def keyReleaseEvent(self, event: QKeyEvent):
        combo = event.keyCombination()

        if combo.keyboardModifiers() & Qt.KeyboardModifier.ControlModifier:
            if combo.key() == Qt.Key.Key_Plus:
                self.nudge_transition_duration(0.1)
            elif combo.key() == Qt.Key.Key_Minus:
                self.nudge_transition_duration(-0.1)
        else:
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
                self.nudge_interval(1)
            elif combo.key() == Qt.Key.Key_Minus:
                self.nudge_interval(-1)
            elif combo.key() == Qt.Key.Key_Question:
                self.toggle_help_toast()

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.move_by(1)

    def move_by(self, delta: int):
        history_idx = self.__history_idx + delta
        self.__remaining_time_tmp = None

        if history_idx >= 0 and not self.__pixmaps_view.is_transitioning:
            self.__history_idx = history_idx
            pixmaps = self.__setup_pixmaps(history_idx)

            self.__pixmaps_view.transition_to(
                pixmaps=pixmaps,
                transition_pair_type=self.__get_next_transition_pair_type(),
                transition_duration=self.__transition_duration
            )

            if self.__timer.isActive():
                self.__timer.start(self.real_interval_ms)

    def nudge_interval(self, delta: int):
        if self.__interval + delta > 0 and self.__interval + delta - self.__transition_duration >= 0:
            self.__interval += delta
            self.show_toast(f"Interval: {self.__interval} s")
            if self.__timer.isActive():
                self.__timer.start(max(self.__timer.remainingTime() + (delta * 1000), 0))

    def nudge_transition_duration(self, delta: float):
        new_value = round(coerce_between(self.__transition_duration + delta, 0.0, self.__interval), 1)
        if new_value != self.__transition_duration:
            self.__transition_duration = new_value
            self.show_toast(f"Transition duration: {self.__transition_duration} s")

    def pause_slideshow(self, show_toast: bool = False) -> bool:
        if self.__timer.isActive():
            self.__remaining_time_tmp = self.__timer.remainingTime()
            self.__timer.stop()
            if show_toast:
                self.show_toast("Slideshow paused")
            return True
        return False

    def resizeEvent(self, event: QResizeEvent):
        rect = self.viewport().rect()
        self.scene().setSceneRect(rect)
        self.__pixmaps_view.setFixedSize(rect.size())
        for toast in self.__toasts:
            toast.setFixedWidth(rect.width())
        self.__place_toasts()
        self.draw()
        super().resizeEvent(event)

    def show_toast(self, text: str, timeout: int | None = 3000, keep: bool = False):
        toast = self.create_toast(timeout, keep)
        toast.set_text(text)
        toast.show()

    def sizeHint(self) -> QSize:
        return QSize(800, 600)

    def toggle_help_toast(self):
        if self.__help_toast.isVisible():
            self.__help_toast.hide()
        else:
            self.__help_toast.show()

    def toggle_slideshow(self):
        if self.__timer.isActive():
            self.pause_slideshow(True)
        else:
            self.unpause_slideshow(True)

    def unpause_slideshow(self, show_toast: bool = False):
        if not self.__timer.isActive():
            if self.__remaining_time_tmp:
                self.__timer.start(self.__remaining_time_tmp)
            else:
                if self.__remaining_time_tmp == 0:
                    self.move_by(1)
                self.__timer.start()
            if show_toast:
                self.show_toast("Slideshow started")

    def __get_history_entry(self, history_idx: int) -> list[str]:
        while len(self.__history) <= history_idx:
            self.__history.append([])
        return self.__history[history_idx]

    def __get_next_image(self, max_ratio: float | None, reinited: bool = False) -> SlidaImage | None:
        files = self.__files.copy()

        for file in files:
            try:
                if max_ratio is None or image_ratio(file) <= max_ratio:
                    return SlidaImage(QPixmap(file), file)
            except (PIL.UnidentifiedImageError, ValueError):
                self.__initial_files.remove(file)
            finally:
                self.__files.remove(file)

        if not reinited:
            self.__files = self.__initial_files.copy()
            return self.__get_next_image(max_ratio=max_ratio, reinited=True)

        return None

    def __get_next_transition_pair_type(self):
        pairs = self.__get_transition_pair_types()
        if not pairs:
            return None
        return random.choice(pairs)

    def __get_no_image_pixmap(self):
        size = self.size()
        image = QPixmap(size)
        image.fill(Qt.GlobalColor.black)
        painter = QPainter(image)
        painter.setPen(Qt.GlobalColor.white)
        font = painter.font()
        font.setPixelSize(int(size.width() / 20))
        painter.setFont(font)
        painter.drawText(image.rect(), Qt.AlignmentFlag.AlignCenter, "No images found!")
        return image

    def __get_transition_pair_types(self):
        pairs = TRANSITION_PAIRS

        if self.__config.transitions is not None:
            names = {p.name for p in pairs}
            include = set(self.__config.transitions.get("include", names))
            exclude = set(self.__config.transitions.get("exclude", []))

            if "all" not in include:
                names &= include
                names -= exclude
                pairs = [p for p in pairs if p.name in names]

        return pairs

    @Slot()
    def __on_debug_timeout(self):
        if self.__debug_toast:
            self.__debug_toast.set_text(
                f"timer.isActive={self.__timer.isActive()}, timer.remainingTime={self.__timer.remainingTime()}"
            )
            self.__debug_toast.show()

    @Slot()
    def __on_timeout(self):
        self.__history = self.__history[:self.__history_idx + 1]
        self.move_by(1)

    def __open_ext(self, program: str, path: str):
        process = QProcess(self)
        process.setProgram(program)
        process.setArguments([path])
        process.startDetached()

    def __place_toasts(self):
        offset = 0
        for toast in reversed(self.__toasts):
            if not toast.isHidden():
                toast.move(0, offset)
                offset += toast.label.height()

    def __setup_pixmaps(self, history_idx: int) -> PixmapList:
        files = self.__get_history_entry(history_idx)
        pixmaps = PixmapList(self.size().toSizeF())
        filenames = iter(files)

        while self.__initial_files and (len(pixmaps) == 0 or not self.__config.no_tiling) and pixmaps.can_fit_more():
            file = next(filenames, None)
            if file:
                image = SlidaImage(QPixmap(file), file)
            else:
                image = self.__get_next_image(max_ratio=pixmaps.fitting_image_max_ratio())
                if image:
                    files.append(image.filename)
            if image:
                pixmaps.add_image(image)
            else:
                if not self.__initial_files:
                    pixmaps.add_image(SlidaImage(self.__get_no_image_pixmap()))
                break

        return pixmaps
