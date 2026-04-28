"""
Event-based sound synthesis and compositional structure.

This module defines the main event layer of the prototype. An `Event` is a
compositional unit that can render pitch-amplitude trajectories, flatten nested
structures, visualize data, and synthesize audio.

The framework treats sound as a vectorized event structure. A curve or event is
understood as a description of how a more basic sonic existence-state is
modified across time. Events can be joined sequentially, combined simultaneously,
overlaid, looped, and grown into higher structural scales.

Current implementation scope:
    T -> (P, A)

Each time point maps to a pitch-amplitude pair. Future extensions may support
spectral/noise-field events of the form:
    T -> (P -> A)

Typical use:
    from event import SingleSignalEvent
    from curveValue import lnv
    from pAPoint import pa_point

    curve = lnv(pa_point(0, -3), pa_point(12, -3))
    event = SingleSignalEvent(curve)
    event.show(duration=200)
    event.synth(duration_second=2)
"""
from __future__ import annotations
from abc import ABC, abstractmethod
import numpy as np
from numpy import ndarray
from bezierCalculator import c_curve
from curveValue import CurveValue, fxv, lnv, CosineCurve, BezierCurve
from interval import RefPointObj, RelativeInterval, AbsInterval, rf, ritv, aitv, ritv_cross
from dataShowing import plot_multiple_xyz
from pAPoint import PAPoint, p_point, pa_point, a_point, e_point
from itertools import product
from synth import save_wav, generate_raw_sine_wave, SR


E_SR = 100
SCALE_RATIO = SR / E_SR

def linear_interpolate(arr, k):
    n = len(arr)
    x = np.linspace(0, n - 1, n)
    x_new = np.linspace(0, n - 1, k)
    return np.column_stack([np.interp(x_new, x, arr[:, i]) for i in range(arr.shape[1])])

class Event(ABC):
    def __init__(self, layer_tag=None):
        self._layer_tag = layer_tag

    @property
    def layer_tag(self):
        return self._layer_tag

    @abstractmethod
    def render(self, duration=E_SR):
        pass

    @abstractmethod
    def flatten_render(self, duration=E_SR):
        pass

    @abstractmethod
    def grow(self, level=1):
        pass

    @property
    @abstractmethod
    def min_required_duration(self) -> float:
        pass

    def show(self, duration=None):
        data_list = []
        if duration is None:
            duration = self.min_required_duration + 50
        elif duration < self.min_required_duration:
            raise ValueError("Duration must be greater than Event's minimal required duration")

        for itv, val_arr in self.flatten_render(duration):
            t = np.linspace(*itv.start_end, int(itv.len))
            data_list.append([t, val_arr[:, 0], val_arr[:, 1]])
        plot_multiple_xyz(data_list, duration)

    def wave_data(self, duration_second: float | int):
        rst_arr = np.zeros(shape=(int(duration_second * SR) + 100))
        for itv, arr in self.flatten_render(int(duration_second * E_SR)):
            itp_arr = linear_interpolate(arr, int(itv.len * SCALE_RATIO))
            freq_data = 261 * np.exp2(itp_arr[:, 0] / 12)
            amp_data = np.exp2(itp_arr[:, 1])
            sub_start = int(itv.start * SCALE_RATIO)
            rst_arr[sub_start:sub_start+len(itp_arr)] += generate_raw_sine_wave(freq_data, amp_data)
        return rst_arr

    def synth(self, duration_second=10.):
        save_wav(self.wave_data(duration_second), 'event_synth')

    def overlay(self, other):
        if not isinstance(other, Event):
            raise TypeError
        elif isinstance(self, OverlaidEvent) and isinstance(other, OverlaidEvent):
            return OverlaidEvent(self.operating_events + other.operating_events)
        elif isinstance(other, OverlaidEvent):
            return OverlaidEvent([self] + other.operating_events)
        elif isinstance(self, OverlaidEvent):
            return OverlaidEvent(self.operating_events + [other])
        else:
            return OverlaidEvent([self, other])

    def __mul__(self, other):
        if not isinstance(other, Event):
            raise TypeError
        else:
            return self.overlay(other)

    def loop(self, times):
        if not isinstance(times, int) or times < 1:
            raise TypeError
        else:
            return CompositeEvent(
                [ritv(t/times, (t+1)/times) for t in range(times)], [self for _ in range(times)]
            )

    def combine(self, other):
        if not isinstance(other, Event):
            raise TypeError
        else:
            return CompositeEvent(
                [ritv(), ritv()], [self, other]
            )

    def join(self, other, ratio=None):
        if ratio is None:
            ratio = 1
        elif not isinstance(ratio, int | float):
            raise TypeError
        if not isinstance(other, Event):
            raise TypeError
        else:
            return CompositeEvent(
                [ritv(0, 1/(ratio+1)), ritv(1/(ratio+1), 1)], [self, other]
            )


