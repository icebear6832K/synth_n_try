"""
Pitch-amplitude vector representation.

This module defines `PAPoint`, the basic vector object used by the sound event
system. A point contains two values: pitch and amplitude. Pitch is interpreted as
a semitone-like value during rendering, while amplitude is interpreted as a
logarithmic value and later converted into linear signal amplitude.

A `PAPoint` can be understood as a local modification vector applied to the
basic sonic existence-state. Helper constructors make it easy to create pure
pitch changes, pure amplitude changes, or combined pitch-amplitude points.

Typical use:
    from pAPoint import e_point, p_point, a_point, pa_point, pa_sum

    neutral = e_point()          # PAPoint(0, 0)
    up_octave = p_point(12)      # pitch +12, amplitude unchanged
    quieter = a_point(-2)        # amplitude lowered by 2 log units
    combined = pa_sum([up_octave, quieter])
"""
from arrStruct import ArrStruct
import numpy as np


class PAPoint(ArrStruct):
    def __new__(cls, pitch, amp):
        obj = np.asarray([pitch, amp], dtype='float64').view(cls)
        return obj

    def pitch(self):
        return self[0]

    def amp(self):
        return self[1]

    def __eq__(self, other):
        if isinstance(other, PAPoint):
            return np.array_equal(self, other)
        else:
            return False

    def __hash__(self):
        return hash((self.pitch(), self.amp(), 'PAP'))


def pa_sum(pa_points: list[PAPoint]) -> PAPoint:
    rst = e_point()
    for pt in pa_points:
        rst += pt
    return rst

def e_point():
    return PAPoint(0, 0)

def p_point(v):
    return PAPoint(v, 0)

def a_point(v):
    return PAPoint(0, v)

def pa_point(pitch, amp):
    return PAPoint(pitch, amp)


if __name__ == '__main__':
    print(pa_sum([p_point(3), a_point(2)]))

