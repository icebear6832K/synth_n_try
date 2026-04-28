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

