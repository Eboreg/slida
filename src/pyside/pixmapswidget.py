from PySide6.QtCore import (
    Property,
    QAbstractAnimation,
    QEasingCurve,
    QParallelAnimationGroup,
    QPropertyAnimation,
    Qt,
    Slot,
    QPoint
)
from PySide6.QtGui import QPainter, QLinearGradient, QGradient, QPalette
from PySide6.QtWidgets import (
    QGraphicsBlurEffect,
    QGraphicsScene,
    QGraphicsView,
    QGraphicsWidget,
    QWidget,
    QGraphicsOpacityEffect,
)

from pyside.animation import Transition, TransitionPair
from pyside.pixmaplist import PixmapList
from pyside.utils import coerce_between


class AnimPixmapsWidget(QGraphicsWidget):
    animation: QPropertyAnimation
    pixmaps: PixmapList | None = None
    duration = 600
    _blur: float = 0.0
    _marquee: float = 1.0
    _noop: float = 0.0

    def __init__(self, view: QGraphicsView, **kwargs):
        super().__init__(**kwargs)
        self.setAutoFillBackground(True)
        self.animation = QPropertyAnimation(parent=view, targetObject=self)
        self.animation.setDuration(self.duration)
        self.animation.setEasingCurve(QEasingCurve.Type.InOutSine)

    @Property(float)
    def blur(self):  # pylint: disable=method-hidden
        return self._blur

    @blur.setter
    def blur(self, value: float):
        self._blur = value
        effect = self.graphicsEffect()

        if not isinstance(effect, QGraphicsBlurEffect):
            effect = QGraphicsBlurEffect(self, blurHints=QGraphicsBlurEffect.BlurHint.AnimationHint)
            self.setGraphicsEffect(effect)

        if value > 0.0:
            effect.setEnabled(True)
            effect.setBlurRadius(value)
        else:
            effect.setEnabled(False)

    @Property(float)
    def marquee(self):  # pylint: disable=method-hidden
        return self._marquee

    @marquee.setter
    def marquee(self, value: float):
        self._marquee = value
        effect = self.graphicsEffect()
        brush = QLinearGradient(QPoint(0, 0), QPoint(50, 0))
        brush.setSpread(QGradient.Spread.RepeatSpread)

        if not isinstance(effect, QGraphicsOpacityEffect):
            effect = QGraphicsOpacityEffect(self)
            self.setGraphicsEffect(effect)

        if value < 1.0:
            effect.setEnabled(True)
            effect.setOpacity(1.0)
            v1 = coerce_between(value, 0.0, 1.0)
            v2 = coerce_between(value + 0.01, 0.0, 1.0)
            brush.setColorAt(v1, Qt.GlobalColor.transparent)
            brush.setColorAt(v2, Qt.GlobalColor.black)
            effect.setOpacityMask(brush)
        else:
            effect.setEnabled(False)

    @Property(float)
    def noop(self):
        return self._noop

    @noop.setter
    def noop(self, value: float):
        self._noop = value

    def paint(self, painter: QPainter, option, widget: QWidget | None):
        if self.pixmaps:
            images = self.pixmaps.get_fitting_images()
            rect = images.get_rect(self.size())
            left = rect.left()
            # painter.setBackground(Qt.GlobalColor.black)

            for pixmap in images.get_scaled_pixmaps(self.size()):
                painter.drawPixmap(left, rect.top(), pixmap)
                left += pixmap.width()

    def reset_transition_properties(self):
        self.setX(0.0)
        self.setY(0.0)
        self.setScale(1.0)
        self.setOpacity(1.0)
        self.blur = 0.0
        self.marquee = 1.0

    def resizeEvent(self, event):
        size = self.size()
        self.setTransformOriginPoint(size.width() / 2, size.height() / 2)
        super().resizeEvent(event)

    def update_animation(self, transition: Transition):
        self.animation.setPropertyName(transition.property_name.encode())
        self.animation.setStartValue(transition.get_start_value())
        self.animation.setEndValue(transition.get_end_value())
        self.setProperty(transition.property_name, transition.get_start_value())

    def set_pixmaps(self, pixmaps: PixmapList):
        self.pixmaps = pixmaps


class AnimPixmapsView(QGraphicsView):
    current_widget: AnimPixmapsWidget
    next_widget: AnimPixmapsWidget
    animation_group: QParallelAnimationGroup

    def __init__(self):
        super().__init__()

        scene = QGraphicsScene(self)

        self.setScene(scene)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setBackgroundRole(QPalette.ColorRole.NoRole)

        self.current_widget = AnimPixmapsWidget(view=self)
        scene.addItem(self.current_widget)
        self.current_widget.setZValue(1.0)

        self.next_widget = AnimPixmapsWidget(view=self)
        scene.addItem(self.next_widget)
        self.next_widget.setZValue(0.0)

        self.animation_group = QParallelAnimationGroup(self)
        self.animation_group.addAnimation(self.current_widget.animation)
        self.animation_group.addAnimation(self.next_widget.animation)
        self.animation_group.finished.connect(self.on_transition_finished)

    def is_transitioning(self):
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
