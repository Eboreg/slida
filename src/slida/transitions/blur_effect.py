from PySide6.QtCore import QEasingCurve
from PySide6.QtWidgets import QGraphicsBlurEffect, QGraphicsWidget

from slida.transitions.base import EffectTransition


class BlurTransition(EffectTransition[QGraphicsBlurEffect]):
    effect_type = QGraphicsBlurEffect

    def cleanup(self):
        super().cleanup()
        self.parent().setOpacity(1.0)

    def create_effect(self, parent: QGraphicsWidget) -> QGraphicsBlurEffect:
        return QGraphicsBlurEffect(parent, blurHints=QGraphicsBlurEffect.BlurHint.AnimationHint)

    def on_progress(self, value: float):
        super().on_progress(value)
        self.parent().setOpacity(1 - (value / 100))
        effect = self.get_effect()

        if value > 0.0:
            effect.setEnabled(True)
            effect.setBlurRadius(value)
        else:
            effect.setEnabled(False)


class BlurDecrease(BlurTransition):
    easing = QEasingCurve.Type.InBounce
    end_value = -10.0
    start_value = 100.0


class BlurIncrease(BlurTransition):
    easing = QEasingCurve.Type.InCubic
    end_value = 100.0
