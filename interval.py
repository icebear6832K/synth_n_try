"""
Absolute and relative interval system for nested event time.

This module defines the time-structure layer of the event framework. It provides
absolute intervals, relative intervals, and reference points that can be mapped
into one another. The goal is to make time itself compositional, so an event can
contain smaller events whose internal proportions are preserved inside a larger
parent interval.

`AbsInterval` represents a concrete time range. `RelativeInterval` represents a
range relative to another interval. `RefPointObj` represents a reusable reference
point such as the beginning, middle, end, or an offset/between relation.

Typical use:
    from interval import aitv, ritv, rf

    parent = aitv(0, 100)
    first_half = ritv(0, 0.5) * parent
    middle = rf(0.5) * parent
"""
from __future__ import annotations
from types import NoneType
from typing import Callable, Tuple, Union, List
import math
from dataclasses import dataclass, field, replace

_RefPoint = Callable[[float, float], float]


@dataclass(frozen=True)
class AbsInterval:
    _start: float | int
    _end: float | int

    @property
    def start(self) -> float | int:
        return self._start

    @property
    def end(self) -> float | int:
        return self._end

    @property
    def len(self) -> float | int:
        return self._end - self._start

    @property
    def start_end(self) -> tuple[float | int, float | int]:
        return self._start, self._end

    def to_int(self):
        return AbsInterval(int(self.start), int(self.end))

    def __bool__(self) -> bool:
        return is_valid_interval(self)

    def __mod__(self, other: AbsInterval) -> AbsInterval:
        return interval_intersection(self, other)

    def __add__(self, other):
        if isinstance(other, (int, float)):
            return AbsInterval(self._start + other, self._end + other)
        else:
            return NotImplemented

    def __sub__(self, other):
        if isinstance(other, (int, float)):
            return AbsInterval(self._start - other, self._end - other)
        else:
            return NotImplemented

    def __repr__(self) -> str:
        if self:
            return f"⊩{round(self._start, 2)} {round(self._end, 2)}⊣"
        else:
            return f"⊮{round(self._start, 2)} {round(self._end, 2)}⊣"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, AbsInterval):
            return NotImplemented
        return math.isclose(self._start, other.start) and math.isclose(self._end, other.end)

    def __gt__(self, other):
        if not isinstance(other, AbsInterval):
            return NotImplemented
        return self._end > other.end and self._start < other.start

    def __ge__(self, other):
        if not isinstance(other, AbsInterval):
            return NotImplemented
        return self._end >= other.end and self._start <= other.start

    def copy(self) -> AbsInterval:
        # 由於為不可變類別，直接回傳自己即可
        return self


def interval_intersection(itv1: AbsInterval, itv2: AbsInterval) -> AbsInterval:
    """計算兩個絕對區間的交集"""
    return AbsInterval(max(itv1.start, itv2.start), min(itv1.end, itv2.end))


def is_valid_interval(itv: AbsInterval) -> bool:
    """檢查區間是否有效（起點小於終點）"""
    return itv.start < itv.end


def aitv(start, end) -> AbsInterval:
    return AbsInterval(start, end)


def _start(itv_start: float, _: float) -> float:
    return itv_start


def _end(_: float, itv_end: float) -> float:
    return itv_end


def _ratio(ratio: float) -> _RefPoint:
    """
    根據比例定位的參考點
    傳回的函數會返回：itv_start + ratio * (itv_end - itv_start)
    """

    def func(itv_start: float, itv_end: float) -> float:
        return itv_start + ratio * (itv_end - itv_start)

    return func


@dataclass(frozen=True)
class RefPointDistance:
    ref1: _RefPoint
    ref2: _RefPoint


def ref_point_distance(rpd: RefPointDistance, itv_start: float, itv_end: float) -> float:
    """
    計算兩參考點在指定區間下的差距：
    即：ref2(itv_start, itv_end) - ref1(itv_start, itv_end)
    """
    return rpd.ref2(itv_start, itv_end) - rpd.ref1(itv_start, itv_end)


