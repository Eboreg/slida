import tracemalloc

from PyQt6.QtCore import Qt, pyqtSlot
from PyQt6.QtWidgets import QGraphicsItem, QGraphicsScene, QGraphicsView, QWidget

from slida.AnimPixmapsWidget import AnimPixmapsWidget
from slida.PixmapList import PixmapList
from slida.transitions import NOOP, TransitionPair


tracemalloc.start(10)


class AnimPixmapsView(QGraphicsView):
    __current_widget: AnimPixmapsWidget
    __next_widget: AnimPixmapsWidget
    __is_transitioning: bool = False
    __snapshot: tracemalloc.Snapshot | None = None

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)

        scene = QGraphicsScene(self)

        self.setScene(scene)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setBackgroundBrush(Qt.GlobalColor.black)

        self.__next_widget = AnimPixmapsWidget()
        scene.addItem(self.__next_widget)

        self.__current_widget = AnimPixmapsWidget()
        scene.addItem(self.__current_widget)

    @property
    def is_transitioning(self):
        return self.__is_transitioning

    @pyqtSlot()
    def on_transition_finished(self):
        old_current = self.__current_widget
        self.__current_widget = self.__next_widget
        self.__next_widget = old_current
        self.__is_transitioning = False
        self.__next_widget.stackBefore(self.__current_widget)

        # self.snapshot()

    def snapshot(self):
        snapshot = tracemalloc.take_snapshot()
        snapshot = snapshot.filter_traces((
            tracemalloc.Filter(False, "<frozen importlib._bootstrap>"),
            tracemalloc.Filter(False, "<frozen importlib._bootstrap_external>"),
            tracemalloc.Filter(False, "<unknown>"),
        ))

        if self.__snapshot:
            diffs = snapshot.compare_to(self.__snapshot, "traceback")
            for diff in diffs[:10]:
                print("%s memory blocks: %.1f KiB" % (diff.count, diff.size / 1024))
                for line in diff.traceback.format():
                    print(line)
                print("")

            print("\n============================================================\n")

        self.__snapshot = snapshot

    def log_item(self, item: QGraphicsItem, indent: int = 0):
        print((" " * indent) + str(item))
        for child in item.childItems():
            self.log_item(child, indent + 4)

    def resizeEvent(self, event):
        # viewport_rect = self.viewport().rect()
        geometry = self.geometry()

        # self.scene().setSceneRect(viewport_rect)
        self.scene().setSceneRect(geometry)
        self.__current_widget.setGeometry(geometry)
        self.__next_widget.setGeometry(geometry)
        super().resizeEvent(event)

    def set_current_pixmaps(self, pixmaps: PixmapList):
        self.__current_widget.set_pixmaps(pixmaps)
        self.scene().update(self.sceneRect())

    def transition_to(
        self,
        pixmaps: PixmapList,
        transition_pair_type: type[TransitionPair] | None,
        transition_duration: float,
    ):
        self.__next_widget.set_pixmaps(pixmaps)
        self.scene().update(self.sceneRect())

        if transition_pair_type is None:
            transition_pair_type = NOOP
            transition_duration = 0.0

        transition_pair = transition_pair_type(
            parent=self,
            enter_parent=self.__next_widget,
            exit_parent=self.__current_widget,
            duration=int(transition_duration * 1000),
        )

        self.__current_widget.set_transition(transition_pair.exit)
        self.__next_widget.set_transition(transition_pair.enter)
        self.__is_transitioning = True

        transition_pair.animation_group.finished.connect(self.on_transition_finished)
        transition_pair.animation_group.start()
