from event import CompositeEvent, fxv_event
from interval import ritv

class Pitch(CompositeEvent):
    def __init__(self, pitch: int | float):
        super().__init__([ritv()], fxv_event(pitch))
        self.pitch = pitch

class PitchClass(CompositeEvent):
    def __init__(self, pitch_class: int | float):
        super().__init__([ritv()], fxv_event(pitch_class))