def _offset(ref: _RefPoint, amount: Union[float, RefPointDistance]) -> _RefPoint:
    """
    根據給定參考點偏移 amount 後的參考點
    若 amount 為數值，則直接加上；若為 RefPointDistance，則先計算兩參考點之差。
    """
    def func(itv_start: float, itv_end: float) -> float:
        base = ref(itv_start, itv_end)
        delta = amount if isinstance(amount, (int, float)) else ref_point_distance(amount, itv_start, itv_end)
        return base + delta

    return func


def _between(ref1: _RefPoint, ref2: _RefPoint, ratio: float) -> _RefPoint:
    """
    返回介於兩參考點之間依比例定位的新參考點。
    例如 ratio=0.5 表示中點。
    """
    def func(itv_start: float, itv_end: float) -> float:
        val1 = ref1(itv_start, itv_end)
        val2 = ref2(itv_start, itv_end)
        return val1 + ratio * (val2 - val1)

    return func


def _compose(ref: _RefPoint, base1: _RefPoint, base2: _RefPoint) -> _RefPoint:
    """
    組合參考點：
    以 base1 與 base2 所定義的絕對數值作為新的區間，
    再將原本的參考點 ref 映射到這個區間中。
    """
    def composed(s: float, e: float) -> float:
        return ref(base1(s, e), base2(s, e))

    return composed


class RefPointObj:
    def __init__(self, func: _RefPoint, descriptor: tuple = None):
        """
        :param func: 用來計算參考點的函式
        :param descriptor: 一個用來描述此參考點屬性之結構化資訊，
                           例如 ('ratio', 0.3, 'offset', 0.2) 或特殊字串 'start', 'end'
        """
        self.func = func
        # 若未指定 descriptor，則以函式的 id 作為描述（僅能作為最基本比較）
        self.descriptor = descriptor if descriptor is not None else ('id', id(func))

    def __call__(self, itv_start: float, itv_end: float) -> float:
        return self.func(itv_start, itv_end)

    def offset(self, amount: Union[float, RefPointDistance]) -> RefPointObj:
        """
        回傳一個新 RefPointObj，為目前參考點偏移 amount 後的結果
        """
        new_func = _offset(self.func, amount)
        # 將 descriptor 複製並附加 offset 的資訊
        new_descriptor = self.descriptor + (
        ('offset', amount) if isinstance(amount, (int, float)) else ('offset', 'RefPointDistance'),)
        return RefPointObj(new_func, new_descriptor)

    def between(self, other: RefPointObj, ratio: float) -> RefPointObj:
        """
        回傳一個新 RefPointObj，位於 self 與 other 之間，以 ratio 定位
        """
        new_func = _between(self.func, other.func, ratio)
        new_descriptor = (self.descriptor, 'between', other.descriptor, 'ratio', ratio)
        return RefPointObj(new_func, new_descriptor)

    def compose(self, base1: RefPointObj, base2: RefPointObj) -> RefPointObj:
        """
        以 base1 與 base2 定義的新區間，將 self 組合至該區間上
        """
        new_func = _compose(self.func, base1.func, base2.func)
        new_descriptor = (self.descriptor, 'compose', base1.descriptor, base2.descriptor)
        return RefPointObj(new_func, new_descriptor)

    def copy(self) -> RefPointObj:
        # 由於本身不會被改變，複製時回傳一個新的物件
        return RefPointObj(self.func, self.descriptor)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, RefPointObj):
            return NotImplemented
        # 這裡的相等性判斷根據 descriptor 進行，假設 descriptor 能夠充分描述邏輯上相等的條件
        return self.descriptor == other.descriptor

    def __hash__(self) -> int:
        return hash(self.descriptor)

    def __mul__(self, other):
        if isinstance(other, AbsInterval):
            return self(other.start, other.end)
        elif isinstance(other, RelativeInterval):
            return self.compose(other.start, other.end)

    def __repr__(self):
        return f"<RefPointObj {self.descriptor}>"


