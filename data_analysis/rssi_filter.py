import numpy as np
from filterpy.kalman import KalmanFilter


def filter_outliers(df, signal_col, s_reference, s_std):
    outlier_filter = (df[signal_col] > s_reference - 0.5 * s_std) & (df[signal_col] < s_reference + s_std)
    return df[outlier_filter]


def filter_and_smooth_mean(df, signal_col, window_size):
    rolling = df[signal_col].rolling(window=window_size)
    s_mean = rolling.mean()
    s_std = rolling.std()
    filtered = filter_outliers(df, signal_col, s_mean, s_std)
    smoothed = filtered[signal_col].rolling(window=window_size).median().rename(signal_col)
    filtered = filtered.rename(columns={signal_col: signal_col + "_unsmoothed"})
    filtered[signal_col] = smoothed
    return filtered


def filter_and_smooth_max(df, signal_col, window_size):
    rolling = df[signal_col].rolling(window=window_size)
    s_max = rolling.max()
    # s_std = rolling.std()
    # filtered = filter_outliers(df, signal_col, s_max, s_std)
    # smoothed = filtered[signal_col].rolling(window=window_size).mean().rename(signal_col)
    # filtered = filtered.rename(columns={signal_col: signal_col + "_old"})
    # filtered[signal_col] = smoothed
    # return filtered
    smoothed = s_max.rolling(window=window_size).mean()
    filtered = df.rename(columns={signal_col: signal_col + "_old"})
    filtered[signal_col] = smoothed
    return filtered


def filter_and_smooth_max_median(df, signal_col, window_size):
    rolling = df[signal_col].rolling(window=window_size)
    s_max = rolling.max()
    s_std = rolling.std()
    filtered = filter_outliers(df, signal_col, s_max, s_std)
    smoothed = filtered[signal_col].rolling(window=window_size).median().rename(signal_col)
    filtered = filtered.rename(columns={signal_col: signal_col + "_old"})
    filtered[signal_col] = smoothed
    return filtered


def filter_and_smooth_mean_only_lower(df, signal_col, window_size):
    rolling = df[signal_col].rolling(window=window_size)
    s_mean = rolling.mean()
    s_std = rolling.std()
    filter = df[signal_col] > s_mean - 0.5 * s_std
    filtered = df[filter]
    smoothed = filtered[signal_col].rolling(window=window_size).mean().rename(signal_col)
    filtered = filtered.rename(columns={signal_col: signal_col + "_old"})
    filtered[signal_col] = smoothed
    return filtered

def filter_max(df, signal_col, window_size):
    rolling = df[signal_col].rolling(window=window_size)
    s_max = rolling.max()
    s_std = rolling.std()
    return filter_outliers(df, signal_col, s_max, s_std)


def filter_and_smooth_kalman(df, signal_col, window_size, filter_outliers=True):
    kf = KalmanFilter(dim_x=1, dim_z=1)
    kf.x = df.iloc[0][signal_col]
    kf.F = np.eye(1)
    kf.H = np.eye(1)
    kf.R = 1
    kf.Q = 0.01

    def predict_update(x):
        kf.predict()
        kf.update(np.array([x]))
        return kf.x[0, 0]

    if filter_outliers:
        df = filter_max(df, signal_col, window_size)

    filtered_sig = list(map(lambda sig: predict_update(sig), df[signal_col]))
    filtered = df.copy()
    filtered[signal_col] = filtered_sig
    return filtered