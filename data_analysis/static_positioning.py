from data_analysis.df_merger import DfMerger
from data_analysis.df_reindexer import DfReindexer
from sink.bp_kalman import BpKalman
from sink.bp_quadlateration import BpQuadlateration
from data_analysis.rssi_filter import filter_and_smooth_max, filter_and_smooth_kalman, filter_and_smooth_max_median, \
    filter_and_smooth_mean, filter_max

import numpy as np


def position_dataset_with_methods(lap, filter_method, positioning_method, initial_val,
                                  d1, d2, d3, d4, d1_coord, d2_coord, d3_coord, d4_coord,
                                  n=2.0, resampling_rate="1s", resampling_rate_in_seconds=1):

    col_x = "x"
    col_y = "y"

    col_s1 = "signal1"
    col_s2 = "signal2"
    col_s3 = "signal3"
    col_s4 = "signal4"

    window_size = "5s"

    def filter_dfs_max(dframe):
        return list(map(lambda df: filter_max(df, "signal", window_size), dframe))

    def filter_dfs_mean(dframe):
        return list(map(lambda df: filter_and_smooth_mean(df, "signal", window_size), dframe))

    def filter_dfs_max_mean(dframe):
        return list(map(lambda df: filter_and_smooth_max(df, "signal", window_size), dframe))

    def filter_dfs_max_median(dframe):
        return list(map(lambda df: filter_and_smooth_max_median(df, "signal", window_size), dframe))

    def filter_dfs_kalman(dframe):
        return list(map(lambda df: filter_and_smooth_kalman(df, "signal", window_size, filter_outliers=False), dframe))

    def filter_dfs_kalman_max(dfs):
        return list(map(lambda df: filter_and_smooth_kalman(df, "signal", window_size), dfs))

    def filter_lap(df):
        return df[df["LAP"] == lap]

    dfs = [filter_lap(d1), filter_lap(d2), filter_lap(d3), filter_lap(d4)]

    if filter_method == "mean":
        filter_func = filter_dfs_mean
    elif filter_method == "max":
        filter_func = filter_dfs_max
    elif filter_method == "max-mean":
        filter_func = filter_dfs_max_mean
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
        kal_lstsq = BpKalman(np.array([initial_val[0], 0, initial_val[1], 0]))

        def kalman_lstsq_predict(row):
            x, y, _ = quad.quadlaterate(row[col_s1], row[col_s2], row[col_s3], row[col_s4]).x
            row[col_x], _, row[col_y], _ = kal_lstsq.predict_update(x, y, resampling_rate_in_seconds)
            return row
        positioning_func = kalman_lstsq_predict
    else:
        raise NotImplementedError()

    filtered_res = filtered_mrgd.apply(positioning_func, axis=1)

    del filtered_mrgd

    return filtered_res
