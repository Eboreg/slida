from PySide6.QtCore import QEasingCurve

from slida.transitions.base import Transition


class HorizontalSlideMixin:
    end_value = 0.0
    property_name = "x"
    easing = QEasingCurve.Type.OutBack


class VerticalSlideMixin:
    end_value = 0.0
    property_name = "y"
    easing = QEasingCurve.Type.OutBack


class SlideInFromBottom(VerticalSlideMixin, Transition):
    def get_start_value(self):
        return self.parent().size().height()


class SlideInFromLeft(HorizontalSlideMixin, Transition):
    def get_start_value(self):
        return self.parent().size().width() * -1


class SlideInFromRight(HorizontalSlideMixin, Transition):
    def get_start_value(self):
        return self.parent().size().width()


class SlideInFromTop(VerticalSlideMixin, Transition):
    def get_start_value(self):
        return self.parent().size().height() * -1


class SlideOutToBottom(VerticalSlideMixin, Transition):
    def get_end_value(self):
        return self.parent().size().height()


class SlideOutToLeft(HorizontalSlideMixin, Transition):
    def get_end_value(self):
        return self.parent().size().width() * -1


class SlideOutToRight(HorizontalSlideMixin, Transition):
    def get_end_value(self):
        return self.parent().size().width()


class SlideOutToTop(VerticalSlideMixin, Transition):
    def get_end_value(self):
        return self.parent().size().height() * -1