def rf(ref_ratio=None, off=None):
    if not isinstance(off, (int, float, RefPointDistance, NoneType)):
        raise TypeError
    if not isinstance(ref_ratio, (int, float, RefPointObj, NoneType)):
        raise TypeError
    if isinstance(ref_ratio, RefPointObj):
        return ref_ratio.offset(off) if off is not None else ref_ratio
    elif ref_ratio == 0 or ref_ratio is None:
        return RefPointObj(_start, ('start',)).offset(off) if off is not None else RefPointObj(_start, ('start',))
    elif ref_ratio == 1:
        return RefPointObj(_end, ('end',)).offset(off) if off is not None else RefPointObj(_end, ('end',))
    elif isinstance(ref_ratio, (int, float)):
        return RefPointObj(_ratio(ref_ratio), ('ratio', ref_ratio)).offset(off) if off is not None else RefPointObj(
            _ratio(ref_ratio), ('ratio', ref_ratio))
    else:
        raise TypeError


def mid(rfp0: RefPointObj, rfp1: RefPointObj):
    return rfp0.between(rfp1, 0.5)


def dst(rfp0: RefPointObj, rfp1: RefPointObj):
    return RefPointDistance(rfp0, rfp1)


def _affine_params(ref: RefPointObj) -> tuple[float, float]:
    val1 = ref(0, 1)  # f(0,1)= 0 + r*1 + delta = r + delta
    val2 = ref(0, 2)  # f(0,2)= 0 + r*2 + delta = 2*r + delta
    r = val2 - val1
    delta = val1 - r
    return r, delta


