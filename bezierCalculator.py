import matplotlib.pyplot as plt
import numpy as np


def _cubic_bezier(u, P0, P1):
    """
    三次貝茲曲線公式（假設起點為 0，終點為 1）：
      B(u) = 3*(1-u)^2*u * P0 + 3*(1-u)*u^2 * P1 + u^3
    u 可為 ndarray
    """
    return 3 * ((1 - u) ** 2) * u * P0 + 3 * (1 - u) * (u ** 2) * P1 + (u ** 3)

def _bezier_x(u, x1, x2):
    """
    利用參數 u 計算 x 座標，控制點分別為 x1 與 1 - x2
    """
    return _cubic_bezier(u, x1, 1 - x2)

def _bezier_y(u, y1, y2):
    """
    利用參數 u 計算 y 座標，控制點分別為 y1 與 1 - y2
    """
    return _cubic_bezier(u, y1, 1 - y2)

def _find_u_for_x_vec(target_x, x1, x2, tol=1e-5, max_iter=100):
    """
    向量化版本的二分搜尋法：
    給定目標 x 值陣列 target_x，假設 _bezier_x(u) 在 u∈[0,1] 單調遞增，
    同時反求所有 target_x 對應的參數 u，使得 _bezier_x(u) 與 target_x 接近。
    """
    target_x = np.asarray(target_x)
    # 初始化 u_low 與 u_high 為與 target_x 形狀相同的陣列
    u_low = np.zeros_like(target_x)
    u_high = np.ones_like(target_x)
    u_mid = (u_low + u_high) / 2.0

    for i in range(max_iter):
        u_mid = (u_low + u_high) / 2.0
        x_val = _bezier_x(u_mid, x1, x2)  # 此處 x_val 為陣列
        diff = x_val - target_x
        # 更新 u_low 與 u_high：當 _bezier_x(u_mid) 小於 target_x，則 u_low = u_mid，否則更新 u_high
        mask = diff < 0
        u_low[mask] = u_mid[mask]
        u_high[~mask] = u_mid[~mask]
        # 若全部收斂則提早結束
        if np.all(np.abs(diff) < tol):
            break
    return u_mid

def _uniform_bezier(cp_1, cp_2, num_points=1000, include_x=False):
    """
    以 x 座標均勻取樣整條曲線（x, y皆假設在 [0,1]）
    透過向量化的二分搜尋法同時求出所有點的參數 u，再計算 y 值。
    """
    (x1, y1), (x2, y2) = cp_1, cp_2
    # 均勻產生 0~1 之間的目標 x 值
    target_xs = np.linspace(0, 1, num_points, endpoint=False)
    # 向量化反求所有 target_x 對應的 u 值
    u_vals = _find_u_for_x_vec(target_xs, x1, x2)
    ys = _bezier_y(u_vals, y1, y2)
    if include_x:
        return target_xs, ys
    else:
        return ys

def _sample_bezier_segment(cp_1, cp_2, x_start, x_end, num_points=1000, include_x=False):
    """
    在指定 x 區間 [x_start, x_end] 上均勻取樣 num_points 個點，
    先產生區間內均勻的目標 x 值，再向量化反求對應參數 u，最後計算 y 值。
    """
    (x1, y1), (x2, y2) = cp_1, cp_2
    target_xs = np.linspace(x_start, x_end, num_points, endpoint=False)
    u_vals = _find_u_for_x_vec(target_xs, x1, x2)
    ys = _bezier_y(u_vals, y1, y2)
    if include_x:
        return target_xs, ys
    else:
        return ys

def _find_y_by_x(cp_1, cp_2, x):
    """
    在指定 x 區間 [x_start, x_end] 上均勻取樣 num_points 個點，
    先產生區間內均勻的目標 x 值，再向量化反求對應參數 u，最後計算 y 值。
    """
    (x1, y1), (x2, y2) = cp_1, cp_2
    u = _find_u_for_x_vec(x, x1, x2)
    return _bezier_y(u, y1, y2)


class BezierSegment:
    def __init__(self, x1, y1, x2, y2):
        self._ctrl_pts = ((x1, y1), (x2, y2))

    def array(self, start=0., end=1., num_points=1000, include_x=False):
        return _sample_bezier_segment(*self._ctrl_pts, start, end, num_points=num_points, include_x=include_x)

    def idx(self, idx=0.5):
        return _find_y_by_x(*self._ctrl_pts, idx)

    def show(self, start=0., end=1.):
        plt.figure(figsize=(8, 5))
        xs_segment, ys_segment = self.array(start, end, 10000, True)
        xs_full, ys_full = _uniform_bezier(*self._ctrl_pts, num_points=10000, include_x=True)
        plt.plot(xs_full, ys_full, color='darkgrey')
        plt.plot(xs_segment, ys_segment, color='blue', linewidth=3)
        plt.plot([0, self._ctrl_pts[0][0]], [0, self._ctrl_pts[0][1]], 'o--', color='darkred')
        plt.plot([1, 1 - self._ctrl_pts[1][0]], [1, 1 - self._ctrl_pts[1][1]], 'o--', color='darkred')
        plt.xlim(0, 1)
        plt.ylim(0, 1)
        plt.grid(True)
        plt.show()


def s_curve(x, y=0.):
    return BezierSegment(x, y, x, y)

def c_curve(x, y=0., scaling=1.):
    return BezierSegment(x * scaling, y * scaling, (1 - x) * scaling, (1 - y) * scaling)


if __name__ == '__main__':
    cc = c_curve(0.2, 0.8, 0.5)
    cc.show(0.3, 0.7)
    print(cc.array(0.5, 0.51, 1))
    print(cc.idx(0.5))
