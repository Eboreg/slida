from slida.transitions.base import Transition
from slida.transitions.blur_effect import BlurDecrease, BlurIncrease
from slida.transitions.opacity_effect import (
    ClockfaceOut,
    ExplodeIn,
    ImplodeOut,
    MarqueeOut,
    RadialOut,
)
from slida.transitions.pair import (
    SequentialTransitionPair,
    TransitionPair,
    transition_pair_factory,
)
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
    FlipXIn,
    FlipXOut,
    FlipYIn,
    FlipYOut,
    Grow,
    HingeIn,
    HingeOut,
    Noop,
    Shrink,
)


NOOP = transition_pair_factory("noop", Noop, Noop)

TRANSITION_PAIRS: list[type[TransitionPair]] = [
    transition_pair_factory("blur", BlurDecrease, BlurIncrease),
    transition_pair_factory("clockface", Noop, ClockfaceOut),
    transition_pair_factory("explode", ExplodeIn, Noop),
    transition_pair_factory("fade", FadeIn, FadeOut),
    transition_pair_factory("flip-x", FlipXIn, FlipXOut, SequentialTransitionPair),
    transition_pair_factory("flip-y", FlipYIn, FlipYOut, SequentialTransitionPair),
    transition_pair_factory("hinge", HingeIn, HingeOut),
    transition_pair_factory("implode", Noop, ImplodeOut),
    transition_pair_factory("marquee", Noop, MarqueeOut),
    transition_pair_factory("radial", Noop, RadialOut),
    transition_pair_factory("random-squares", RandomSquaresIn, Noop),
    transition_pair_factory("shrink-grow", Grow, Shrink, SequentialTransitionPair),
    transition_pair_factory("slide-down", SlideInFromTop, SlideOutToBottom),
    transition_pair_factory("slide-left", SlideInFromRight, SlideOutToLeft),
    transition_pair_factory("slide-right", SlideInFromLeft, SlideOutToRight),
    transition_pair_factory("slide-up", SlideInFromBottom, SlideOutToTop),
    transition_pair_factory("top-squares", TopSquaresIn, Noop),
    transition_pair_factory("top-left-squares", TopLeftSquaresIn, Noop),
]

TRANSITION_PAIR_MAP: dict[str, type[TransitionPair]] = {
    pair.name: pair for pair in TRANSITION_PAIRS
}

__all__ = ["NOOP", "TRANSITION_PAIRS", "TRANSITION_PAIR_MAP", "TransitionPair", "Transition"]
