"""
Composable pitch-amplitude curve objects.

This module defines the lower-level transformation layer of the event framework.
A `CurveValue` describes how a pitch-amplitude vector changes over normalized
time. Curves are treated as composable descriptions of modification applied to a
more basic sonic existence-state.

The module includes fixed, linear, Bezier, cosine, cropped, joint, and overlaid
curves. Curve-level overlay with `*` packages multiple curve transformations into
one curve object, so the event layer can treat the result as an ordinary curve.
Sequential connection with `+` joins continuous curves across time.

Typical use:
    from curveValue import fxv, lnv
    from pAPoint import p_point, a_point, pa_point

    constant = fxv(pa_point(0, -2))
    glide = lnv(pa_point(0, -3), pa_point(12, -3))
    shaped = constant * glide
    data = shaped.arr(100)
"""
import numpy as np
import matplotlib.pyplot as plt
from abc import ABC, abstractmethod
from pAPoint import PAPoint, p_point, e_point, a_point, pa_point, pa_sum
from bezierCalculator import BezierSegment, s_curve


C = np.pi * 2

def itv_multi(a, b):
    a0, a1, b0, b1 = a[0], a[1], b[0], b[1]
    return b0 + a0 * (b1 - b0), b0 + a1 * (b1 - b0)

def itv_divide(a, b):
    a0, a1, b0, b1 = a[0], a[1], b[0], b[1]
    return (a0 - b0) / (b1 - b0), 1 + (a1 - b1) / (b1 - b0)

def itv_cross(a, b):
    a0, a1, b0, b1 = a[0], a[1], b[0], b[1]
    return max(a0, b0), min(a1, b1)

def itv_length(itv):
    return itv[1] - itv[0]

def itv_valid(itv):
    return itv[0] < itv[1]


class CurveValue(ABC):
    @property
    @abstractmethod
    def start(self) -> PAPoint:
        pass

    @property
    @abstractmethod
    def end(self) -> PAPoint:
        pass

    def value_by_idx(self, idx):
        if not 0 <= idx < 1:
            raise ValueError("Index must be between 0 and 1")
        else:
            return self._value_by_idx(idx)

    @abstractmethod
    def _value_by_idx(self, idx):
        pass

    @abstractmethod
    def arr(self, sample_num, start_idx=0., end_idx=1.):
        pass

    def joint(self, other, ratio=1.):
        if not isinstance(other, CurveValue):
            raise TypeError
        elif np.any(self.end != other.start):
            raise ValueError("point must be continuous")
        elif isinstance(other, JointCurve) and isinstance(self, JointCurve):
            return JointCurve(self.components + other.components,
                                   self.ratios + [r * ratio for r in other.ratios])
        elif isinstance(other, JointCurve):
            return JointCurve([self] + other.components,
                                   [1] + [r * ratio for r in other.ratios])
        elif isinstance(self, JointCurve):
            return JointCurve(self.components + [other],
                                   [r * ratio for r in self.ratios] + [1])
        else:
            return JointCurve([self, other], [1, ratio])

    def crop(self, itv: tuple):
        return CroppedCurve(self, itv)

    def __mul__(self, other):
        if isinstance(other, CurveValue):
            return OverlaidCurve([self, other])
        else:
            raise TypeError

    def __add__(self, other):
        if isinstance(other, CurveValue):
            return self.joint(other)

    def __copy__(self):
        cls = self.__class__
        result = cls.__new__(cls)
        result.__dict__.update(self.__dict__)
        return result

    def copy(self):
        return self.__copy__()

    def show(self):
        plt.figure(figsize=(8, 5))
        p_a = self.arr(1000)
        t = np.linspace(0, 1, len(p_a), endpoint=False)
        plt.scatter(t, p_a[:, 0], np.exp2(np.maximum(-40, p_a[:, 1])), color='blue', linewidth=3)
        max_y = np.max(p_a[:, 0])
        min_y = np.min(p_a[:, 0])
        plt.xlim(0, 1)
        if max_y - min_y < 4:
            plt.ylim(
                (max_y + min_y) / 2 - 3,
                (max_y + min_y) / 2 + 3
            )
        else:
            plt.ylim(
                (max_y + min_y) / 2 - (max_y - min_y) * 0.75,
                (max_y + min_y) / 2 + (max_y - min_y) * 0.75
            )
        plt.title(str(self))
        plt.show()


class SingleCurveValue(CurveValue):
    @property
    @abstractmethod
    def start(self) -> PAPoint:
        pass

    @property
    @abstractmethod
    def end(self) -> PAPoint:
        pass

    @abstractmethod
    def _value_by_idx(self, idx):
        pass

    @abstractmethod
    def arr(self, sample_num, start_idx=0., end_idx=1.):
        pass


