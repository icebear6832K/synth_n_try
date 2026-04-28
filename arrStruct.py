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