class SignalEvent(Event):
    def render(self, duration=E_SR):
        return self.arr(duration)

    def flatten_render(self, duration=E_SR):
        return [(aitv(0, duration), self.arr(duration))]

    def grow(self, level=1):
        if level == 1:
            return CompositeEvent(
                    [ritv()], [self]
            )
        else:
            return CompositeEvent(
                [ritv()], [self.grow(level - 1)]
            )

    @property
    @abstractmethod
    def min_required_duration(self) -> float:
        pass

    @abstractmethod
    def arr(self, duration=E_SR) -> np.ndarray:
        pass

    @property
    @abstractmethod
    def start(self) -> PAPoint:
        pass

    @property
    @abstractmethod
    def end(self) -> PAPoint:
        pass

    def sgn_join(self, other, ref=None) -> JointSignalEvent:
        if isinstance(ref, RefPointObj):
            ref_point = ref
        elif ref is None:
            ref_point = rf(0.5)
        else:
            raise TypeError
        if not isinstance(other, SignalEvent):
            raise TypeError
        elif isinstance(self, JointSignalEvent) and isinstance(other, JointSignalEvent):
            return JointSignalEvent(
                [rfp * ritv(0, ref_point) for rfp in self.ref_points + rf(1)] + [rfp * ritv(ref_point, 1) for rfp in other.ref_points],
                self.signal_values + other.signal_values
            )
        elif isinstance(self, JointSignalEvent):
            return JointSignalEvent(
                [rfp * ritv(0, ref_point) for rfp in self.ref_points] + [ref_point],
                self.signal_values + [other]
            )
        elif isinstance(other, JointSignalEvent):
            return JointSignalEvent(
                [ref_point] + [rfp * ritv(ref_point, 1) for rfp in other.ref_points],
                [self] + other.signal_values
            )
        else:
            return JointSignalEvent([ref_point], [self, other])


class SingleSignalEvent(SignalEvent):
    def __init__(self, value: CurveValue):
        super().__init__(layer_tag=0)
        self._value = value

    @property
    def value(self):
        return self._value

    def arr(self, duration=E_SR) -> np.ndarray:
        return self._value.arr(int(duration))

    @property
    def start(self) -> PAPoint:
        return self._value.start

    @property
    def end(self) -> PAPoint:
        return self._value.end

    @property
    def min_required_duration(self):
        return 0


def is_continuous(signal_values: list[SignalEvent]):
    for val_0, val_1 in zip(signal_values[:-1], signal_values[1:]):
        if val_0.end.any() != val_1.start.any():
            return False
    return True

class JointSignalEvent(SignalEvent):
    def __init__(self, reference_points: list[RefPointObj], signal_values: list[SignalEvent]):
        super().__init__(layer_tag=0)
        if len(signal_values) != (len(reference_points) + 1):
            raise ValueError("Length of reference_points and values are inconsistent")
        if not is_continuous(signal_values):
            raise ValueError("Signal values are not continuous")
        self._signal_values = signal_values
        self._ref_points = reference_points

    @property
    def signal_values(self):
        return self._signal_values

    @property
    def ref_points(self):
        return self._ref_points

    @property
    def start(self):
        return self._signal_values[0].start

    @property
    def end(self):
        return self._signal_values[-1].end

    @property
    def intervals(self):
        intervals = []
        for i in range(len(self._signal_values)):
            if i == 0:
                intervals.append(ritv(end=self._ref_points[0]))
            elif i == len(self._signal_values) - 1:
                intervals.append(ritv(start=self._ref_points[i - 1]))
            else:
                intervals.append(ritv(self._ref_points[i - 1], self._ref_points[i]))
        return intervals

    @property
    def min_required_duration(self):
        return max(itv.min_required_length_for_result(val.min_required_duration) for itv, val in zip(self.intervals, self._signal_values))

    def arr(self, duration=E_SR) -> np.ndarray:
        if duration <= self.min_required_duration:
            raise ValueError("Event Duration must be at least {}".format(self.min_required_duration))
        duration_aitv = aitv(0, duration)
        arrays = [val.arr(int((itv * duration_aitv).len)) for itv, val in zip(self.intervals, self._signal_values)]
        return np.concatenate(arrays)