class FixedValue(SingleCurveValue):
    def __init__(self, value: PAPoint):
        self._value = value

    @property
    def start(self) -> PAPoint:
        return self._value

    @property
    def end(self) -> PAPoint:
        return self._value

    def _value_by_idx(self, idx):
        return self._value

    def arr(self, sample_num, start_idx=0., end_idx=1.):
        return np.tile(self._value, (sample_num, 1))


class LinearValue(SingleCurveValue):
    def __init__(self, value_0: PAPoint, value_1: PAPoint):
        self._value_0 = value_0
        self._value_1 = value_1

    @property
    def start(self) -> PAPoint:
        return self._value_0

    @property
    def end(self) -> PAPoint:
        return self._value_1

    def _value_by_idx(self, idx):
        return self._value_0 + idx * (self._value_1 - self._value_0)

    def arr(self, sample_num, start_idx=0., end_idx=1.):
        return np.linspace(
            *itv_multi((start_idx, end_idx), (self._value_0, self._value_1)),
            sample_num, endpoint=False
        )


class BezierCurve(SingleCurveValue):
    def __init__(self, value_0: PAPoint, value_1: PAPoint, bezier_segment=None):
        if bezier_segment is None:
            self._bezier_segment = s_curve(0.5)
        elif isinstance(bezier_segment, BezierSegment):
            self._bezier_segment = bezier_segment
        else:
            raise TypeError("bezier_segment must be BezierSegment")
        self._value_0 = value_0
        self._value_1 = value_1

    @property
    def start(self) -> PAPoint:
        return self._value_0

    @property
    def end(self) -> PAPoint:
        return self._value_1

    def _value_by_idx(self, idx):
        return self._value_0 + self._bezier_segment.idx(idx) * self._value_1

    def arr(self, sample_num, start_idx=0., end_idx=1.):
        raw_bezier = self._bezier_segment.array(
            start_idx,
            end_idx, sample_num
        )
        return self._value_0 + raw_bezier.repeat(2).reshape(-1, 2) * (self._value_1 - self._value_0)


class CosineCurve(SingleCurveValue):
    def __init__(self, value_0: PAPoint, value_1: PAPoint, repeat_times=1., phase=0.):
        self._value_0 = value_0
        self._value_1 = value_1
        self._repeat_times = repeat_times
        self._phase = phase

    def _value_mapping(self, cos_value):
        return (self._value_0 - self._value_1) * ((np.repeat(cos_value, 2).reshape(-1, 2) + 1) / 2) + self._value_1

    @property
    def start(self) -> PAPoint:
        return self._value_mapping(np.cos(self._phase * C))

    @property
    def end(self) -> PAPoint:
        return self._value_mapping(np.cos((self._phase + self._repeat_times) * C))

    def _value_by_idx(self, idx):
        return self._value_mapping(np.cos((self._phase + self._repeat_times * idx) * C))

    def arr(self, sample_num, start_idx=0., end_idx=1.):
        return self._value_mapping(
            np.cos(
                np.linspace(
                    *itv_multi((start_idx, end_idx), (self._phase * C, (self._phase + self._repeat_times) * C)),
                    sample_num,
                    endpoint=False
                )
            )
        )


class CroppedCurve(CurveValue):
    def __init__(self, value: CurveValue, crop_itv: tuple):
        self._value = value
        self._crop_itv = crop_itv

    @property
    def start(self) -> PAPoint:
        return self._value.value_by_idx(self._crop_itv[0])

    @property
    def end(self) -> PAPoint:
        return self._value.value_by_idx(self._crop_itv[1])

    def _value_by_idx(self, idx):
        return self._value.value_by_idx(itv_multi((idx, 1), self._crop_itv)[0])

    def arr(self, sample_num, start_idx=0., end_idx=1.):
        return self._value.arr(sample_num, *itv_multi((start_idx, end_idx), self._crop_itv))


def _valid_continuity(values: list[CurveValue]):
    for i in range(len(values) - 1):
        if np.any(values[i].end != values[i + 1].start):
            return False
    return True

def _ratio_normalize(ratios):
    return [x / sum(ratios) for x in ratios]

