from typing import Any

from PySide6.QtWidgets import QWidget


class Transition:
    property_name: str
    start_value: Any
    end_value: Any

    def __init__(self, parent: QWidget):
        self.parent = parent

    def get_start_value(self):
        return self.start_value

    def get_end_value(self):
        return self.end_value


class FadeIn(Transition):
    property_name = "opacity"
    start_value = 0.0
    end_value = 1.0


class FadeOut(Transition):
    property_name = "opacity"
    start_value = 1.0
    end_value = 0.0


class SlideInFromBottom(Transition):
    property_name = "y"
    end_value = 0.0

    def get_start_value(self):
        return self.parent.size().height()


class SlideOutToTop(Transition):
    property_name = "y"
    start_value = 0.0

    def get_end_value(self):
        return self.parent.size().height() * -1


class SlideInFromTop(Transition):
    property_name = "y"
    end_value = 0.0

    def get_start_value(self):
        return self.parent.size().height() * -1


class SlideOutToBottom(Transition):
    property_name = "y"
    start_value = 0.0

    def get_end_value(self):
        return self.parent.size().height()


class SlideInFromLeft(Transition):
    property_name = "x"
    end_value = 0.0

    def get_start_value(self):
        return self.parent.size().width() * -1


class SlideOutToRight(Transition):
    property_name = "x"
    start_value = 0.0

    def get_end_value(self):
        return self.parent.size().width()


class SlideInFromRight(Transition):
    property_name = "x"
    end_value = 0.0

    def get_start_value(self):
        return self.parent.size().width()


class SlideOutToLeft(Transition):
    property_name = "x"
    start_value = 0.0

    def get_end_value(self):
        return self.parent.size().width() * -1


class Shrink(Transition):
    property_name = "scale"
    start_value = 1.0
    end_value = 0.0


class Grow(Transition):
    property_name = "scale"
    start_value = 0.0
    end_value = 1.0


class BlurIncrease(Transition):
    property_name = "blur"
    start_value = 0.0
    end_value = 100.0


class BlurDecrease(Transition):
    property_name = "blur"
    start_value = 100.0
    end_value = 0.0


class MarqueeIncrease(Transition):
    property_name = "marquee"
    start_value = 0.0
    end_value = 1.0


class MarqueeDecrease(Transition):
    property_name = "marquee"
    start_value = 1.0
    end_value = 0.0


class Noop(Transition):
    property_name = "noop"
    start_value = 0.0
    end_value = 0.0


class TransitionPair:
    enter_type: type[Transition] | None = None
    exit_type: type[Transition] | None = None
    enter: Transition | None = None
    exit: Transition | None = None

    def __init__(self, parent: QWidget):
        self.parent = parent
        if self.enter_type is not None:
            self.enter = self.enter_type(parent)
        if self.exit_type is not None:
            self.exit = self.exit_type(parent)


class Fade(TransitionPair):
    exit_type = FadeOut
    enter_type = FadeIn


class SlideUp(TransitionPair):
    exit_type = SlideOutToTop
    enter_type = SlideInFromBottom


class SlideDown(TransitionPair):
    exit_type = SlideOutToBottom
    enter_type = SlideInFromTop


class SlideRight(TransitionPair):
    exit_type = SlideOutToRight
    enter_type = SlideInFromLeft


class SlideLeft(TransitionPair):
    exit_type = SlideOutToLeft
    enter_type = SlideInFromRight


class ShrinkGrow(TransitionPair):
    exit_type = Shrink
    enter_type = Grow


class Blur(TransitionPair):
    exit_type = BlurIncrease
    enter_type = BlurDecrease


class Marquee(TransitionPair):
    exit_type = MarqueeIncrease
    enter_type = Noop


TRANSITION_PAIR_CLASSES = [Fade, SlideUp, SlideDown, SlideLeft, SlideRight, ShrinkGrow, Marquee]
