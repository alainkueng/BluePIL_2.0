import tkinter as tk
from tkinter import ttk  # some kind of CSS
import matplotlib
import pandas as pd
from matplotlib import patches
import numpy as np
from math import sqrt
from sink.bp_kalman import BpKalman

matplotlib.use('TkAgg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
import matplotlib.animation as animation
from matplotlib import style

LARGE_FONT = ("Verdana", 12)


class GUI(tk.Tk):

    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)

        tk.Tk.iconbitmap(self, default="Bluepill.ico")
        tk.Tk.wm_title(self, "BluePIL 2.0")

        container = tk.Frame(self)
        container.pack(side="top", fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.frames = {}

        for F in (StartPage, PageOne, GraphPage):
            frame = F(container, self)
            self.frames[F] = frame
            frame.grid(row=0, column=0,
                       sticky="nsew")  # sticky: alignment + stretch to all directions (north, south...)

        self.show_frame(StartPage)

    def show_frame(self, cont):
        frame = self.frames[cont]
        frame.tkraise()  # puts page in the front


class StartPage(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        label = ttk.Label(self, text="Start Page", font=LARGE_FONT)
        label.pack(pady=10, padx=10)

        button1 = ttk.Button(self, text="Visit Page 1",
                             command=lambda: controller.show_frame(PageOne))
        button1.pack()
        button2 = ttk.Button(self, text="Visit Graph Page",
                             command=lambda: controller.show_frame(GraphPage))
        button2.pack()


class PageOne(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        label = ttk.Label(self, text="Page One", font=LARGE_FONT)
        label.pack(pady=10, padx=10)
        button1 = ttk.Button(self, text="Back to Home",
                             command=lambda: controller.show_frame(StartPage))
        button1.pack()


class GraphPage(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        label = ttk.Label(self, text="Graph Page", font=LARGE_FONT)
        label.pack(pady=10, padx=10)
        button1 = ttk.Button(self, text="Back to Home",
                             command=lambda: controller.show_frame(StartPage))
        button1.pack()

        # pos_df = read_positions()  # not kalman applied yet
        # pos_df_filtered = kalman_filter_df(pos_df)  # just kalman applied

        canvas = FigureCanvasTkAgg(fig, self)
        canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        toolbar = NavigationToolbar2Tk(canvas, self)
        toolbar.update()
        canvas._tkcanvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

exp_pos = "exp_pos"  # for Kalman

nokia_lap = "22052d"  # lap of the bluetooth device

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


def read_positions():
    df = pd.read_csv('positions.csv')
    df["timestamp"] = df["timestamp"].astype('datetime64[ns]')
    df.set_index("timestamp", inplace=True, drop=False)
    df.sort_index(inplace=True)
    return df


def plot_results_pos(df, true_point):
    fig = Figure(figsize=(5,5), dpi=100)
    ax = fig.add_subplot(111)
    df.plot(kind="scatter", legend=None, x=col_x, y=col_y, xlim=plot_lim_x, ylim=plot_lim_y, alpha=0.3,
                 color="#C5D86D",
                 marker=".", label="Predictions", ax=ax)

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
    file = f'cropped.png'

    # plt.savefig(file, bbox_inches='tight', dpi=300)
    return fig, ax
    # plt.show()


def kalman_filter_df(df):
    row1 = df.iloc()[0]
    x = row1[col_x]
    y = row1[col_y]

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


def filter_df_w_interval(df, i):
    filter = (df["timestamp"] > i[0]) & (df["timestamp"] < i[1])
    return df[filter]


# Dynamic with kalman
# Moving positions
# pos1 = (1, 1)
# pos2 = (1, 4)
# pos3 = (4, 1)


# Moving times
# i1 = (dt.datetime(2020, 7, 13, 18, 4, 30), dt.datetime(2020, 7, 13, 18, 6, 30))
# i2 = (dt.datetime(2020, 7, 13, 18, 7, 30), dt.datetime(2020, 7, 13, 18, 9, 30))
# i3 = (dt.datetime(2020, 7, 13, 18, 10, 30), dt.datetime(2020, 7, 13, 18, 12, 30))


pos_df = read_positions()  # not kalman applied yet
# pos_df_filtered = kalman_filter_df(pos_df)  # just kalman applied
# df1 = filter_df_w_interval(pos_df_filtered, i1) # ziitinterval

fig, ax = plot_results_pos(pos_df, (1, 0))

def animate(i):
    true_point = (0,1)
    df = read_positions()
    df = df.sample(n=30)
    ax.clear()
    df.plot(kind="scatter", legend=None, x=col_x, y=col_y, xlim=plot_lim_x, ylim=plot_lim_y, alpha=0.3,
            color="#C5D86D",
            marker=".", label="Predictions", ax=ax)

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

app = GUI()
ani = animation.FuncAnimation(fig, animate, interval=500)
app.mainloop()