@dataclass(frozen=True)
class RelativeInterval:
    _rfp0: RefPointObj
    _rfp1: RefPointObj

    def __mul__(self, other):
        return mul_relative_interval(self, other)

    def __pow__(self, power, modulo=None):
        if isinstance(power, AbsInterval):
            return (self * power).to_int()

    def __mod__(self, other):
        if isinstance(other, RelativeInterval):
            return RelativeIntervalIntersection((self, other))
        elif isinstance(other, RelativeIntervalIntersection):
            return RelativeIntervalIntersection(tuple([self] + list(other.intervals)))
        else:
            raise TypeError

    @property
    def start(self) -> RefPointObj:
        return self._rfp0

    @property
    def end(self) -> RefPointObj:
        return self._rfp1

    @property
    def min_required_length(self) -> float:
        """
        計算使映射結果有效所需的最小區間長度。
        設：
            f₀ = s + r₀·L + δ₀,   f₁ = s + r₁·L + δ₁, 取 s = 0
        則 f₀ = r₀·L + δ₀, f₁ = r₁·L + δ₁，
        有效性要求： f₀ < f₁  → (r₁ - r₀)·L > (δ₀ - δ₁).

        定義 diff_r = r₁ - r₀, diff_δ = δ₀ - δ₁：
         - 若 diff_r > 0，則 L > diff_δ/diff_r（若 diff_δ/diff_r 為負，則任意 L > 0 即可）。
         - 若 diff_r == 0，則必須 δ₀ < δ₁；此時只要 L>0 即可。
         - 若 diff_r < 0，則無論 L 多大都無法滿足 f₀ < f₁。

        因此，若無法得到有效結果，回傳 None。
        """
        r0, delta0 = _affine_params(self._rfp0)
        r1, delta1 = _affine_params(self._rfp1)
        diff_r = r1 - r0
        diff_delta = delta0 - delta1

        if diff_r > 0:
            base = diff_delta / diff_r
            return base if base > 0 else 0.0
        elif diff_r == 0:
            if delta0 < delta1:
                return 0.0
            else:
                return math.inf
        else:
            return math.inf

    def min_required_length_for_result(self, target_length: float) -> float:
        """
        計算使得映射後的實體區間不僅有效，
        且其長度至少達 target_length，
        所需要的最小絕對區間長度 L。

        由 f0(s,s+L) = s + r0*L + delta0,
             f1(s,s+L) = s + r1*L + delta1，
        則映射後的區間長度為：
             f1 - f0 = (r1 - r0)*L + (delta1 - delta0)
                      = diff_r * L - diff_delta,
        其中 diff_r = r1 - r0, diff_delta = delta0 - delta1.

        要求 f1 - f0 >= target_length，同時必須滿足 f0 < f1。
        因此：
             (r1 - r0)*L - diff_delta >= target_length.
        當 diff_r > 0 時，解得：
             L >= (target_length + diff_delta) / diff_r.
        另外，為滿足 f0 < f1，有 L >= max{0, diff_delta/diff_r}.

        最終需要的 L 為：
             L_min^* = max( max{0, diff_delta/diff_r}, (target_length + diff_delta)/diff_r ).
        若 diff_r==0 則必須檢查映射後長度是否固定且 >= target_length，
        否則返回 math.inf；若 diff_r < 0 則返回 math.inf。
        """

        r0, delta0 = _affine_params(self._rfp0)
        r1, delta1 = _affine_params(self._rfp1)
        diff_r = r1 - r0
        diff_delta = delta0 - delta1  # 注意：原式中 f1 - f0 = diff_r * L - diff_delta

        if diff_r > 0:
            # 條件1：使得 f0 < f1，有 L >= max(0, diff_delta/diff_r)
            candidate1 = diff_delta / diff_r if diff_delta > 0 else 0.0
            # 條件2：使得 f1 - f0 >= target_length，有
            #   diff_r * L - diff_delta >= target_length  =>  L >= (target_length + diff_delta) / diff_r
            candidate2 = (target_length + diff_delta) / diff_r
            return max(candidate1, candidate2)
        elif diff_r == 0:
            # 此時映射後區間長度固定為 f1 - f0 = -diff_delta
            if -diff_delta >= target_length and delta0 < delta1:
                return 0.0  # 任意 L>0 均有效
            else:
                return math.inf
        else:
            return math.inf

    @property
    def required_length_range_strictly(self) -> Union[tuple[float, Union[float, None]], None]:
        """
        【層二】要求映射後結果除了有效之外，
        還必須落在原始 AbsInterval [s, s+L] 內，即：
          (a) f₀(s, s+L) ≥ s  →  r₀·L + δ₀ ≥ 0,
          (b) f₁(s, s+L) ≤ s+L  →  r₁·L + δ₁ ≤ L.

        以 s=0 表示：
          條件 (a)： r₀·L + δ₀ ≥ 0.
            - 若 r₀ > 0：則 L ≥ -δ₀/r₀.
            - 若 r₀ == 0：必須 δ₀ ≥ 0；否則無解.
            - 若 r₀ < 0：則 L ≤ -δ₀/r₀（前提是 -δ₀/r₀ > 0）.

          條件 (b)： r₁·L + δ₁ ≤ L  → (1 - r₁)·L ≥ δ₁.
            - 若 r₁ < 1：若 δ₁ > 0，則 L ≥ δ₁/(1 - r₁)；若 δ₁ ≤ 0，則此條件自動滿足.
            - 若 r₁ == 1：必須 δ₁ ≤ 0；否則無解.
            - 若 r₁ > 1：則 (1 - r₁) 為負，變成 L ≤ δ₁/(1 - r₁)（此時必須 δ₁ < 0）。

        另外，還需滿足基本有效性條件（即 min_required_length 的下限）。

        綜合上述，我們可以分別取出下界與上界：
         - 下界候選值：
            (i) L_valid = min_required_length（若存在，否則表示無法有效）。
            (ii) 若 r₀ > 0：L ≥ -δ₀/r₀.
            (iii) 若 r₁ < 1 且 δ₁ > 0：L ≥ δ₁/(1 - r₁).
         - 上界候選值：
            (iv) 若 r₀ < 0：L ≤ -δ₀/r₀.
            (v) 若 r₁ > 1：L ≤ δ₁/(1 - r₁).

        將所有有下界限制者取最大，所有有上界限制者取最小。
        若下界超過上界，則無法滿足條件，回傳 None。
        若只有下界，則回傳 (下界, None)；若只有上界，則回傳 (0, 上界)；若兩者皆有，則回傳 (下界, 上界)。
        若皆無限制，則視為 (0, None)。
        """
        r0, delta0 = _affine_params(self._rfp0)
        r1, delta1 = _affine_params(self._rfp1)

        # 先檢查基本有效性：必須能滿足 f₀ < f₁
        base = self.min_required_length
        if base is None:
            return None  # 永遠無法有效

        lower_candidates = [base]  # 至少必須大於或等於 base
        upper_candidates = []  # 收集可能的上界

        # 條件 (a)： f₀ ≥ 0  → r₀·L + δ₀ ≥ 0
        if r0 > 0:
            lower_candidates.append(-delta0 / r0)
        elif r0 == 0:
            if delta0 < 0:
                return None  # 無法滿足
        else:  # r0 < 0
            # r0·L + δ₀ ≥ 0  → L ≤ -δ₀/r0  (必須 -δ₀/r0 > 0)
            if -delta0 / r0 <= 0:
                return None
            upper_candidates.append(-delta0 / r0)

        # 條件 (b)： f₁ ≤ L  → r₁·L + δ₁ ≤ L  → (1 - r₁)·L ≥ δ₁
        if r1 < 1:
            if delta1 > 0:
                lower_candidates.append(delta1 / (1 - r1))
            # 若 delta1 ≤ 0，則條件自動成立，不需下界限制
        elif r1 == 1:
            if delta1 > 0:
                return None  # 無法滿足
        else:  # r1 > 1
            # (1 - r₁) 為負，條件變為 L ≤ δ₁/(1 - r₁)，注意此時 δ₁ 必須 < 0
            if delta1 >= 0:
                return None
            upper_candidates.append(delta1 / (1 - r1))  # 此值為正的上界

        lower_bound = max(lower_candidates) if lower_candidates else 0.0
        upper_bound = min(upper_candidates) if upper_candidates else None

        # 若有上界，則必須 lower_bound <= upper_bound
        if upper_bound is not None and lower_bound > upper_bound:
            return None

        # 回傳結果。若沒有上界限制，則視為 (lower_bound, None)；若下界為 0 而有上界，則 (0, upper_bound)。
        if upper_bound is None:
            return lower_bound, None
        else:
            return lower_bound, upper_bound

    @property
    def is_valid(self) -> bool:
        """
        若存在某個 L > 0 能使映射結果有效 (f₀ < f₁)，則返回 True。
        這裡以 min_required_length 不為 None 作為判斷依據。
        """
        return self.min_required_length is not None

    @property
    def is_strictly_valid(self) -> bool:
        """
        若存在某個 L > 0 能使映射結果除了有效外，
        還能完全落在 apply 的 AbsInterval 內 (f₀ ≥ s 且 f₁ ≤ s+L)，則返回 True。
        這裡以 required_length_range_strictly 不為 None 作為判斷依據。
        """
        return self.required_length_range_strictly is not None

    def is_strictly_valid_length(self, target_length: float) -> bool:
        if self.min_required_length > target_length:
            return False
        trg_itv = aitv(0, target_length)
        apl_itv = apply_relative_interval(self, trg_itv)
        if trg_itv >= apl_itv:
            return True
        else:
            return False

    def copy(self) -> RelativeInterval:
        return replace(self)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, RelativeInterval):
            return NotImplemented
        return self._rfp0 == other._rfp0 and self._rfp1 == other._rfp1

    def __hash__(self) -> int:
        return hash((self._rfp0, self._rfp1))

    def __repr__(self) -> str:
        return f"<RelativeInterval: {self._rfp0} ~ {self._rfp1}>"


