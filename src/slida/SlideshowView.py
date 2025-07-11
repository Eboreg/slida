import math
import random

from PySide6.QtCore import QPointF, QProcess, QRectF, QSize, Qt, QTimer, Slot
from PySide6.QtGui import (
    QContextMenuEvent,
    QKeyEvent,
    QMouseEvent,
    QResizeEvent,
    QWheelEvent,
)
from PySide6.QtWidgets import QGraphicsScene, QGraphicsView, QMenu, QWidget
from klaatu_python.utils import coerce_between

from slida.AnimPixmapsView import AnimPixmapsView
from slida.DirScanner import DirScanner
from slida.ImageFileList import ImageFileList
from slida.Toast import Toast
from slida.debug import add_live_object, print_live_objects, remove_live_object
from slida.transitions import TRANSITION_PAIRS
from slida.UserConfig import UserConfig


class DragTracker:
    def __init__(self, start_pos: QPointF, timestamp: int):
        self.start_pos = start_pos
        self.current_pos = start_pos
        self.latest_diff = QPointF()
        self.total_distance = 0.0
        self.timestamp = timestamp

    def update(self, current_pos: QPointF):
        self.latest_diff = current_pos - self.current_pos
        print("current_pos", current_pos, "self.current_pos", self.current_pos, "self.latest_diff", self.latest_diff)
        self.current_pos = current_pos
        self.total_distance += math.sqrt(pow(self.latest_diff.x(), 2) + pow(self.latest_diff.y(), 2))


