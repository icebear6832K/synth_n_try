from event import *
from random import random

def timbre(*args):
    if all(isinstance(arg, (int, float)) for arg in args):
        print()
        return CompositeEvent(
            [ritv() for _ in args],
            [SingleSignalEvent(fxv(p=12*np.log2(i+1), a=arg)) for i, arg in enumerate(args)]
        )
    else:
        raise TypeError

def scale(*args):
    if all(isinstance(arg, (int, float)) for arg in args):
        return CompositeEvent(
            [ritv(i/len(args), (i+1)/len(args)) for i in range(len(args))],
            [SingleSignalEvent(fxv(p=arg)) for arg in args]
        )
    else:
        raise TypeError

def major_scale():
    return scale(0, 2, 4, 5, 7, 9, 11)

def main_try():
    sgn4 = SingleSignalEvent(fxv(0) * BezierCurve(a_point(-10), e_point(), bezier_segment=c_curve(0, 1)) * BezierCurve(e_point(), a_point(-10), bezier_segment=c_curve(1, 0)))
    sgn5 = SingleSignalEvent(fxv(3) * BezierCurve(a_point(-10), e_point(), bezier_segment=c_curve(0, 1)) * BezierCurve(e_point(), a_point(-10), bezier_segment=c_curve(1, 0)))
    sgn6 = CompositeEvent(
        [ritv(), ritv()],
        [sgn4, sgn5]
    )
    sgn8 = SingleSignalEvent(fxv(0) * BezierCurve(a_point(-10), e_point(), bezier_segment=c_curve(0, 1)) * BezierCurve(e_point(), a_point(-10), bezier_segment=c_curve(1, 0)))
    sgn81 = SingleSignalEvent(fxv(-12) * BezierCurve(a_point(-10), e_point(), bezier_segment=c_curve(0, 1)) * BezierCurve(e_point(), a_point(-10), bezier_segment=c_curve(1, 0)))
    sgn9 = SingleSignalEvent(fxv(4) * BezierCurve(a_point(-10), e_point(), bezier_segment=c_curve(0, 1)) * BezierCurve(e_point(), a_point(-10), bezier_segment=c_curve(1, 0)))
    sgn10 = CompositeEvent(
        [ritv(), ritv(), ritv()],
        [sgn8, sgn81, sgn9]
    )
    sgn11 = CompositeEvent(
        [ritv(0, 0.5), ritv(0.5, 1)],
        [sgn6, sgn10]
    )
    tbr = timbre(0, -1, -1.3, -3, -5, -6, -7, -8, -10, -6, -8, -10)
    rst0 = OverlaidEvent(
        [sgn11, tbr]
    )
    trl = SingleSignalEvent(CosineCurve(p_point(-0.3), e_point(), repeat_times=250))
    rst1 = OverlaidEvent(
        [rst0, trl, major_scale()]
    )
    rst1.synth(60)

a = CompositeEvent(
    [ritv(t/8, (t+1)/8) for t in range(6)] + [ritv(0.75, 1)], [SingleSignalEvent(fxv(p)) for p in (0, -1, -8, -9, -16, -17, -24)]
)
b = CompositeEvent(
    [ritv() for _ in (0, -1, -1.3, -3, -2, -3, -5, -6, -6, -5.5, -8.6, -7, -7, -9, -7, -7, -9, -11, -13, -14, -14, -15, -16, -18, -19, -14, -15, -16, -29, -18, -19, -14, -19, -20, -30, -49, -33, -40, -36, -50)],
    [SingleSignalEvent(fxv(p=12*np.log2(i+1), a=arg)) for i, arg in enumerate((0, -1, -1.3, -3, -2, -3, -5, -6, -6, -5.5, -8.6, -7, -7, -9, -7, -7, -9, -11, -13, -14, -14, -15, -16, -18, -19, -14, -15, -16, -29, -18, -19, -14, -19, -20, -30, -49, -33, -40, -36, -50))]
)


c = CompositeEvent([ritv(0, 0.6), ritv(0.2, 0.8), ritv(0.2, 0.9), ritv(0.4, 1), ritv(0.6, 1), ritv(0.6, 1), ritv(0.8, 1)], [SingleSignalEvent(fxv(12*x)) for x in (-2, -1, 0, 1, 2, 0, -1)]).grow()
c2 = SingleSignalEvent(BezierCurve(a_point(-5), e_point(), bezier_segment=c_curve(0, 0.5)) * BezierCurve(e_point(), a_point(-5), bezier_segment=c_curve(0.5, 0))).grow()
d = SingleSignalEvent(CosineCurve(p_point(-0.8), e_point(), repeat_times=100)).grow(2)
c2.show()
c2.synth(1)
c3 = (c * c2 * d * CompositeEvent([ritv(), ritv()], [SingleSignalEvent(fxv(0)), SingleSignalEvent(fxv(7))])).loop(10) * b
c3.show()
z0 = a.grow(3) * c3
z0.synth(10)
z0.show()

z = (a * b).grow() * CompositeEvent(
    [ritv(), ritv(), ritv()],
    [SingleSignalEvent(BezierCurve(pa_point(11.7, 0), pa_point(12.3, -3), c_curve(0.5, 0))), SingleSignalEvent(fxv(p=0)), SingleSignalEvent(BezierCurve(p_point(-11.5), p_point(-12), c_curve(0, 1)))]
) * SingleSignalEvent(CosineCurve(p_point(-0.5), p_point(0.2), repeat_times=100)).grow()

# c.synth(50)