def apply_relative_interval(rel_itv: RelativeInterval, abs_itv: AbsInterval) -> AbsInterval:
    """
    將相對區間映射到具體的絕對區間上
    """
    return AbsInterval(
        rel_itv.start(abs_itv.start, abs_itv.end),
        rel_itv.end(abs_itv.start, abs_itv.end)
    )

def compose_relative_interval(outer: RelativeInterval, inner: RelativeInterval) -> RelativeInterval:
    """
    將另一個相對區間作為基底，組合出一個新的相對區間
    """
    new_ref1 = outer.start.compose(inner.start, inner.end)
    new_ref2 = outer.end.compose(inner.start, inner.end)
    return RelativeInterval(new_ref1, new_ref2)

def mul_relative_interval(a: RelativeInterval, b: Union[RelativeInterval, AbsInterval]) -> Union[
    RelativeInterval, AbsInterval]:
    """
    依 b 的型態進行運算：
      - 若 b 為 RelativeInterval，返回 a 與 b 組合後的新 RelativeInterval
      - 若 b 為 AbsInterval，則將 a 映射到 b 上，返回新的 AbsInterval
    """
    if isinstance(b, AbsInterval):
        return apply_relative_interval(a, b)
    elif isinstance(b, RelativeInterval):
        return compose_relative_interval(a, b)
    else:
        raise TypeError("不支援此型態與 RelativeInterval 進行乘法運算。")


