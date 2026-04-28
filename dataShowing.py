import numpy as np
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from matplotlib.colors import LinearSegmentedColormap

LINE_WIDTH_MIN=0.2
LINE_WIDTH_MAX=3.0
COLOR_MAPPING_INTERVAL = (0, 10)
LINE_WIDTH_MAPPING_INTERVAL = (-30, 10)
FIG_SIZE = (8, 6)


def plot_multiple_xyz(data_list, x_lim_max):
    """
    一次繪製多組 (x, y, z) 資料於同一張圖表。

    參數說明：
    ----------
    data_list : list of tuples/list
        每個元素應為 (x, y, z)，其中 x, y, z 長度相同。
    lw_min, lw_max : float
        線條最細與最粗的寬度，用於 z<0 區間之線寬映射。
    figsize : tuple
        圖表大小 (width, height)，單位吋。

    視覺化規則：
    -----------
    1) z ≥ 0：
       - 顏色由 z=0 (藍) 線性漸變到 z=10 (紅)；
         z < 0 強制顯示「z=0 對應的藍色」，z > 10 則顯示「z=10 對應的紅色」。
    2) z < 0：
       - 線寬由 z=-10 (最細 lw_min) 線性漸變到 z=0 (最粗 lw_max)；
         z < -10 強制顯示「z=-10 對應的最細」，z > 0 則顯示「z=0 對應的最粗」。
    3) y 軸範圍：
       - 先找出所有資料的最小 y 與最大 y，若其差距 ≥ 4，則上下各保留 10% margin。
       - 若差距 < 4，則固定用 5 為範圍，區間為 (平均值 ± 2.5)。
    4) 最後產生一個 colorbar，顯示 0 ~ 10 的漸層（藍 -> 紅）。
    """

    # ====================================#
    # 0. 準備 figure, ax，以及全域 y_min, y_max
    # ====================================#
    fig, ax = plt.subplots(figsize=FIG_SIZE)

    global_y_min = np.inf
    global_y_max = -np.inf

    # 先準備一個從藍到紅的 colormap
    my_cmap = LinearSegmentedColormap.from_list(
        "my_cmap",
        [(0, "blue"), (1, "red")]  # 0->藍, 1->紅
    )
    # color 正規化：z=0 -> 0.0, z=10 -> 1.0
    color_norm = plt.Normalize(vmin=0, vmax=10)

    for (x, y, z) in data_list:
        # 確保是 numpy array
        x = np.asarray(x)
        y = np.asarray(y)
        z = np.asarray(z)

        # 更新全域 y 範圍
        local_y_min = y.min()
        local_y_max = y.max()
        global_y_min = min(global_y_min, local_y_min)
        global_y_max = max(global_y_max, local_y_max)

        # segment：每一對相鄰點 (N-1 段)
        points = np.column_stack((x, y)).reshape(-1, 1, 2)  # shape: (N,1,2)
        segments = np.concatenate([points[:-1], points[1:]], axis=1)  # (N-1,2,2)

        # 取 segment 起始點 (或可用平均) 當作該段 z 值
        z_seg = z[:-1]

        # (a) 計算顏色：只對 z ≥ 0 做漸變，<0 視為 0，>10 視為 10
        z_color_clipped = np.clip(z_seg, *COLOR_MAPPING_INTERVAL)
        # 轉成 RGBA
        seg_colors = my_cmap(color_norm(z_color_clipped))  # shape: (N-1,4)

        # (b) 計算線寬：只對 z < 0 做映射，-10=最細, 0=最粗；< -10 就固定最細，> 0 固定最粗
        z_lw_clipped = np.clip(z_seg, *LINE_WIDTH_MAPPING_INTERVAL)
        # 線性內插 -10 -> lw_min, 0 -> lw_max
        # lw = lw_min + ((z_lw_clipped - (-10)) / 10) * (lw_max - lw_min)
        lw_values = (LINE_WIDTH_MIN +
                     ((z_lw_clipped - LINE_WIDTH_MAPPING_INTERVAL[0]) /
                      (LINE_WIDTH_MAPPING_INTERVAL[1] - LINE_WIDTH_MAPPING_INTERVAL[0])) *
                     (LINE_WIDTH_MAX - LINE_WIDTH_MIN))

        # (c) 建立 LineCollection
        lc = LineCollection(
            segments,
            colors=seg_colors,
            linewidths=lw_values
        )
        ax.add_collection(lc)

    if not np.isfinite(global_y_min) or not np.isfinite(global_y_max):
        # 如果資料不正常(空值)，就不特別設定
        pass
    else:
        diff = global_y_max - global_y_min
        if diff >= 4:
            # 上下各加 10% 的 margin
            margin = 0.1 * diff
            y_min_plot = global_y_min - margin
            y_max_plot = global_y_max + margin
        else:
            # 固定範圍=5, 以中間值為中心
            center = 0.5 * (global_y_max + global_y_min)
            y_min_plot = center - 2.5
            y_max_plot = center + 2.5
        ax.set_ylim(y_min_plot, y_max_plot)

    ax.set_xlim(0, x_lim_max)
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    pass