class SlideshowView(QGraphicsView):
    __debug_toast: Toast | None = None
    __drag_tracker: DragTracker | None = None
    __history_idx: int = 0
    __remaining_time_tmp: int | None = None
    __show_debug_toast: bool = False
    __wheel_delta: int = 0
    __zoom: int = 0

    __config: UserConfig
    __help_toast: Toast
    __image_files: ImageFileList
    __interval: int
    __pixmaps_view: AnimPixmapsView
    __timer: QTimer
    __toasts: list[Toast]
    __transition_duration: float

    def __init__(self, path: str | list[str], config: UserConfig | None = None, parent: QWidget | None = None):
        super().__init__(parent)

        self.__config = config or UserConfig()
        self.__transition_duration = self.__config.transition_duration.value
        self.__interval = self.__config.interval.value
        self.__toasts = []

        add_live_object(id(self), self.__class__.__name__)

        self.__image_files = ImageFileList(DirScanner(path, config=self.__config).list())

        if self.__show_debug_toast:
            self.__debug_toast = self.create_toast(None, True)

        self.__help_toast = self.create_toast(None, True)
        self.__help_toast.set_text(
            "[Space]/[->] Move forward  |  [Backspace]/[<-] Move backward  |  [F11] Toggle fullscreen\n" + \
            "[Esc] Leave fullscreen  |  [?] Toggle help  |  [+] Increase interval  |  [-] Decrease interval\n" + \
            "[S] Toggle auto-advance"
        )

        self.__pixmaps_view = AnimPixmapsView()
        scene = QGraphicsScene(self)

        self.setScene(scene)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.DefaultContextMenu)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        # self.setMouseTracking(False)
        scene.addWidget(self.__pixmaps_view)

        if self.__show_debug_toast:
            debug_timer = QTimer(self, interval=200)
            debug_timer.timeout.connect(self.__on_debug_timeout)
            debug_timer.start()

        self.__timer = QTimer(self, interval=self.real_interval_ms)
        self.__timer.timeout.connect(self.__on_timeout)

        if self.__config.auto.value:
            self.__timer.start()

        self.draw()

    @property
    def real_interval_ms(self) -> int:
        return max(int((self.__interval - self.__transition_duration) * 1000), 0)

    @property
    def zoom_percent(self) -> int:
        return int(pow(1.4, self.__zoom) * 100)

    def contextMenuEvent(self, event: QContextMenuEvent):
        menu = QMenu(self)
        timer_was_active = self.pause_slideshow()

        def on_hide():
            if timer_was_active:
                self.unpause_slideshow()

        if self.__history_idx > 0:
            menu.addAction("Previous", lambda: self.move_by(-1))
        if timer_was_active:
            menu.addAction("Stop slideshow", lambda: self.pause_slideshow(True))
        else:
            menu.addAction("Start slideshow", lambda: self.unpause_slideshow(True))

        menu.addAction("Toggle fullscreen", self.toggle_fullscreen)
        menu.addAction("Exit", self.close)

        menu.addSeparator()

        for path in self.__pixmaps_view.get_current_filenames():
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

        @Slot()
        def on_hidden():
            if not keep:
                self.__toasts.remove(toast)
                toast.hidden.disconnect()
                toast.shown.disconnect()
                toast.resized.disconnect()
                toast.deleteLater()
            self.__place_toasts()

        @Slot()
        def on_resized():
            self.__place_toasts()

        @Slot()
        def on_shown():
            self.__place_toasts()

        toast.hidden.connect(on_hidden)
        toast.shown.connect(on_shown)
        toast.resized.connect(on_resized)
        toast.setFixedWidth(self.width())

        return toast

    def deleteLater(self):
        remove_live_object(id(self))
        super().deleteLater()

    def draw(self):
        self.__pixmaps_view.transition_to(
            combo=self.__image_files.get_history_entry(self.__history_idx, self.size().toSizeF()),
        )

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
                self.toggle_fullscreen()
            elif combo.key() == Qt.Key.Key_Escape and self.isFullScreen():
                self.toggle_fullscreen()
            elif combo.key() == Qt.Key.Key_S:
                self.toggle_slideshow()
            elif combo.key() == Qt.Key.Key_Plus:
                self.nudge_interval(1)
            elif combo.key() == Qt.Key.Key_Minus:
                self.nudge_interval(-1)
            elif combo.key() == Qt.Key.Key_Question:
                self.toggle_help_toast()

    def _mouseMoveEvent(self, event: QMouseEvent):
        if event.buttons():
            if not self.__drag_tracker:
                self.__drag_tracker = DragTracker(event.position(), event.timestamp())
            else:
                self.__drag_tracker.update(event.position())

            if self.__zoom:
                # transform.m31() # neg x-pos
                # transform.m32() # neg y-pos
                if self.__drag_tracker.latest_diff:
                    # transform = self.viewportTransform()
                    # transform.translate(self.__drag_tracker.latest_diff.x(), self.__drag_tracker.latest_diff.y())
                    # self.setTransform(transform)

                    size = self.size()
                    transform = self.viewportTransform()
                    zoom_factor = transform.m11()
                    x_offset = transform.m31()
                    y_offset = transform.m32()
                    viewport = QRectF()
                    print("viewporttransform", self.viewportTransform())
                    # pos = self.viewport().pos()
                    # self.viewport().move(pos.x() + 10, pos.y() + 10)
                    # self.translate(self.__drag_tracker.latest_diff.x(), self.__drag_tracker.latest_diff.y())

    def _mousePressEvent(self, event: QMouseEvent):
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        print("mouserelease")
        # if self.__drag_tracker:
        #     tracker = self.__drag_tracker
        #     self.__drag_tracker = None
        #     if tracker.total_distance > 10:
        #         return

        if event.button() == Qt.MouseButton.LeftButton:
            self.move_by(1)
        elif event.button() == Qt.MouseButton.MiddleButton:
            self.move_by(-1)

    def move_by(self, delta: int):
        history_idx = self.__history_idx + delta
        self.__remaining_time_tmp = None

        if history_idx >= 0 and not self.__pixmaps_view.is_transitioning:
            self.__history_idx = history_idx
            combo = self.__image_files.get_history_entry(history_idx, self.size().toSizeF())

            if history_idx % 10 == 0:
                print_live_objects()

            self.__pixmaps_view.transition_to(
                combo=combo,
                transition_pair_type=self.__get_next_transition_pair_type(),
                transition_duration=self.__transition_duration,
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

    def toggle_fullscreen(self):
        self.setWindowState(self.windowState() ^ Qt.WindowState.WindowFullScreen)

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

    def wheelEvent(self, event: QWheelEvent):
        self.__wheel_delta += event.angleDelta().y()

        if abs(self.__wheel_delta) >= 120:
            zoom_delta = 1 if self.__wheel_delta > 0 else -1
            self.__wheel_delta = 0
            self.zoom(zoom_delta, event.position())

    def zoom(self, delta: int, target_viewport_pos: QPointF):
        zoom = coerce_between(self.__zoom + delta, 0, 8)

        if zoom != self.__zoom:
            self.__zoom = zoom
            scale_factor = 1.4 if delta > 0 else 1 / 1.4
            target_scene_pos = self.mapToScene(target_viewport_pos.toPoint())
            viewport = self.viewport()

            self.scale(scale_factor, scale_factor)
            self.centerOn(target_scene_pos)

            delta_viewport_pos = target_viewport_pos - QPointF(viewport.width() / 2, viewport.height() / 2)
            target_pos = self.mapFromScene(target_scene_pos)
            viewport_center = target_pos - delta_viewport_pos.toPoint()

            print(
                "target_viewport_pos", target_viewport_pos, "target_scene_pos", target_scene_pos,
                "delta_viewport_pos", delta_viewport_pos, "target_pos", target_pos, "viewport_center", viewport_center,
            )

            self.centerOn(self.mapToScene(viewport_center))

    def __get_next_transition_pair_type(self):
        pairs = self.__get_transition_pair_types()
        if not pairs:
            return None
        return random.choice(pairs)

    # def __get_no_image_pixmap(self):
    #     size = self.size()
    #     image = QPixmap(size)
    #     image.fill(Qt.GlobalColor.black)
    #     painter = QPainter(image)
    #     painter.setPen(Qt.GlobalColor.white)
    #     font = painter.font()
    #     font.setPixelSize(int(size.width() / 20))
    #     painter.setFont(font)
    #     painter.drawText(image.rect(), Qt.AlignmentFlag.AlignCenter, "No images found!")
    #     return image

    def __get_transition_pair_types(self):
        pairs = TRANSITION_PAIRS

        if self.__config.transitions.value is not None:
            names = {p.name for p in pairs}
            include = set(name.replace("_", "-") for name in self.__config.transitions.value.get("include", names))
            exclude = set(name.replace("_", "-") for name in self.__config.transitions.value.get("exclude", []))

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
