import os

from matplotlib import patches

from data_analysis.df_merger import DfMerger
from data_analysis.df_reindexer import DfReindexer
from sink.bp_kalman import BpKalman
from data_analysis.pcap_proc import read_pcap_to_df
from sink.bp_quadlateration import BpQuadlateration
from data_analysis.rssi_filter import filter_and_smooth_max, filter_and_smooth_kalman, filter_and_smooth_max_median, \
    filter_and_smooth_mean

import numpy as np
import matplotlib.pyplot as plt
import math


def position_dataset_with_methods(exp_subdir, lap, filter_method, positioning_method, results_dir, true_point=None, true_path=None, n=2.0,
                                  resampling_rate="1s", resampling_rate_in_seconds=1):

    d1_file = "D1.pcap"
    d2_file = "D2.pcap"
    d3_file = "D3.pcap"
    d4_file = "D4.pcap"

    d1_coord = (0, 0)
    d2_coord = (0, 2.9)
    d3_coord = (4.2, 0)
    d4_coord = (4.2, 2.9)

    col_x = "x"
    col_y = "y"

    col_s1 = "signal1"
    col_s2 = "signal2"
    col_s3 = "signal3"
    col_s4 = "signal4"

    def load_pcaps(exp_dir):
        d1 = read_pcap_to_df(exp_dir + d1_file, lap)
        d2 = read_pcap_to_df(exp_dir + d2_file, lap)
        d3 = read_pcap_to_df(exp_dir + d3_file, lap)
        d4 = read_pcap_to_df(exp_dir + d4_file, lap)
        return d1, d2, d3, d4


    def filter_dfs_mean(dfs):
        return list(map(lambda df: filter_and_smooth_mean(df, "signal", "20s"), dfs))

    def filter_dfs_max(dfs):
        return list(map(lambda df: filter_and_smooth_max(df, "signal", "20s"), dfs))

    def filter_dfs_max_median(dfs):
        return list(map(lambda df: filter_and_smooth_max_median(df, "signal", "20s"), dfs))

    def filter_dfs_kalman(dfs):
        return list(map(lambda df: filter_and_smooth_kalman(df, "signal", "20s", filter_outliers=False), dfs))

    def filter_dfs_kalman_max(dfs):
        return list(map(lambda df: filter_and_smooth_kalman(df, "signal", "20s"), dfs))

    dfs = load_pcaps(exp_subdir)

    for idx, df in enumerate(dfs):
        print(f'df{idx}: {len(df)} rows')

    avg_len = np.mean([len(df) for df in dfs])
    print(f'average length: {avg_len}')

    if filter_method == "mean":
        filter_func = filter_dfs_mean
    elif filter_method == "max-mean":
        filter_func = filter_dfs_max
    elif filter_method == "max-median":
        filter_func = filter_dfs_max_median
    elif filter_method == "kalman":
        filter_func = filter_dfs_kalman
    elif filter_method == "kalman-max":
        filter_func = filter_dfs_kalman_max
    else:
        raise NotImplementedError(filter_method)

    filtered = filter_func(dfs)

    ridxr = DfReindexer(resampling_rate, "signal", "timestamp")
    filtered_ri = ridxr.reindex_dfs(*filtered)

    del filtered

    mrgr = DfMerger("signal", "timestamp")
    filtered_mrgd = mrgr.merge_dfs(filtered_ri).dropna()

    del filtered_ri

    quad = BpQuadlateration(d1_coord, d2_coord, d3_coord, d4_coord, n)
    def quadlaterate(row):
        row[col_x], row[col_y], row["tx"] = quad.quadlaterate(row[col_s1], row[col_s2], row[col_s3], row[col_s4]).x
        return row
    if positioning_method == "nlls":
        positioning_func = quadlaterate
    elif positioning_method == "nlls-kalman":
        row0 = filtered_mrgd.iloc[0]
        x0, y0, _ = quad.quadlaterate(row0[col_s1], row0[col_s2], row0[col_s3], row0[col_s4]).x
        kal_lstsq = BpKalman(np.array([x0, 0, y0, 0]))
        def kalman_lstsq_predict(row):
            x, y, _ = quad.quadlaterate(row[col_s1], row[col_s2], row[col_s3], row[col_s4]).x
            row[col_x], _, row[col_y], _ = kal_lstsq.predict_update(x, y, resampling_rate_in_seconds)
            return row
        positioning_func = kalman_lstsq_predict
    else:
        raise NotImplementedError()

    filtered_res = filtered_mrgd.apply(positioning_func, axis=1)

    del(filtered_mrgd)

    room_lim_x = (0, 4.2)
    room_lim_y = (0, 2.9)

    plot_padding = 0.5

    plot_lim_x = (room_lim_x[0] - plot_padding, room_lim_x[1] + plot_padding)
    plot_lim_y = (room_lim_y[0] - plot_padding, room_lim_y[1] + plot_padding)

    ax = filtered_res.plot(kind="scatter", x=col_x, y=col_y, xlim=plot_lim_x, ylim=plot_lim_y, alpha=0.3, color="#C5D86D",
                 marker=".", label="Predictions")
    rect1 = patches.Rectangle((room_lim_x[0], room_lim_y[0]), room_lim_x[1], room_lim_y[1], linewidth=1,
                              edgecolor='gray', facecolor='none', linestyle=(0, (1, 10)))
    ax.add_patch(rect1)
    device_coords = np.transpose([d1_coord, d2_coord, d3_coord, d4_coord])
    ax.plot(*device_coords, marker="^", color="#2E294E", linestyle='None', label="Uberteeth")

    ax.set_title("fil: {0}; pos: {1}".format(filter_method, positioning_method))
    ax.set_aspect("equal")

    me = 0.0

    if true_point is not None:
        ax.plot(*true_point, marker="x", color="#D7263D", label="True Point", linestyle='None')
        x_avg = filtered_res[col_x].mean()
        y_avg = filtered_res[col_y].mean()
        ax.plot(x_avg, y_avg, marker="D", color="#1B998B", label="Prediction Mean", linestyle='None')
        squared_error = filtered_res.apply(lambda row: (row[col_x] - true_point[0])**2 + (row[col_y] - true_point[1])**2, axis=1)
        mse = squared_error.mean()
        error = squared_error.apply(lambda se: math.sqrt(se))
        me = error.mean()

        dist_sq = filtered_res.apply(lambda row: (row[col_x] - x_avg)**2 + (row[col_y] - y_avg)**2, axis=1)

        print(f'50% qantile: {error.quantile(0.5)}')
        print(f'66% qantile: {error.quantile(0.66)}')
        print(f'80% qantile: {error.quantile(0.80)}')
        print(f'90% qantile: {error.quantile(0.90)}')

        print(f'true: {true_point}, extimated avg: ({x_avg},{y_avg}), error avg: {me}')

        ax.text(-0.4, -0.4, "ME: {:.4f}".format(me))

    if true_path is not None:
        path = np.transpose(true_path)
        ax.plot(*path, marker=".", color="#D7263D", label="True Path")

    lgd = plt.legend(bbox_to_anchor=(1, 1), loc='upper left', ncol=1)
    file = "{0}{1}_{2}_{3}_{4}_{5}.png".format(results_dir, true_point, true_path, filter_method, positioning_method, lap)
    print("saving: {0}".format(file))
    os.makedirs(os.path.dirname(file), exist_ok=True)
    plt.savefig(file, bbox_extra_artists=(lgd,), bbox_inches='tight', dpi=300)
    plt.close()
    # plt.show()

    return me
