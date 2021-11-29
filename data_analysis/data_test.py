import os
import datetime as dt
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import patches
import numpy as np
from math import sqrt

import data_analysis.static_positioning as sp
import data_analysis.static_positioning_simplified as sps
from sink.bp_kalman import BpKalman

data_dir = ""  # wo sind Daten gespeichert

ip1 = "192.168.8.101"
ip2 = "192.168.8.102"
ip3 = "192.168.8.103"
ip4 = "192.168.8.104"

# Experimentname + Truepoint
exp_0_1 = ("exp_0_1", (0, 1))
exp_0_2 = ("exp_0_2", (0, 2))
exp_0_3 = ("exp_0_3", (0, 3))
exp_0_4 = ("exp_0_4", (0, 4))
exp_1_0 = ("exp_1_0", (1, 0))
exp_1_1 = ("exp_1_1", (1, 1))
exp_1_2 = ("exp_1_2", (1, 2))
exp_1_3 = ("exp_1_3", (1, 3))
exp_1_4 = ("exp_1_4", (1, 4))
exp_1_5 = ("exp_1_5", (1, 5))
exp_2_0 = ("exp_2_0", (2, 0))
exp_2_1 = ("exp_2_1", (2, 1))
exp_2_2 = ("exp_2_2", (2, 2))
exp_2_3 = ("exp_2_3", (2, 3))
exp_2_4 = ("exp_2_4", (2, 4))
exp_2_5 = ("exp_2_5", (2, 5))
exp_3_0 = ("exp_3_0", (3, 0))
exp_3_1 = ("exp_3_1", (3, 1))
exp_3_2 = ("exp_3_2", (3, 2))
exp_3_3 = ("exp_3_3", (3, 3))
exp_3_4 = ("exp_3_4", (3, 4))
exp_3_5 = ("exp_3_5", (3, 5))
exp_4_0 = ("exp_4_0", (4, 0))
exp_4_1 = ("exp_4_1", (4, 1))
exp_4_2 = ("exp_4_2", (4, 2))
exp_4_3 = ("exp_4_3", (4, 3))
exp_4_4 = ("exp_4_4", (4, 4))
exp_4_5 = ("exp_4_5", (4, 5))
exp_5_1 = ("exp_5_1", (5, 1))
exp_5_2 = ("exp_5_2", (5, 2))
exp_5_3 = ("exp_5_3", (5, 3))
exp_5_4 = ("exp_5_4", (5, 4))
experiments = [exp_0_1, exp_0_2, exp_0_3, exp_0_4,
               exp_1_0, exp_1_1, exp_1_2, exp_1_3, exp_1_4, exp_1_5,
               exp_2_0, exp_2_1, exp_2_2, exp_2_3, exp_2_4, exp_2_5,
               exp_3_0, exp_3_1, exp_3_2, exp_3_3, exp_3_4, exp_3_5,
               exp_4_0, exp_4_1, exp_4_2, exp_4_3, exp_4_4, exp_4_5,
               exp_5_1, exp_5_2, exp_5_3, exp_5_4]


exp_pos = "exp_pos" # for Kalman

nokia_lap = "22052d"  #lap of the bluetooth device

# coordinates of the corners
d1_coord = (0, 0)
d2_coord = (5, 0)
d3_coord = (0, 5)
d4_coord = (5, 5)

coords = (d1_coord, d2_coord, d3_coord, d4_coord)

col_x = "x"
col_y = "y"

room_lim_x = (0, 5)
room_lim_y = (0, 5)

plot_padding = 0.5

plot_lim_x = (room_lim_x[0] - plot_padding, room_lim_x[1] + plot_padding)
plot_lim_y = (room_lim_y[0] - plot_padding, room_lim_y[1] + plot_padding)

# read csv with IP_name ub dur /exp_1/ip.csv (experminent point 1.  minutes)
def read_dfs(exp_dir):
    dir = f'{data_dir}/{exp_dir}'

    def read_and_index(ip):
        df = pd.read_csv(f'{dir}/{ip}.csv')
        df["timestamp"] = df["timestamp"].astype('datetime64[ns]')
        df.set_index("timestamp", inplace=True, drop=False)
        return df

    df1 = read_and_index(ip1)
    df2 = read_and_index(ip2)
    df3 = read_and_index(ip3)
    df4 = read_and_index(ip4)
    return df1, df2, df3, df4


def plot_results(df, true_point, filter_method, positioning_method, exp_dir):
    results_subdir = f'{data_dir}/results'
    ax = df.plot(kind="scatter", x=col_x, y=col_y, xlim=plot_lim_x, ylim=plot_lim_y, alpha=0.3, color="#C5D86D",
                 marker=".", label="Predictions")
    rect1 = patches.Rectangle((room_lim_x[0], room_lim_y[0]), room_lim_x[1], room_lim_y[1], linewidth=1,
                              edgecolor='gray', facecolor='none', linestyle=(0, (1, 10)))
    ax.add_patch(rect1)
    device_coords = np.transpose([d1_coord, d2_coord, d3_coord, d4_coord])
    ax.plot(*device_coords, marker="^", color="#2E294E", linestyle='None', label="Uberteeth")
    ax.set_title("fil: {0}; pos: {1}".format(filter_method, positioning_method))
    ax.set_aspect("equal")
    ax.plot(*true_point, marker="x", color="#D7263D", label="True Point", linestyle='None')
    x_avg = df[col_x].mean()
    y_avg = df[col_y].mean()
    ax.plot(x_avg, y_avg, marker="D", color="#1B998B", label="Prediction Mean", linestyle='None')
    squared_error = df.apply(lambda row: (row[col_x] - true_point[0]) ** 2 + (row[col_y] - true_point[1]) ** 2, axis=1)
    error = squared_error.apply(lambda se: sqrt(se))
    me = error.mean()
    ax.text(-0.4, -0.4, "ME: {:.4f}".format(me))
    lgd = plt.legend(bbox_to_anchor=(1, 1), loc='upper left', ncol=1)
    file = f'{results_subdir}/{exp_dir}.png'
    os.makedirs(os.path.dirname(file), exist_ok=True)
    plt.savefig(file, bbox_extra_artists=(lgd,), bbox_inches='tight', dpi=300)
    plt.show()


