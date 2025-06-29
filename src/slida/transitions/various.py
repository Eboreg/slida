from PySide6.QtCore import QEasingCurve

from slida.transitions.base import Transition


class HingeTransition(Transition):
    no_borders = True

    def on_progress(self, value: float):
        super().on_progress(value)
        self.parent().setRotation(value)


class ShrinkGrowTransition(Transition):
    property_name = "scale"

    def on_animation_start(self):
        super().on_animation_start()
        size = self.parent().size()
        self.parent().setTransformOriginPoint(size.width() / 2, size.height() / 2)


class FadeIn(Transition):
    property_name = "opacity"


class FadeOut(Transition):
    property_name = "opacity"
    start_value = 1.0
    end_value = 0.0


class Grow(ShrinkGrowTransition):
    easing = QEasingCurve.Type.OutExpo


class HingeIn(HingeTransition):
    start_value = -90.0
    end_value = 0.0
    easing = QEasingCurve.Type.OutBack
    parent_z = 1.0

    def on_animation_start(self):
        super().on_animation_start()
        self.parent().setTransformOriginPoint(0.0, self.parent().size().height())


class HingeOut(HingeTransition):
    start_value = 0.0
    end_value = -90.0

    def on_animation_finish(self):
        super().on_animation_finish()
        self.parent().setRotation(0.0)

    def on_animation_start(self):
        super().on_animation_start()
        size = self.parent().size()
        self.parent().setTransformOriginPoint(size.width(), size.height())


class Noop(Transition):
    end_value = 0.0


class Shrink(ShrinkGrowTransition):
    end_value = 0.0
    start_value = 1.0
    easing = QEasingCurve.Type.OutSine
