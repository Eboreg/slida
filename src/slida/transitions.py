import dataclasses

from PySide6.QtCore import (
    QAbstractAnimation,
    QAnimationGroup,
    QEasingCurve,
    QParallelAnimationGroup,
    QPropertyAnimation,
    QSequentialAnimationGroup,
)
from PySide6.QtWidgets import QGraphicsWidget, QWidget


Parent = QWidget | QGraphicsWidget


class Transition:
    name: str
    property_name: str | None = None
    start_value: float = 0.0
    end_value: float = 0.0
    easing: QEasingCurve.Type = QEasingCurve.Type.Linear

    def __init__(self, name: str):
        self.name = name

    def create_animation(self, parent: Parent, duration: int) -> QAbstractAnimation:
        anim = QPropertyAnimation(targetObject=parent)
        anim.setDuration(duration)
        anim.setEasingCurve(self.easing)
        anim.setStartValue(self.get_start_value(parent))
        anim.setEndValue(self.get_end_value(parent))
        if self.property_name:
            anim.setPropertyName(self.property_name.encode())
        return anim

    def get_start_value(self, parent: Parent) -> float:
        return self.start_value

    def get_end_value(self, parent: Parent) -> float:
        return self.end_value

    def init(self, parent: Parent, duration: int):
        if self.property_name:
            parent.setProperty(self.property_name, self.get_start_value(parent))

        return self.create_animation(parent, duration)


class BlurTransition(Transition):
    def create_animation(self, parent: Parent, duration: int) -> QAbstractAnimation:
        group = QParallelAnimationGroup(parent)
        blur_anim = QPropertyAnimation(targetObject=parent)
        blur_anim.setPropertyName("blur".encode())
        blur_anim.setStartValue(self.start_value)
        blur_anim.setEndValue(self.end_value)
        opacity_anim = QPropertyAnimation(targetObject=parent)
        opacity_anim.setPropertyName("opacity".encode())
        opacity_anim.setStartValue(self.end_value / 100)
        opacity_anim.setEndValue(self.start_value / 100)

        for anim in (blur_anim, opacity_anim):
            anim.setDuration(duration)
            anim.setEasingCurve(self.easing)
            group.addAnimation(anim)

        return group

    def init(self, parent, duration):
        parent.setProperty("blur", self.start_value)
        parent.setProperty("opacity", self.end_value / 100)

        return self.create_animation(parent, duration)


class BlurDecrease(BlurTransition):
    start_value = 100.0
    end_value = 0.0


class BlurIncrease(BlurTransition):
    start_value = 0.0
    end_value = 100.0


class ClockfaceOut(Transition):
    property_name = "clockface"
    start_value = 0.0
    end_value = 1.0


class FadeIn(Transition):
    property_name = "opacity"
    start_value = 0.0
    end_value = 1.0


class FadeOut(Transition):
    property_name = "opacity"
    start_value = 1.0
    end_value = 0.0


class Grow(Transition):
    property_name = "scale"
    start_value = 0.0
    end_value = 1.0


class MarqueeOut(Transition):
    property_name = "marquee"
    start_value = 0.0
    end_value = 1.0


class Noop(Transition):
    ...


class RadialOut(Transition):
    property_name = "radial"
    start_value = 0.0
    end_value = 1.0


class RandomSquaresIn(Transition):
    property_name = "random_squares"
    start_value = 0.0
    end_value = 1.0

    def init(self, parent, duration):
        if isinstance(parent, QGraphicsWidget):
            parent.setZValue(1.0)

        return super().init(parent, duration)


class Shrink(Transition):
    property_name = "scale"
    start_value = 1.0
    end_value = 0.0


class SlideInFromBottom(Transition):
    property_name = "y"
    end_value = 0.0

    def get_start_value(self, parent):
        return parent.size().height()


class SlideInFromLeft(Transition):
    property_name = "x"
    end_value = 0.0

    def get_start_value(self, parent):
        return parent.size().width() * -1


class SlideInFromRight(Transition):
    property_name = "x"
    end_value = 0.0

    def get_start_value(self, parent):
        return parent.size().width()


class SlideInFromTop(Transition):
    property_name = "y"
    end_value = 0.0

    def get_start_value(self, parent):
        return parent.size().height() * -1


class SlideOutToBottom(Transition):
    property_name = "y"
    start_value = 0.0

    def get_end_value(self, parent):
        return parent.size().height()


class SlideOutToLeft(Transition):
    property_name = "x"
    start_value = 0.0

    def get_end_value(self, parent):
        return parent.size().width() * -1


class SlideOutToRight(Transition):
    property_name = "x"
    start_value = 0.0

    def get_end_value(self, parent):
        return parent.size().width()


class SlideOutToTop(Transition):
    property_name = "y"
    start_value = 0.0

    def get_end_value(self, parent):
        return parent.size().height() * -1


@dataclasses.dataclass
class TransitionPair:
    name: str
    enter_class: dataclasses.InitVar[type[Transition]]
    exit_class: dataclasses.InitVar[type[Transition]]
    enter: Transition = dataclasses.field(init=False)
    exit: Transition = dataclasses.field(init=False)

    def __post_init__(self, enter_class: type[Transition], exit_class: type[Transition]):
        self.enter = enter_class(name=self.name)
        self.exit = exit_class(name=self.name)

    def init(
        self,
        parent: Parent,
        enter_parent: Parent,
        exit_parent: Parent,
        duration: int,
    ) -> QAnimationGroup:
        group = QParallelAnimationGroup(parent)
        group.addAnimation(self.enter.init(enter_parent, duration))
        group.addAnimation(self.exit.init(exit_parent, duration))

        return group


@dataclasses.dataclass
class SequentialTransitionPair(TransitionPair):
    def init(self, parent, enter_parent, exit_parent, duration):
        group = QSequentialAnimationGroup(parent)
        group.addAnimation(self.exit.init(exit_parent, int(duration / 2)))
        group.addAnimation(self.enter.init(enter_parent, int(duration / 2)))

        return group


blur = TransitionPair("blur", BlurDecrease, BlurIncrease)
clockface = TransitionPair("clockface", Noop, ClockfaceOut)
fade = TransitionPair("fade", FadeIn, FadeOut)
marquee = TransitionPair("marquee", Noop, MarqueeOut)
noop = TransitionPair("noop", Noop, Noop)
radial = TransitionPair("radial", Noop, RadialOut)
random_squares = TransitionPair("random_squares", RandomSquaresIn, Noop)
shrink_grow = SequentialTransitionPair("shrink_grow", Grow, Shrink)
slide_down = TransitionPair("slide_down", SlideInFromTop, SlideOutToBottom)
slide_left = TransitionPair("slide_left", SlideInFromRight, SlideOutToLeft)
slide_right = TransitionPair("slide_right", SlideInFromLeft, SlideOutToRight)
slide_up = TransitionPair("slide_up", SlideInFromBottom, SlideOutToTop)
top_squares = TransitionPair("top_squares", RandomSquaresIn, Noop)
topleft_squares = TransitionPair("topleft_squares", RandomSquaresIn, Noop)


TRANSITION_PAIRS: list[TransitionPair] = [
    blur,
    clockface,
    fade,
    marquee,
    radial,
    random_squares,
    shrink_grow,
    slide_down,
    slide_left,
    slide_right,
    slide_up,
    top_squares,
    topleft_squares,
]
