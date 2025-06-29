from PySide6.QtCore import (
    QAbstractAnimation,
    QAnimationGroup,
    QParallelAnimationGroup,
    QSequentialAnimationGroup,
)
from PySide6.QtWidgets import QGraphicsWidget, QWidget

from slida.transitions.base import Transition


Parent = QWidget | QGraphicsWidget


class TransitionPair:
    name: str
    enter_class: type[Transition]
    exit_class: type[Transition]
    enter: Transition
    exit: Transition
    parent: Parent
    animation_group_type: type[QAnimationGroup] = QParallelAnimationGroup

    def __init__(self, name: str, enter_class: type[Transition], exit_class: type[Transition]):
        self.name = name
        self.enter = enter_class(name=self.name)
        self.exit = exit_class(name=self.name)

    def create_animation(
        self,
        parent: Parent,
        enter_parent: QGraphicsWidget,
        exit_parent: QGraphicsWidget,
        duration: int,
    ):
        group = self.animation_group_type(parent)
        self.enter.setParent(enter_parent)
        self.exit.setParent(exit_parent)
        group.addAnimation(self.exit.create_animation(duration))
        group.addAnimation(self.enter.create_animation(duration))
        group.stateChanged.connect(self.on_animation_state_changed)

        return group

    def on_animation_state_changed(self, new_state: QAbstractAnimation.State, old_state: QAbstractAnimation.State):
        if new_state == QAbstractAnimation.State.Running and old_state != new_state:
            self.enter.on_animation_start()
            self.exit.on_animation_start()
        elif new_state == QAbstractAnimation.State.Stopped and old_state != new_state:
            try:
                self.enter.on_animation_finish()
                self.exit.on_animation_finish()
            except RuntimeError:
                pass


class SequentialTransitionPair(TransitionPair):
    animation_group_type = QSequentialAnimationGroup

    def create_animation(self, parent, enter_parent, exit_parent, duration):
        return super().create_animation(parent, enter_parent, exit_parent, int(duration / 2))