class JointCurve(CurveValue):
    def __init__(self, value_units: list[CurveValue], ratios: list[int | float]):
        if not _valid_continuity(value_units):
            raise ValueError
        self._components = value_units
        self._ratios = _ratio_normalize(ratios)

    @property
    def components(self):
        return self._components

    @property
    def ratios(self):
        return self._ratios

    @property
    def start(self) -> PAPoint:
        return self._components[0].start

    @property
    def end(self) -> PAPoint:
        return self._components[-1].end

    def domains(self):
        return [(sum(self._ratios[:i]), sum(self._ratios[:i+1])) for i in range(len(self._ratios))]

    def idx_domain(self, idx):
        if idx == 1:
            return 1., len(self._components) - 1
        else:
            for i, dm in enumerate(self.domains()):
                if idx in dm:
                    return itv_divide((idx, 1), dm)[0], i

    def _value_by_idx(self, idx):
        idx_2, seg_i = self.idx_domain(idx)
        return self._components[seg_i].value_by_idx(idx_2)

    def arr(self, sample_num, start_idx=0., end_idx=1.):
        arr_itv = (start_idx, end_idx)
        sub_sample_nums_and_sub_itv = [
            (
                i,
                int(sample_num * itv_length(itv_cross(arr_itv, d_itv)) / itv_length(arr_itv)),
                itv_divide(itv_cross(arr_itv, d_itv), d_itv)
            )
            for i, d_itv in enumerate(self.domains()) if itv_valid(itv_cross(arr_itv, d_itv))
        ]
        sample_count = sum(x[1] for x in sub_sample_nums_and_sub_itv)
        extra = sample_num - sample_count
        arrays = []
        for i, sub_sample, sub_itv in sub_sample_nums_and_sub_itv:
            if i < extra:
                arrays.append(self._components[i].arr(
                    sub_sample + 1,
                    *sub_itv
                ))
            else:
                arrays.append(self._components[i].arr(
                    sub_sample,
                    *sub_itv
                ))
        return np.concatenate(arrays)


class OverlaidCurve(CurveValue):
    def __init__(self, components: list[CurveValue]):
        self._components = components

    @property
    def components(self):
        return self._components

    @property
    def start(self) -> PAPoint:
        return pa_sum([x.start for x in self._components])

    @property
    def end(self) -> PAPoint:
        return pa_sum([x.end for x in self._components])

    def _value_by_idx(self, idx):
        return sum(x._value_by_idx(idx) for x in self._components)

    def arr(self, sample_num, start_idx=0., end_idx=1.):
        return sum(x.arr(sample_num, start_idx, end_idx) for x in self._components)

    def __mul__(self, other):
        if not isinstance(other, CurveValue):
            raise TypeError
        if isinstance(other, OverlaidCurve):
            return OverlaidCurve(self.components + other.components)
        else:
            return OverlaidCurve(self.components + [other])


def cv_join(*args):
    if all(isinstance(arg, CurveValue) for arg in args):
        return JointCurve(list(args), ratios=[1 for _ in args])
    else:
        raise TypeError


def fxv(*args, p=None, a=None):
    if len(args) == 0:
        if a is None and p is None:
            return FixedValue(e_point())
        elif p is None:
            return FixedValue(a_point(a))
        elif a is None:
            return FixedValue(p_point(p))
        else:
            return FixedValue(pa_point(p, a))
    elif len(args) == 1:
        if a is None and p is None:
            return FixedValue(p_point(args[0]))
        elif a is not None:
            return FixedValue(pa_point(args[0], a))
        else:
            return FixedValue(pa_point(p, args[0]))
    elif len(args) == 2:
        return FixedValue(pa_point(args[0], args[1]))

def lnv(*args, p=None, a=None):
    if len(args) == 0:
        if a is None and p is None:
            return FixedValue(e_point())
        elif p is None and isinstance(a, (tuple, list)) and all(isinstance(x, (int, float)) for x in a) and len(a) == 2:
            return LinearValue(a_point(a[0]), a_point(a[1]))
        elif a is None and isinstance(p, (tuple, list)) and all(isinstance(x, (int, float)) for x in p) and len(p) == 2:
            return LinearValue(p_point(p[0]), p_point(p[1]))
        elif isinstance(a, (tuple, list)) and isinstance(p, (tuple, list)) and all(isinstance(x, (int, float)) for x in list(p) + list(a)) and len(a) == len(p) == 2:
            return LinearValue(pa_point(p[0], a[0]), pa_point(p[1], a[1]))
        else:
            raise TypeError
    elif len(args) == 1:
        raise TypeError
    elif len(args) == 2:
        if all(isinstance(arg, (int, float)) for arg in args):
            return lnv(p=args)
        elif all(isinstance(arg, (list, tuple)) for arg in args):
            return lnv(p=args[0], a=args[1])
    elif len(args) == 4 and all(isinstance(arg, (int, float)) for arg in args):
        return lnv(p=list(args)[:2], a=list(args)[2:])


if __name__ == '__main__':
    pass
