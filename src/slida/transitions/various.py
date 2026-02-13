import copy

from PySide6.QtCore import QEasingCurve, QRectF, Qt
from PySide6.QtGui import QColor, QImage, QPainter, QPixmap, QTransform

from slida.qt.test_effect import TestEffect
from slida.transitions.base import EffectTransition, Transition


class ShrinkGrowTransition(Transition):
    property_name = "scale"

    def on_animation_group_start(self):
        super().on_animation_group_start()
        size = self.parent().size()
        self.parent().setTransformOriginPoint(size.width() / 2, size.height() / 2)


class FadeIn(Transition):
    property_name = "opacity"


class FadeOut(Transition):
    end_value = 0.0
    property_name = "opacity"
    start_value = 1.0

    def cleanup(self):
        super().cleanup()
        self.parent().setOpacity(1.0)


class FlashIn(Transition):
    easing = QEasingCurve.Type.OutSine
    parent_z = 1.0
    start_value = 1.0
    end_value = 0.0

    def on_progress(self, value: float):
        super().on_progress(value)
        self.parent().update(self.parent().rect())

    def paint(self, painter: QPainter, image: QImage, image_rect: QRectF):
        painter.drawImage(self.parent().rect(), image)

        if self._progress:
            overlay = QPixmap(self.parent().size().toSize())
            overlay.fill(QColor(255, 255, 255, int(self._progress * 255)))
            painter.drawPixmap(self.parent().rect().toRect(), overlay)


class Grow(ShrinkGrowTransition):
    easing = QEasingCurve.Type.OutExpo


class Noop(Transition):
    end_value = 0.0


class Shrink(ShrinkGrowTransition):
    easing = QEasingCurve.Type.OutSine
    end_value = 0.0
    start_value = 1.0

    def cleanup(self):
        super().cleanup()
        self.parent().setScale(1.0)


class TestIn(EffectTransition[TestEffect]):
    effect_type = TestEffect
    parent_z = 1.0

    def on_progress(self, value: float):
        self.parent().update(self.parent().rect())
        self.parent().setVisible(True)

    def paint(self, painter: QPainter, image: QImage, image_rect: QRectF):
        t = QTransform()
        left_rect = copy.copy(image_rect)
        left_rect.setRight(image_rect.right() / 2)
        left = image.copy(left_rect.toRect())
        print(f"före: TestIn.paint({image_rect}, {left_rect}, {left.rect()})")
        t.translate(left_rect.width(), left_rect.height() / 2)
        t.rotate(self._progress * -90.0, Qt.Axis.YAxis)
        t.translate(0, -left_rect.height() / 2)
        left = left.transformed(t)
        print(f"efter: TestIn.paint({image_rect}, {left_rect}, {left.rect()})")
        painter.drawImage(left.rect(), left)