class CompositeEvent(Event):
    def __init__(self, intervals: list[RelativeInterval], events: list[Event]):
        max_layer = max(evt.layer_tag for evt in events)
        sub_events = [
            (evt if evt.layer_tag == max_layer else evt.grow(max_layer - evt.layer_tag))
            for evt in events
        ]
        super().__init__(max_layer + 1)
        self._intervals = intervals
        self._sub_events = sub_events

    def grow(self, level=1):
        return CompositeEvent(
            self._intervals,
            [x.grow(level) for x in self._sub_events]
        )

    @property
    def intervals(self):
        return self._intervals

    @property
    def sub_events(self):
        return self._sub_events

    @property
    def min_required_duration(self):
        return max(itv.min_required_length_for_result(val.min_required_duration)
                   for itv, val in zip(self._intervals, self._sub_events))

    def render(self, duration=E_SR):
        rst = []
        duration_aitv = aitv(0, duration)
        for itv, evt in zip(self._intervals, self._sub_events):
            sub_aitv = (itv * duration_aitv).to_int()
            sub_rendered = evt.render(sub_aitv.len)
            rst.append((sub_aitv, sub_rendered))
        return rst

    def flatten_render(self, duration=E_SR):
        rst = []
        duration_aitv = aitv(0, duration)
        for itv, evt in zip(self._intervals, self._sub_events):
            sub_aitv = (itv * duration_aitv).to_int()
            sub_rendered = evt.flatten_render(sub_aitv.len)
            rst += [(sub_aitv_2 + sub_aitv.start, sub_evt) for sub_aitv_2, sub_evt in sub_rendered]
        return rst


def _rebase_sub_intervals(sub_list, parent_start, inter_start, inter_end):
    """
    將 `sub_list` (其中元素形如 ( (sub_s, sub_e), sub_data ))
    從「相對於 parent_start」的座標系，轉到「相對於 inter_start」的座標系下，
    並且只保留落在 [inter_start, inter_end] 裡的部分。

    回傳新的 list, 其區間都在 [0, inter_end - inter_start] 之間。
    """
    new_list = []
    for (sub_itv, sub_data) in sub_list:
        # 原本的絕對區間
        abs_s = parent_start + sub_itv.start
        abs_e = parent_start + sub_itv.end
        # 與 [inter_start, inter_end] 求交集
        rebased_start = max(abs_s, inter_start)
        rebased_end   = min(abs_e, inter_end)

        if rebased_end > rebased_start:
            # 轉成相對座標 => 以 inter_start 為 0
            local_s = rebased_start - inter_start
            local_e = rebased_end   - inter_start
            new_list.append((AbsInterval(local_s, local_e), sub_data))
    return new_list

def _interval_cross(obj1: list[tuple[AbsInterval, list | np.ndarray]], obj2: list[tuple[AbsInterval, list | np.ndarray]]):
    """
    多層結構交集:
    obj1, obj2 = [
        ( (start, end), sub ),  # sub 可能是 np.ndarray 或下一層 list
        ...
    ]
    若 sub 是 array => 做陣列切片
    若 sub 是 list  => 先把子區間轉到「交集區間」的局部座標，再遞迴交集
    """
    obj1_sorted = sorted(obj1, key=lambda x: x[0].start)
    obj2_sorted = sorted(obj2, key=lambda x: x[0].start)
    result = []
    for (itv1, sub1), (itv2, sub2) in product(obj1_sorted, obj2_sorted):
        itvc = itv1 % itv2
        if itvc:
            # case 1: 兩邊都是 array => 底層直接做切片+相加
            if isinstance(sub1, np.ndarray) and isinstance(sub2, np.ndarray):
                arr_sum = sub1[itvc.start - itv1.start : itvc.end - itv1.start] + sub2[itvc.start - itv2.start : itvc.end - itv2.start]
                result.append((itvc, arr_sum))

            # case 2: 兩邊都是 list => 先 rebase 到 (0, ec - sc) 區間，再做「子層交集」
            elif isinstance(sub1, list) and isinstance(sub2, list):
                new_sub1 = _rebase_sub_intervals(sub1, itv1.start, *itvc.start_end)
                new_sub2 = _rebase_sub_intervals(sub2, itv2.start, *itvc.start_end)
                # 以上把子區間都轉到「父層交集 itvc」的局部座標
                # 再遞迴交集
                child_cross = _interval_cross(new_sub1, new_sub2)
                if child_cross:
                    # child_cross 本身的座標都在 [0, ec - sc] 裡，
                    # 但我們要以 (sc, ec) 作為這層區間，包住子結果
                    result.append((itvc, child_cross))
    return result

