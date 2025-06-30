from PySide6.QtCore import (
    QAbstractAnimation,
    QAnimationGroup,
    QObject,
    QParallelAnimationGroup,
    QSequentialAnimationGroup,
)
from PySide6.QtWidgets import QGraphicsWidget

from slida.transitions.base import Transition
from slida.utils import KebabCase, PascalCase, convert_case


class TransitionPair(QObject):
    name: str
    enter: Transition
    exit: Transition
    animation_group: QAnimationGroup

    enter_class: type[Transition]
    exit_class: type[Transition]
    animation_group_type: type[QAnimationGroup] = QParallelAnimationGroup

    def __init__(
        self,
        parent: QObject,
        enter_parent: QGraphicsWidget,
        exit_parent: QGraphicsWidget,
        duration: int,
    ):
        super().__init__(parent)
        self.enter = self.enter_class(name=self.name, parent=enter_parent, duration=duration)
        self.exit = self.exit_class(name=self.name, parent=exit_parent, duration=duration)
        self.animation_group = self.animation_group_type(parent)
        self.animation_group.addAnimation(self.exit.animation)
        self.animation_group.addAnimation(self.enter.animation)
        self.animation_group.stateChanged.connect(self.on_animation_state_changed)

    def on_animation_state_changed(self, new_state: QAbstractAnimation.State, old_state: QAbstractAnimation.State):
        if new_state == QAbstractAnimation.State.Running and old_state != new_state:
            self.enter.on_animation_group_start()
            self.exit.on_animation_group_start()
        elif new_state == QAbstractAnimation.State.Stopped and old_state != new_state:
            try:
                self.enter.on_animation_group_finish()
                self.exit.on_animation_group_finish()
            except RuntimeError:
                pass


class SequentialTransitionPair(TransitionPair):
    animation_group_type = QSequentialAnimationGroup

    def __init__(self, parent, enter_parent, exit_parent, duration):
        super().__init__(parent, enter_parent, exit_parent, int(duration / 2))


def transition_pair_factory(
    name: str,
    enter_class: type[Transition],
    exit_class: type[Transition],
    pair_class: type[TransitionPair] = TransitionPair,
):
    return type(
        convert_case(name, source=KebabCase, target=PascalCase),
        (pair_class,),
        {
            "name": name,
            "enter_class": enter_class,
            "exit_class": exit_class,
        }
    )
