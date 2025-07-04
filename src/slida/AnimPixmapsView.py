from PySide6.QtCore import Qt, Slot
from PySide6.QtWidgets import QGraphicsScene, QGraphicsView

from slida.AnimPixmapsWidget import AnimPixmapsWidget
from slida.PixmapList import PixmapList
from slida.transitions import NOOP, TransitionPair


class AnimPixmapsView(QGraphicsView):
    __current_widget: AnimPixmapsWidget
    __next_widget: AnimPixmapsWidget
    __is_transitioning: bool = False

    def __init__(self):
        super().__init__()

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

    @Slot()
    def on_transition_finished(self):
        old_current = self.__current_widget
        self.__current_widget = self.__next_widget
        self.__next_widget = old_current
        self.__is_transitioning = False
        self.__next_widget.stackBefore(self.__current_widget)

    def resizeEvent(self, event):
        viewport_rect = self.viewport().rect()
        geometry = self.geometry()

        self.scene().setSceneRect(viewport_rect)
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