def _overlay_rendering(rendered: list[tuple[AbsInterval, list | np.ndarray]],
                       layer: int,
                       other: Event,
                       duration: int):
    if layer == other.layer_tag:
        if layer > 0:
            return _interval_cross(rendered, other.render(duration))
        else:
            return rendered + other.render(duration)
    elif layer > other.layer_tag:
        result = []
        for itv, sub_rendered in rendered:
            result.append((itv, _overlay_rendering(sub_rendered, layer - 1, other, itv.len)))
        return result
    else:
        raise NotImplementedError

def _flatten_rendered_structure(rendered: list[tuple[AbsInterval, list | np.ndarray]]) -> list[tuple[AbsInterval, np.ndarray]]:
    rst = []
    for itv, sub_rendered in rendered:
        if isinstance(sub_rendered, ndarray):
            rst.append((itv, sub_rendered))
        else:
            rst.extend([(sub_itv + itv.start, sub_sub) for sub_itv, sub_sub in _flatten_rendered_structure(sub_rendered)])
    return rst

class OverlaidEvent(Event):
    def __init__(self, events: list[Event]):
        self._operating_events = sorted(events, key=lambda x: x.layer_tag, reverse=True)
        super().__init__(self._operating_events[0].layer_tag)

    @property
    def operating_events(self):
        return self._operating_events

    @property
    def min_required_duration(self) -> float:
        return max(evt.min_required_duration for evt in self._operating_events)

    def render(self, duration=E_SR):
        rendered = self._operating_events[0].render(duration)
        for evt in self._operating_events[1:]:
            rendered = _overlay_rendering(rendered, self.layer_tag, evt, duration)
        return rendered

    def flatten_render(self, duration=E_SR):
        return _flatten_rendered_structure(self.render(duration))

    def grow(self, level=1):
        return OverlaidEvent([evt.grow(level) for evt in self._operating_events])


def fxv_event(*args):
    return SingleSignalEvent(fxv(*args))


def combine(events: list[Event]) -> CompositeEvent:
    return CompositeEvent(
        [ritv() for _ in events], events
    )

def join(events: list[Event]) -> CompositeEvent:
    m = len(events)
    return CompositeEvent(
        [ritv(i/m, (i+1)/m) for i in range(m)], events
    )


if __name__ == '__main__':
    a = join(
        [fxv_event(i) for i in (36, 35, 28, 27, 20, 19, 12, 11, 4, 3, -4, -5, -12, -13, -20, -21, -28, -29, -36)]
    ).grow(2)
    a.show()
    a2 = combine([SingleSignalEvent(lnv(p=(i*12, i*12), a=(-1+i, 2-i))) for i in range(-3, 3)]).grow(2)
    a3 = combine([SingleSignalEvent(CosineCurve(pa_point(12*np.log2(i+1), t), pa_point(12*np.log2(i+1)-0.5, t), repeat_times=10))
                  for i, t in enumerate([2, 1, 0, -1, -3, -1, -1, -2, -3, -4, -3, -2, -3, -5, -5, -5, -4, -6, -5, -7, -8, -6, -9, -9, -10, -9.4, -7.8, -12, -10, -13])]).grow(1)
    a2.show()
    a3.show()
    (a * a3).show()
    (a * a3 * a2).synth(10)
    c = SingleSignalEvent(BezierCurve(pa_point(-1, -6), e_point(), c_curve(0.2, 1))).grow(3)
    c.show()
    (a * a2 * a3 * c).show()
    (a * a2 * a3 * c).synth(10)
