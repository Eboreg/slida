from PySide6.QtCore import (
    QAbstractAnimation,
    QParallelAnimationGroup,
    Qt,
    Slot,
)
from PySide6.QtGui import QPalette
from PySide6.QtWidgets import QGraphicsScene, QGraphicsView

from slida.animpixmapswidget import AnimPixmapsWidget
from slida.pixmaplist import PixmapList
from slida.transitions import TransitionPair


class AnimPixmapsView(QGraphicsView):
    current_widget: AnimPixmapsWidget
    next_widget: AnimPixmapsWidget
    animation_group: QParallelAnimationGroup

    def __init__(self, transition_duration: float = 0.5):
        super().__init__()

        scene = QGraphicsScene(self)

        self.setScene(scene)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setBackgroundRole(QPalette.ColorRole.NoRole)

        self.current_widget = AnimPixmapsWidget(view=self, transition_duration=transition_duration)
        scene.addItem(self.current_widget)
        self.current_widget.setZValue(1.0)

        self.next_widget = AnimPixmapsWidget(view=self, transition_duration=transition_duration)
        scene.addItem(self.next_widget)
        self.next_widget.setZValue(0.0)

        self.animation_group = QParallelAnimationGroup(self)
        self.animation_group.addAnimation(self.current_widget.animation)
        self.animation_group.addAnimation(self.next_widget.animation)
        self.animation_group.finished.connect(self.on_transition_finished)

    def is_transitioning(self) -> bool:
        return self.animation_group.state() != QAbstractAnimation.State.Stopped

    @Slot()
    def on_transition_finished(self):
        old_current = self.current_widget
        self.current_widget = self.next_widget
        self.next_widget = old_current

        self.next_widget.setVisible(False)
        self.next_widget.reset_transition_properties()
        self.current_widget.reset_transition_properties()
        self.current_widget.setZValue(1.0)
        self.next_widget.setZValue(0.0)

    def resizeEvent(self, event):
        viewport_rect = self.viewport().rect()
        geometry = self.geometry()

        self.scene().setSceneRect(viewport_rect)
        self.current_widget.setGeometry(geometry)
        self.next_widget.setGeometry(geometry)
        super().resizeEvent(event)

    def set_current_pixmaps(self, pixmaps: PixmapList):
        self.current_widget.set_pixmaps(pixmaps)
        self.scene().update(self.sceneRect())

    def set_transition_duration(self, value: float):
        self.current_widget.set_transition_duration(value)
        self.next_widget.set_transition_duration(value)

    def transition_to(self, pixmaps: PixmapList, transitions_class: type[TransitionPair]):
        transitions = transitions_class(self)

        if transitions.exit:
            self.current_widget.update_animation(transitions.exit)
        if transitions.enter:
            self.next_widget.update_animation(transitions.enter)
        self.next_widget.setVisible(True)

        self.next_widget.set_pixmaps(pixmaps)
        self.scene().update(self.sceneRect())

        self.animation_group.start()
