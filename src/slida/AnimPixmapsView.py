from PySide6.QtCore import Qt, Slot
from PySide6.QtWidgets import QGraphicsScene, QGraphicsView, QWidget

from slida.AnimPixmapsWidget import AnimPixmapsWidget
from slida.debug import add_live_object, remove_live_object
from slida.ImageFileCombo import ImageFileCombo
from slida.transitions import NOOP, TransitionPair


class AnimPixmapsView(QGraphicsView):
    __current_widget: AnimPixmapsWidget | None = None
    __is_transitioning: bool = False
    __next_widget: AnimPixmapsWidget | None = None

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)

        scene = QGraphicsScene(self)

        self.setScene(scene)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setBackgroundBrush(Qt.GlobalColor.black)

        add_live_object(id(self), self.__class__.__name__)

    @property
    def is_transitioning(self):
        return self.__is_transitioning

    def deleteLater(self):
        super().deleteLater()
        remove_live_object(id(self))

    def get_current_filenames(self):
        if self.__current_widget:
            return self.__current_widget.get_current_filenames()
        return []

    @Slot()
    def on_transition_finished(self):
        old_current = self.__current_widget
        self.__current_widget = self.__next_widget

        if old_current:
            self.scene().removeItem(old_current)
            old_current.deleteLater()
            self.__next_widget = None

        self.__is_transitioning = False

    def resizeEvent(self, event):
        viewport_rect = self.viewport().rect()
        geometry = self.geometry()

        self.scene().setSceneRect(viewport_rect)
        if self.__current_widget:
            self.__current_widget.setGeometry(geometry)
        if self.__next_widget:
            self.__next_widget.setGeometry(geometry)
        super().resizeEvent(event)

    def transition_to(
        self,
        combo: ImageFileCombo,
        transition_pair_type: type[TransitionPair] | None = None,
        transition_duration: float = 0.0,
    ):
        if self.__is_transitioning:
            return

        if transition_pair_type is None:
            transition_pair_type = NOOP
            transition_duration = 0.0

        self.__next_widget = AnimPixmapsWidget(combo=combo, size=self.size().toSizeF())
        self.scene().addItem(self.__next_widget)

        if self.__current_widget and self.__current_widget.isActive():
            self.__next_widget.stackBefore(self.__current_widget)

        transition_pair = transition_pair_type(
            parent=self,
            enter_parent=self.__next_widget,
            exit_parent=self.__current_widget,
            duration=int(transition_duration * 1000),
        )

        self.__next_widget.set_transition(transition_pair.enter)
        if self.__current_widget:
            self.__current_widget.set_transition(transition_pair.exit)

        self.__is_transitioning = True

        transition_pair.animation_group.finished.connect(self.on_transition_finished)
        transition_pair.animation_group.start()