def ritv(start=None, end=None) -> RelativeInterval:
    start = rf(start)
    end = rf(end) if end is not None else rf(1)
    return RelativeInterval(start, end)


@dataclass(frozen=True)
class RelativeIntervalIntersection:
    _intervals: Tuple[RelativeInterval, ...] = field(default_factory=tuple)

    @property
    def intervals(self) -> Tuple[RelativeInterval, ...]:
        return self._intervals

    def __post_init__(self):
        # 在建構後自動將內部的 RelativeInterval 攤平
        flat: List[RelativeInterval] = []
        for itv in self._intervals:
            if isinstance(itv, RelativeIntervalIntersection):
                flat.extend(itv._intervals)
            else:
                flat.append(itv)
        object.__setattr__(self, 'intervals', tuple(flat))

    def apply(self, abs_itv: AbsInterval) -> AbsInterval:
        """
        對內部所有 RelativeInterval 物件分別 apply 至 abs_itv，
        並取它們的交集，最終結果為一個 AbsInterval。
        如果沒有任何 RelativeInterval，則回傳完整的 abs_itv。
        """
        if not self._intervals:
            return abs_itv
        result = None
        for rel in self._intervals:
            applied = apply_relative_interval(rel, abs_itv)
            if result is None:
                result = applied
            else:
                result = result % applied  # 利用 AbsInterval.__mod__ 計算交集
        return result

    def __mod__(self, other: Union[RelativeInterval, RelativeIntervalIntersection, AbsInterval]) -> Union[RelativeIntervalIntersection, AbsInterval]:
        """
        定義交集運算：
         - 若 other 為 RelativeInterval 或 RelativeIntervalIntersection，
           則返回新的 RelativeIntervalIntersection，其內部包含兩者的所有 RelativeInterval，
           並自動將列表攤平。
         - 若 other 為 AbsInterval，則直接對本物件 apply 該 AbsInterval，返回 AbsInterval。
        """
        if isinstance(other, RelativeInterval):
            new_intervals = list(self._intervals) + [other]
            return RelativeIntervalIntersection(tuple(new_intervals))
        elif isinstance(other, RelativeIntervalIntersection):
            new_intervals = list(self._intervals) + list(other._intervals)
            return RelativeIntervalIntersection(tuple(new_intervals))
        else:
            raise TypeError("不支援與此型態進行交集運算。")

    def __rmod__(self, other: Union[RelativeInterval, RelativeIntervalIntersection, AbsInterval]) -> Union[RelativeIntervalIntersection, AbsInterval]:
        return self.__mod__(other)

    def __mul__(self, other):
        if isinstance(other, AbsInterval):
            return self.apply(other)

    def __repr__(self) -> str:
        return f"<RelativeIntervalIntersection: {self._intervals}>"


def ritv_cross(ritv_list: list[RelativeInterval|RelativeIntervalIntersection]) -> RelativeIntervalIntersection:
    return RelativeIntervalIntersection(tuple(ritv_list))


if __name__ == '__main__':
    r1 = ritv(rf(), rf(8))
    print(r1 * aitv(0, 1))
    print(rf(8) * aitv(0, 1))