def read_position_plot(exp_dir, true_point):
    filter_method = "max-mean"
    positioning_method = "nlls"
    dfs = read_dfs(exp_dir)
    res = sp.position_dataset_with_methods(nokia_lap, filter_method, positioning_method, (2.5, 2.5), *dfs, *coords)
    plot_results(res, true_point, filter_method, positioning_method, exp_dir)


for exp in experiments:
    try:
        read_position_plot(*exp)
    except:
        pass


# Dynamic with kalman
# Moving positions
pos1 = (1, 1)
pos2 = (1, 4)
pos3 = (4, 1)
pos4 = (4, 4)
pos5 = (2.5, 2.5)

# Moving times
i1 = (dt.datetime(2020, 7, 13, 18, 4, 30), dt.datetime(2020, 7, 13, 18, 6, 30))
i2 = (dt.datetime(2020, 7, 13, 18, 7, 30), dt.datetime(2020, 7, 13, 18, 9, 30))
i3 = (dt.datetime(2020, 7, 13, 18, 10, 30), dt.datetime(2020, 7, 13, 18, 12, 30))
i4 = (dt.datetime(2020, 7, 13, 18, 13, 30), dt.datetime(2020, 7, 13, 18, 15, 30))
i5 = (dt.datetime(2020, 7, 13, 18, 16, 30), dt.datetime(2020, 7, 13, 18, 18, 30))


def read_position_df():
    df = pd.read_csv(f'{data_dir}/{exp_pos}/positions.csv')
    df["timestamp"] = df["timestamp"].astype('datetime64[ns]')
    df.set_index("timestamp", inplace=True, drop=False)
    df.sort_index(inplace=True)
    return df


def filter_df_w_interval(df, i):
    filter = (df["timestamp"] > i[0]) & (df["timestamp"] < i[1])
    return df[filter]


def kalman_filter_df(df):
    row1 = df.iloc()[0]
    x = row1[col_x]
    y = row1[col_y]
    print((x, 0, y, 0))
    kalman_filter = BpKalman(np.array([x, 0, y, 0]))

    df["t-1"] = df["timestamp"].shift(1)
    df["dt"] = (df["timestamp"] - df["t-1"]).apply(lambda x: x.total_seconds())

    df_from_1 = df[1:]

    def filter(row):
        res = kalman_filter.predict_update(row[col_x], row[col_y], row["dt"])
        row[col_x] = res[0]
        row[col_y] = res[2]
        return row

    return df_from_1.apply(filter, axis=1)


def plot_results_pos(df, true_point, exp_dir):
    results_subdir = f'{data_dir}/results'
    ax = df.plot(kind="scatter", legend=None, x=col_x, y=col_y, xlim=plot_lim_x, ylim=plot_lim_y, alpha=0.3,
                 color="#C5D86D",
                 marker=".", label="Predictions")
    rect1 = patches.Rectangle((room_lim_x[0], room_lim_y[0]), room_lim_x[1], room_lim_y[1], linewidth=1,
                              edgecolor='gray', facecolor='none', linestyle=(0, (1, 10)))
    ax.add_patch(rect1)
    device_coords = np.transpose([d1_coord, d2_coord, d3_coord, d4_coord])
    ax.plot(*device_coords, marker="^", color="#2E294E", linestyle='None', label="Uberteeth")

    ax.set_aspect("equal")

    ax.plot(*true_point, marker="x", color="#D7263D", label="True Point", linestyle='None')
    x_avg = df[col_x].mean()
    y_avg = df[col_y].mean()
    ax.plot(x_avg, y_avg, marker="D", color="#1B998B", label="Prediction Mean", linestyle='None')
    squared_error = df.apply(lambda row: (row[col_x] - true_point[0]) ** 2 + (row[col_y] - true_point[1]) ** 2, axis=1)
    error = squared_error.apply(lambda se: sqrt(se))
    me = error.mean()
    ax.text(-0.4, -0.4, "ME: {:.4f}".format(me))
    # lgd = plt.legend(bbox_to_anchor=(1, 1), loc='upper left', ncol=1)
    # file = f'{results_subdir}/{exp_dir}.png'
    file = f'{results_subdir}/{exp_dir}_cropped.png'
    os.makedirs(os.path.dirname(file), exist_ok=True)
    # plt.savefig(file, bbox_extra_artists=(lgd,), bbox_inches='tight', dpi=300)
    plt.savefig(file, bbox_inches='tight', dpi=300)
    # plt.close()
    plt.show()


pos_df = read_position_df()
pos_df_filtered = kalman_filter_df(pos_df)

df1 = filter_df_w_interval(pos_df_filtered, i1)
df2 = filter_df_w_interval(pos_df_filtered, i2)
df3 = filter_df_w_interval(pos_df_filtered, i3)
df4 = filter_df_w_interval(pos_df_filtered, i4)
df5 = filter_df_w_interval(pos_df_filtered, i5)

plot_results_pos(df1, pos1, "exp_pos_1")
plot_results_pos(df2, pos2, "exp_pos_2")
plot_results_pos(df3, pos3, "exp_pos_3")
plot_results_pos(df4, pos4, "exp_pos_4")
plot_results_pos(df5, pos5, "exp_pos_5")

pos_df_filtered = kalman_filter_df(pos_df)
