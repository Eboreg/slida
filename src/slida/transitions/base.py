from abc import abstractmethod
from typing import Generic, TypeVar

from PySide6.QtCore import (
    Property,
    QAbstractAnimation,
    QEasingCurve,
    QObject,
    QPropertyAnimation,
)
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import QGraphicsEffect, QGraphicsWidget, QWidget

from slida.ScaledImage import ScaledImage


Parent = QWidget | QGraphicsWidget
_ET = TypeVar("_ET", bound=QGraphicsEffect)


class Transition(QObject):
    name: str
    property_name: str | None = None
    start_value: float = 0.0
    end_value: float = 1.0
    easing: QEasingCurve.Type = QEasingCurve.Type.Linear
    parent_z: float | None = None
    is_active: bool = False
    no_borders: bool = False
    _progress: float
    _scaled_image: ScaledImage | None = None

    def __init__(self, name: str):
        super().__init__()
        self.name = name
        self._progress = self.start_value

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

    def create_animation(self, duration: int) -> QAbstractAnimation:
        anim = QPropertyAnimation(targetObject=self)
        anim.setDuration(duration)
        anim.setEasingCurve(self.easing)
        anim.setStartValue(self.get_start_value())
        anim.setEndValue(self.get_end_value())
        anim.setPropertyName("progress".encode())

        return anim

    def get_end_value(self) -> float:
        return self.end_value

    def get_start_value(self) -> float:
        return self.start_value

    def on_animation_finish(self):
        self.is_active = False
        parent = self.parent()
        parent.setX(0.0)
        parent.setY(0.0)
        parent.setScale(1.0)
        parent.setOpacity(1.0)
        parent.setZValue(0.0)

    def on_animation_start(self):
        self.is_active = True

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

    def setParent(self, parent: QObject | None):
        super().setParent(parent)

        if parent and self.property_name:
            parent.setProperty(self.property_name, self.get_start_value())
        if isinstance(parent, QGraphicsWidget) and self.parent_z is not None:
            parent.setZValue(self.parent_z)
            parent.setVisible(False)


class EffectTransition(Transition, Generic[_ET]):
    @abstractmethod
    def get_effect(self) -> _ET:
        ...

    def on_animation_finish(self):
        super().on_animation_finish()
        self.get_effect().setEnabled(False)
