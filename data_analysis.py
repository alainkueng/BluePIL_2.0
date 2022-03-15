import tkinter as tk
from tkinter import ttk  # some kind of CSS
import matplotlib
import pandas as pd
from matplotlib import patches
import numpy as np
from math import sqrt
from sink.bp_kalman import BpKalman
import json

matplotlib.use('TkAgg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import matplotlib.animation as animation

# FONT Style
LARGE_FONT = ("Verdana", 12)
NORMAL_FONT = ("Verdana", 10)
SMALL_FONT = ("Verdana", 8)


# read the csv file
def read_positions():
    df = pd.read_csv('positions.csv')
    df["timestamp"] = df["timestamp"].astype('datetime64[ns]')
    return df


# pop up if no data is available
def error():
    popup = tk.Tk()
    popup.wm_title("!")
    label = ttk.Label(popup, text='No Data in CSV yet', font=NORMAL_FONT)
    label.pack(side="top", fill="x", pady=10)
    B1 = ttk.Button(popup, text="Okay", command=popup.destroy)
    B1.pack()
    popup.mainloop()
    exit()


# check if position exists
try:
    df = pd.read_csv('positions.csv')
except Exception:
    error()
# read the positions.csv file
df = pd.read_csv('positions.csv')
# if the skeleton is there but no data
if df.empty:
    error()

# plot initialization that gets used later
fig = Figure()
ax = fig.add_subplot()

# reads the current configuration of BluePIL
with open("bp.json") as f:
    conf = json.load(f)
number_of_nodes = conf["number_of_nodes"]

# coordinates of the Uberteeth
coordinates = []
room_length = 0
for i in range(1, number_of_nodes + 1):
    sensor = conf[f'node{i}']
    coordinates.append((sensor["loc"][0], sensor["loc"][1]))
    room_length = sensor["loc"][0] if sensor["loc"][0] > room_length else room_length
    room_length = sensor["loc"][1] if sensor["loc"][1] > room_length else room_length
# n coefficient
n_value = conf['n_value']

d1_coord = coordinates[0]
d2_coord = coordinates[1]
d3_coord = coordinates[2]
d4_coord = coordinates[3]

true_point = (conf['true_point'][0], conf['true_point'][1])
coords = (d1_coord, d2_coord, d3_coord, d4_coord)

col_x = "x"
col_y = "y"

# room length
room_lim_x = (0, room_length)
room_lim_y = (0, room_length)

# plot padding
plot_padding = 0.5
plot_lim_x = (room_lim_x[0] - plot_padding, room_lim_x[1] + plot_padding)
plot_lim_y = (room_lim_y[0] - plot_padding, room_lim_y[1] + plot_padding)

kalman = False
plot_all = False

pos_df = read_positions()  # not kalman applied yet

# unique laps of the positions file
unique_laps = pos_df['LAP'].unique()
is_LAP = pos_df['LAP'] == unique_laps[0]
sensed_laps = sum(1 for line in open('laps.csv'))

# takes the last 20 points
pos_df = pos_df.tail(20)


# if something goes wrong this is the pop up message
def popupmsg(msg):
    popup = tk.Tk()
    popup.wm_title("!")
    label = ttk.Label(popup, text=msg, font=NORMAL_FONT)
    label.pack(side="top", fill="x", pady=10)
    B1 = ttk.Button(popup, text="Okay", command=popup.destroy)
    B1.pack()
    popup.mainloop()


class GUI(tk.Tk):

    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)

        # Title & Icon
        tk.Tk.iconbitmap(self, default="Bluepill.ico")
        tk.Tk.wm_title(self, "BluePIL 2.0")

        # The big Container
        container = tk.Frame(self)
        container.pack(side="top", fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        # Menubar
        menubar = tk.Menu(container)
        filemenu = tk.Menu(menubar, tearoff=0)
        filemenu.add_command(label="Exit", command=quit)
        menubar.add_cascade(label="Menu", menu=filemenu)
        tk.Tk.config(self, menu=menubar)

        # The different Pages
        self.frames = {}
        for F in [GraphPage]:
            frame = F(container, self)
            self.frames[F] = frame
            frame.grid(row=0, column=0,
                       sticky="nsew")  # sticky: alignment + stretch to all directions (north, south...)

        self.show_frame(GraphPage)

    def show_frame(self, cont):
        frame = self.frames[cont]
        frame.tkraise()  # puts page in the front


class GraphPage(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        # Title
        label = ttk.Label(self, text="Graph Page", font=LARGE_FONT)
        label.pack(pady=10, padx=10)

        # Input fields container for Graph
        self.parameters_container = tk.Frame(self, bg='grey')
        self.parameters_container.pack(side='left', padx='20', fill=tk.BOTH, pady=5)

        # Range field
        simple_field = tk.Frame(master=self.parameters_container)
        simple_field.pack(side='top', padx='10', fill=tk.BOTH, pady="5")
        self.range = ttk.Entry(master=simple_field, width=3, font=SMALL_FONT)
        self.range.insert(0, '20')
        self.range.pack(side=tk.RIGHT, padx=5, pady=4)
        label = ttk.Label(master=simple_field, text="Last points", font=NORMAL_FONT)
        label.pack(side=tk.RIGHT, padx=4, pady=2)

        # N-Value field
        simple_field = tk.Frame(master=self.parameters_container)
        simple_field.pack(side='top', padx='10', fill=tk.BOTH, pady="5")
        self.n_value = ttk.Entry(master=simple_field, width=3, font=SMALL_FONT)
        self.n_value.insert(0, n_value)
        self.n_value.pack(side=tk.RIGHT, padx=5, pady=4)
        label = ttk.Label(master=simple_field, text="n value", font=NORMAL_FONT)
        label.pack(side=tk.RIGHT, padx=4, pady=2)

        # Kalman applied
        simple_field = tk.Frame(master=self.parameters_container)
        simple_field.pack(side='top', padx='10', fill=tk.BOTH, pady="5")
        self.var = tk.BooleanVar()
        self.var.set(kalman)
        self.kalman = tk.Checkbutton(master=simple_field, var=self.var)
        self.kalman.pack(side=tk.RIGHT, padx=5, pady=4)
        label = ttk.Label(master=simple_field, text="Apply Kalman", font=NORMAL_FONT)
        label.pack(side=tk.RIGHT, padx=4, pady=2)

        # Plot all applied
        simple_field = tk.Frame(master=self.parameters_container)
        simple_field.pack(side='top', padx='10', fill=tk.BOTH, pady="5")
        self.plot_all = tk.BooleanVar()
        self.plot_all.set(plot_all)
        self.plot_all_box = tk.Checkbutton(master=simple_field, var=self.plot_all)
        self.plot_all_box.pack(side=tk.RIGHT, padx=5, pady=4)
        label = ttk.Label(master=simple_field, text="Plot all laps", font=NORMAL_FONT)
        label.pack(side=tk.RIGHT, padx=4, pady=2)

        # True Point
        simple_field = tk.Frame(master=self.parameters_container)
        simple_field.pack(side='top', padx='10', fill=tk.BOTH, pady="5")
        self.true_point_two = ttk.Entry(master=simple_field, width=3, font=SMALL_FONT)
        self.true_point_two.insert(0, true_point[1])
        self.true_point_two.pack(side=tk.RIGHT, padx=5, pady=4)
        self.true_point_one = ttk.Entry(master=simple_field, width=3, font=SMALL_FONT)
        self.true_point_one.insert(0, true_point[0])
        self.true_point_one.pack(side=tk.RIGHT, padx=5, pady=4)
        label = ttk.Label(master=simple_field, text="True Point", font=NORMAL_FONT)
        label.pack(side=tk.RIGHT, padx=4, pady=2)

        # LAPS
        self.simple_field = tk.Frame(master=self.parameters_container)
        self.simple_field.pack(side='top', padx='10', fill=tk.BOTH, pady="5")
        self.unique_laps = unique_laps
        self.option = tk.StringVar(self)
        self.option.set(unique_laps[0])
        self.optionBox = tk.OptionMenu(self.simple_field, self.option, *self.unique_laps)
        self.optionBox.pack(side=tk.RIGHT, padx=4, pady=2)
        self.option_label = ttk.Label(master=self.simple_field, text="Devices", font=NORMAL_FONT)
        self.option_label.pack(side=tk.RIGHT, padx=4, pady=2)

        # Nr. of devices
        self.count_field = tk.Frame(master=self.parameters_container)
        self.count_field.pack(side='top', padx='10', fill=tk.BOTH, pady="5")
        self.laps_count = ttk.Label(master=self.count_field, text='Positioned Devices: ' + str(len(self.unique_laps)),
                                    font=NORMAL_FONT)
        self.laps_count.pack(side=tk.RIGHT, padx=4, pady=2)

        # Nr. of devices
        self.sensed_field = tk.Frame(master=self.parameters_container)
        self.sensed_field.pack(side='top', padx='10', fill=tk.BOTH, pady="5")
        self.laps_sensed = ttk.Label(master=self.sensed_field,
                                     text='Sensed Devices: ' + str(sum(1 for line in open('laps.csv'))),
                                     font=NORMAL_FONT)
        self.laps_sensed.pack(side=tk.RIGHT, padx=4, pady=2)

        # Devices Laps sensed
        lines = []
        for line in open('laps.csv'):
            lines.append(line)
        self.scroll_bar = tk.Scrollbar(master=self.parameters_container)
        self.scroll_bar.pack(side='right', padx='10', fill=tk.Y, pady="5")
        self.laps_list = tk.Listbox(master=self.parameters_container, yscrollcommand=self.scroll_bar.set,
                                    font=NORMAL_FONT, width='25')
        for line in lines:
            self.laps_list.insert(tk.END, line)
        self.laps_list.pack(side=tk.LEFT, fill=tk.BOTH, padx='10', pady="5")
        self.scroll_bar.config(command=self.laps_list.yview)

        # plot figure
        canvas = FigureCanvasTkAgg(fig, self)
        canvas.get_tk_widget().pack(side=tk.LEFT, fill=tk.BOTH, expand=tk.TRUE)

        # somethings wrong label
        self.label = ttk.Label(self, text="Somethings wrong", font=LARGE_FONT)

    # this is the function that runs a set interval
    def animate(self, i):
        global coords, true_point, room_lim_x, room_lim_y, plot_lim_x, plot_lim_y, plot_padding, kalman, n_value, sensed_laps
        df = read_positions()
        laps = list(self.unique_laps)
        self.unique_laps = list(df['LAP'].unique())

        # if true, there are new laps, i.e the option box has to update
        if laps != self.unique_laps:
            # option box reset
            self.optionBox.destroy()
            self.option_label.destroy()
            self.optionBox = tk.OptionMenu(self.simple_field, self.option, *self.unique_laps)
            self.optionBox.pack(side=tk.RIGHT, padx=4, pady=2)
            self.option_label = ttk.Label(master=self.simple_field, text="Devices", font=NORMAL_FONT)
            self.option_label.pack(side=tk.RIGHT, padx=4, pady=2)
            # lap counter reset
            self.laps_count.destroy()
            self.laps_count = ttk.Label(master=self.count_field,
                                        text='Positioned Devices: ' + str(len(self.unique_laps)), font=NORMAL_FONT)
            self.laps_count.pack(side=tk.RIGHT, padx=4, pady=2)
            # if the lap does not exist anymore (only for debugging purposes)
            if self.option.get() not in self.unique_laps:
                self.option.set(self.unique_laps[0])

        # reset if the amount of sensed laps changed
        if sensed_laps < sum(1 for line in open('laps.csv')):
            # reset the number
            self.laps_sensed.destroy()
            self.laps_sensed = ttk.Label(master=self.sensed_field,
                                         text='Sensed Devices: ' + str(sum(1 for line in open('laps.csv'))),
                                         font=NORMAL_FONT)
            self.laps_sensed.pack(side=tk.RIGHT, padx=4, pady=2)
            # reset the list with the names
            self.laps_list.destroy()
            lines = []
            for line in open('laps.csv'):
                lines.append(line)
            self.laps_list = tk.Listbox(master=self.parameters_container, yscrollcommand=self.scroll_bar.set,
                                        font=NORMAL_FONT, width='25')
            for line in lines:
                self.laps_list.insert(tk.END, line)
            self.laps_list.pack(side=tk.LEFT, fill=tk.BOTH, padx='10', pady="5")
            self.scroll_bar.config(command=self.laps_list.yview)
            sensed_laps = sum(1 for line in open('laps.csv'))

        # For color per lap
        lap_dic = {}
        lap_colors = ['#e6194b', '#3cb44b', '#ffe119', '#4363d8', '#f58231', '#911eb4', '#46f0f0', '#f032e6', '#bcf60c',
                      '#fabebe', '#008080', '#e6beff', '#9a6324', '#fffac8', '#800000', '#aaffc3', '#808000', '#ffd8b1',
                      '#000075', '#808080', '#ffffff', '#000000']
        # sorts the lap positions into dedicated dfs that get stored into a dictionary, also applies kalman if chosen
        for lap in self.unique_laps:
            is_LAP = df['LAP'] == lap
            lap_dic[lap] = kalman_filter_df(df[is_LAP]) if kalman else df[is_LAP]

        # chosen lap of all laps gets stored into df
        is_LAP = df['LAP'] == self.option.get()
        df = df[is_LAP]

        # applies kalman filter to df
        if kalman:
            df = kalman_filter_df(df)

        # chosen range to be displayed, if not valid input, an error is shown
        try:
            df = df.tail(int(self.range.get()) if int(self.range.get()) != 0 else 1)
            show_error = False if int(self.range.get()) > 0 else True
        except ValueError:
            df = df.tail(n=1)
            show_error = True

        ax.clear()

        # if all device should be plotted
        if self.plot_all.get():
            for key in lap_dic:
                # chooses a color of the list, yes it is limited to the amount of colors (22) in the list right now
                color = lap_colors[0]
                lap_colors.remove(color)

                try:
                    lap_dic[key] = lap_dic[key].tail(int(self.range.get()) if int(self.range.get()) != 0 else 1)
                    show_error = False if int(self.range.get()) > 0 else True
                except ValueError:
                    lap_dic[key] = lap_dic[key].tail(n=1)
                    show_error = True

                x_avg = lap_dic[key][col_x].mean()
                y_avg = lap_dic[key][col_y].mean()
                lap_dic[key].plot(kind="scatter", x=col_x, y=col_y, xlim=plot_lim_x, ylim=plot_lim_y, alpha=1,
                                  color=color,
                                  marker=".", label=key + " Predictions", ax=ax, grid=True)
                ax.plot(x_avg, y_avg, marker="D", color='black', label=key + " Prediction Mean", linestyle='None',
                        markerfacecolor=color)
        else:
            # plot the chosen device
            df.plot(kind="scatter", legend=None, x=col_x, y=col_y, xlim=plot_lim_x, ylim=plot_lim_y, alpha=0.3,
                    color="#e6194b", grid=True,
                    marker=".", label="Predictions", ax=ax)

        # if error should be displayed, it gets displayed else not
        self.label.pack() if show_error else self.label.pack_forget()

        # add ons
        rect1 = patches.Rectangle((room_lim_x[0], room_lim_y[0]), room_lim_x[1], room_lim_y[1], linewidth=1,
                                  edgecolor='gray', facecolor='none', linestyle=(0, (1, 10)))
        ax.add_patch(rect1)
        device_coords = np.transpose([d1_coord, d2_coord, d3_coord, d4_coord])
        ax.plot(*device_coords, marker="^", color="#2E294E", linestyle='None', label="Uberteeth")

        ax.set_aspect("equal")
        ax.plot(*true_point, marker="x", color="#D7263D", label="True Point", linestyle='None')

        # calculates the difference to the true_point and plots the prediction mean
        if not self.plot_all.get():
            x_avg = df[col_x].mean()
            y_avg = df[col_y].mean()
            ax.plot(x_avg, y_avg, marker="D", color='black', label="Prediction Mean", linestyle='None',
                    markerfacecolor="#e6194b")

            squared_error = df.apply(lambda row: (row[col_x] - true_point[0]) ** 2 + (row[col_y] - true_point[1]) ** 2,
                                     axis=1)
            error = squared_error.apply(lambda se: sqrt(se))
            me = error.mean()
            try:
                ax.text(-0.4, -0.4, "ME: {:.4f}".format(me))
            except:
                pass
        ax.legend(bbox_to_anchor=(1, 1))

        # tries to store the n value of the input field, if it fails: set to default 1.8
        try:
            n_value = float(self.n_value.get())
        except ValueError:
            n_value = 1.8
        # tries to store the true point values of the input field, if it fails: set to default true point 0, 0
        try:
            true_point = float(self.true_point_one.get()), float(self.true_point_two.get())
        except ValueError:
            true_point = 0, 0

        # updates the kalman boolean
        kalman = self.var.get()

        # tries to store the na value into the json fail, if it fails gets skipped
        try:
            conf_file = open("bp.json", "r")
            conf = json.load(conf_file)
            conf_file.close()

            conf['n_value'] = float(self.n_value.get())

            conf_file = open("bp.json", "w")
            json.dump(conf, conf_file, indent=4)
            conf_file.close()
        except Exception:
            pass

        self.update()


# plots the result for the first time
def plot_results_pos(df, true_point):
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
    ax.legend(bbox_to_anchor=(1, 1))
    return fig, ax

# kalman filter
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


if kalman:
    pos_df = kalman_filter_df(pos_df)  # just kalman applied

fig, ax = plot_results_pos(pos_df, true_point)

# creates app and size
app = GUI()
app.geometry("1350x720")
# interval set for polling
ani = animation.FuncAnimation(fig, app.frames[GraphPage].animate, interval=100)
app.mainloop()
