from abc import abstractmethod
from typing import Generic, TypeVar

from PySide6.QtCore import (
    Property,
    QAbstractAnimation,
    QEasingCurve,
    QObject,
    QPropertyAnimation,
    Slot,
)
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import QGraphicsEffect, QGraphicsWidget, QWidget

from slida.ScaledImage import ScaledImage


Parent = QWidget | QGraphicsWidget
_ET = TypeVar("_ET", bound=QGraphicsEffect)


class Transition(QObject):
    name: str
    animation: QAbstractAnimation
    property_name: str | None = None
    start_value: float = 0.0
    end_value: float = 1.0
    easing: QEasingCurve.Type = QEasingCurve.Type.Linear
    parent_z: float | None = None
    is_active: bool = False
    no_borders: bool = False
    _progress: float
    _scaled_image: ScaledImage | None = None

    def __init__(self, name: str, parent: QGraphicsWidget, duration: int):
        super().__init__(parent)
        self.name = name
        self._progress = self.start_value

        if self.property_name:
            parent.setProperty(self.property_name, self.get_start_value())
        if self.parent_z is not None:
            parent.setZValue(self.parent_z)
            parent.setVisible(False)

        self.animation = self.create_animation(duration)

    @Property(float) # type: ignore
    def progress(self): # type: ignore
        return self._progress

    @progress.setter
    def progress(self, value: float):
        if value != self._progress:
            self._progress = value

            if self.parent_z:
                self.parent().setVisible(True)
            self.on_progress(value)
            if self.property_name:
                self.parent().setProperty(self.property_name, value)

    def cleanup(self):
        self.animation.stateChanged.disconnect(self.__on_animation_state_changed)

    def create_animation(self, duration: int) -> QAbstractAnimation:
        animation = QPropertyAnimation(parent=self, targetObject=self)
        animation.setDuration(duration)
        animation.setEasingCurve(self.easing)
        animation.setStartValue(self.get_start_value())
        animation.setEndValue(self.get_end_value())
        animation.setPropertyName("progress".encode())
        animation.stateChanged.connect(self.__on_animation_state_changed)

        return animation

    def get_end_value(self) -> float:
        return self.end_value

    def get_start_value(self) -> float:
        return self.start_value

    def on_animation_group_finish(self):
        self.is_active = False
        self.parent().setZValue(0.0)
        self.cleanup()

    def on_animation_group_start(self):
        self.is_active = True

    def on_animation_finish(self):
        ...

    def on_animation_start(self):
        ...

    def on_progress(self, value: float):
        ...

    def paint(self, painter: QPainter, scaled_image: ScaledImage):
        image = scaled_image.get_image(no_borders=self.is_active and self.no_borders)
        painter.drawImage(self.parent().rect(), image)

    def parent(self) -> QGraphicsWidget:
        parent = super().parent()
        assert isinstance(parent, QGraphicsWidget)

        return parent

    def set_scaled_image(self, value: ScaledImage):
        self._scaled_image = value

    @Slot(QAbstractAnimation.State, QAbstractAnimation.State)
    def __on_animation_state_changed(self, new_state: QAbstractAnimation.State, old_state: QAbstractAnimation.State):
        if new_state == QAbstractAnimation.State.Running and old_state != new_state:
            self.on_animation_start()
        elif new_state == QAbstractAnimation.State.Stopped and old_state != new_state:
            try:
                self.on_animation_finish()
            except RuntimeError:
                pass


class EffectTransition(Transition, Generic[_ET]):
    @abstractmethod
    def get_effect(self) -> _ET:
        ...

    def cleanup(self):
        super().cleanup()
        self.get_effect().setEnabled(False)
