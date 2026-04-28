"""
Array-structure helper module.

This module defines a small NumPy ndarray subclass pattern used by the rest of
this prototype. `ArrStruct` allows compact vector-like objects to behave like
NumPy arrays while still exposing named accessors in subclasses.

In the current project, this is mainly used by `PAPoint`, which represents a
pitch-amplitude vector. `SampleObj` is only a minimal example showing how a
custom array object can expose semantic fields such as `a()`, `b()`, and `c()`.

Typical use:
    from arrStruct import ArrStruct

    class MyPoint(ArrStruct):
        def __new__(cls, x, y):
            obj = np.asarray([x, y]).view(cls)
            return obj
"""
import numpy as np

class ArrStruct(np.ndarray):
    def __new__(cls, *input_array):
        obj = np.asarray(input_array).view(cls)
        return obj

    def __array_finalize__(self, obj):
        if obj is None: return


class SampleObj(ArrStruct):
    def __new__(cls, a, b, c):
        obj = np.asarray([a, b, c]).view(cls)
        return obj

    def a(self):
        return self[0]

    def b(self):
        return self[1]

    def c(self):
        return self[2]


if __name__ == '__main__':
    n = SampleObj(12, 33, 475)
    n2 = SampleObj(1, 3, 5)
    print(n)
