from slida.transitions.base import Transition
from slida.transitions.blur_effect import BlurDecrease, BlurIncrease
from slida.transitions.opacity_effect import (
    ClockfaceOut,
    ExplodeIn,
    ImplodeOut,
    MarqueeOut,
    RadialOut,
)
from slida.transitions.pair import SequentialTransitionPair, TransitionPair
from slida.transitions.slide import (
    SlideInFromBottom,
    SlideInFromLeft,
    SlideInFromRight,
    SlideInFromTop,
    SlideOutToBottom,
    SlideOutToLeft,
    SlideOutToRight,
    SlideOutToTop,
)
from slida.transitions.sub_image import (
    RandomSquaresIn,
    TopLeftSquaresIn,
    TopSquaresIn,
)
from slida.transitions.various import (
    FadeIn,
    FadeOut,
    Grow,
    HingeIn,
    HingeOut,
    Noop,
    Shrink,
)


NOOP = TransitionPair("noop", Noop, Noop)

TRANSITION_PAIRS: list[TransitionPair] = [
    TransitionPair("blur", BlurDecrease, BlurIncrease),
    TransitionPair("clockface", Noop, ClockfaceOut),
    TransitionPair("explode", ExplodeIn, Noop),
    TransitionPair("fade", FadeIn, FadeOut),
    TransitionPair("hinge", HingeIn, HingeOut),
    TransitionPair("implode", Noop, ImplodeOut),
    TransitionPair("marquee", Noop, MarqueeOut),
    TransitionPair("radial", Noop, RadialOut),
    TransitionPair("random-squares", RandomSquaresIn, Noop),
    SequentialTransitionPair("shrink-grow", Grow, Shrink),
    TransitionPair("slide-down", SlideInFromTop, SlideOutToBottom),
    TransitionPair("slide-left", SlideInFromRight, SlideOutToLeft),
    TransitionPair("slide-right", SlideInFromLeft, SlideOutToRight),
    TransitionPair("slide-up", SlideInFromBottom, SlideOutToTop),
    TransitionPair("top-squares", TopSquaresIn, Noop),
    TransitionPair("topleft-squares", TopLeftSquaresIn, Noop),
]

TRANSITION_PAIR_MAP: dict[str, TransitionPair] = {
    pair.name: pair for pair in TRANSITION_PAIRS
}

__all__ = ["NOOP", "TRANSITION_PAIRS", "TRANSITION_PAIR_MAP", "TransitionPair", "Transition"]
