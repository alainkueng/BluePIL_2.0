def start():
    import tkinter as tk
    from tkinter import ttk  # some kind of CSS
    import matplotlib
    import json

    matplotlib.use('TkAgg')
    from matplotlib.figure import Figure
    import matplotlib.animation as animation

    LARGE_FONT = ("Verdana", 12)
    NORMAL_FONT = ("Verdana", 10)
    SMALL_FONT = ("Verdana", 8)

    fig = Figure()
    ax = fig.add_subplot(111)

    conf_file = open("bp.json", "r")
    conf = json.load(conf_file)
    conf_file.close()

    sensor_locs = []
    number_of_nodes = conf["number_of_nodes"]
    for i in range(1, number_of_nodes + 1):
        sensorconf = conf[f'node{i}']
        ip = sensorconf["ip"]
        loc = sensorconf["loc"]
        sensor_locs.append(loc)

    true_point = conf['true_point']
    n_value = conf['n_value']

    class Configuration(tk.Tk):

        def __init__(self, *args, **kwargs):
            tk.Tk.__init__(self, *args, **kwargs)

            # Title & Icon
            tk.Tk.iconbitmap(self, default="Bluepill.ico")
            tk.Tk.wm_title(self, "BluePIL 2.0 Configuration")

            # The big Container
            container = tk.Frame(self)
            container.pack(side="top", fill="both", expand=True)
            container.grid_rowconfigure(0, weight=1)
            container.grid_columnconfigure(0, weight=1)

            # The different Pages
            self.frames = {}
            for F in [ConfigurationPage]:
                frame = F(container, self)
                self.frames[F] = frame
                frame.grid(row=0, column=0,
                           sticky="nsew")  # sticky: alignment + stretch to all directions (north, south...)

            self.show_frame(ConfigurationPage)

        def show_frame(self, cont):
            frame = self.frames[cont]
            frame.tkraise()  # puts page in the front

    class ConfigurationPage(tk.Frame):
        def __init__(self, parent, controller):
            tk.Frame.__init__(self, parent)
            # Title
            label = ttk.Label(self, text="Configuration", font=LARGE_FONT)
            label.pack(pady=10, padx=10)

            # Input fields container for Graph
            self.parameters_container = tk.Frame(self, bg='grey')
            self.parameters_container.pack(side='left', padx='20', fill=tk.BOTH, pady=5, expand=True)

            # True Point
            simple_field = tk.Frame(master=self.parameters_container)
            simple_field.pack(side='top', padx='10', fill=tk.BOTH, pady="5")
            self.true_point_two = ttk.Entry(master=simple_field, width=3, font=SMALL_FONT)
            self.true_point_two.insert(0, true_point[1])
            self.true_point_two.pack(side=tk.RIGHT, padx=5, pady=4)
            self.true_point = ttk.Entry(master=simple_field, width=3, font=SMALL_FONT)
            self.true_point.insert(0, true_point[0])
            self.true_point.pack(side=tk.RIGHT, padx=5, pady=4)
            label = ttk.Label(master=simple_field, text="True Point", font=NORMAL_FONT)
            label.pack(side=tk.RIGHT, padx=4, pady=2)

            # N Value
            simple_field = tk.Frame(master=self.parameters_container)
            simple_field.pack(side='top', padx='10', fill=tk.BOTH, pady="5")
            self.n_value = ttk.Entry(master=simple_field, width=3, font=SMALL_FONT)
            self.n_value.insert(0, n_value)
            self.n_value.pack(side=tk.RIGHT, padx=5, pady=4)
            label = ttk.Label(master=simple_field, text="N-Value", font=NORMAL_FONT)
            label.pack(side=tk.RIGHT, padx=4, pady=2)

            # d1_cord
            simple_field = tk.Frame(master=self.parameters_container)
            simple_field.pack(side='top', padx='10', fill=tk.BOTH, pady="5")
            self.d1_cord_two = ttk.Entry(master=simple_field, width=3, font=SMALL_FONT)
            self.d1_cord_two.insert(0, sensor_locs[0][1])
            self.d1_cord_two.pack(side=tk.RIGHT, padx=5, pady=4)
            self.d1_cord_one = ttk.Entry(master=simple_field, width=3, font=SMALL_FONT)
            self.d1_cord_one.insert(0, sensor_locs[0][0])
            self.d1_cord_one.pack(side=tk.RIGHT, padx=5, pady=4)
            label = ttk.Label(master=simple_field, text="Ubertooth_1", font=NORMAL_FONT)
            label.pack(side=tk.RIGHT, padx=4, pady=2)

            # d2_cord
            simple_field = tk.Frame(master=self.parameters_container)
            simple_field.pack(side='top', padx='10', fill=tk.BOTH, pady="5")
            self.d2_cord_two = ttk.Entry(master=simple_field, width=3, font=SMALL_FONT)
            self.d2_cord_two.insert(0, sensor_locs[1][1])
            self.d2_cord_two.pack(side=tk.RIGHT, padx=5, pady=4)
            self.d2_cord_one = ttk.Entry(master=simple_field, width=3, font=SMALL_FONT)
            self.d2_cord_one.insert(0, sensor_locs[1][0])
            self.d2_cord_one.pack(side=tk.RIGHT, padx=5, pady=4)
            label = ttk.Label(master=simple_field, text="Ubertooth_2", font=NORMAL_FONT)
            label.pack(side=tk.RIGHT, padx=4, pady=2)

            # d3_cord
            simple_field = tk.Frame(master=self.parameters_container)
            simple_field.pack(side='top', padx='10', fill=tk.BOTH, pady="5")
            self.d3_cord_two = ttk.Entry(master=simple_field, width=3, font=SMALL_FONT)
            self.d3_cord_two.insert(0, sensor_locs[2][1])
            self.d3_cord_two.pack(side=tk.RIGHT, padx=5, pady=4)
            self.d3_cord_one = ttk.Entry(master=simple_field, width=3, font=SMALL_FONT)
            self.d3_cord_one.insert(0, sensor_locs[2][0])
            self.d3_cord_one.pack(side=tk.RIGHT, padx=5, pady=4)
            label = ttk.Label(master=simple_field, text="Ubertooth_3", font=NORMAL_FONT)
            label.pack(side=tk.RIGHT, padx=4, pady=2)

            # d4_cord
            simple_field = tk.Frame(master=self.parameters_container)
            simple_field.pack(side='top', padx='10', fill=tk.BOTH, pady="5")
            self.d4_cord_two = ttk.Entry(master=simple_field, width=3, font=SMALL_FONT)
            self.d4_cord_two.insert(0, sensor_locs[3][1])
            self.d4_cord_two.pack(side=tk.RIGHT, padx=5, pady=4)
            self.d4_cord_one = ttk.Entry(master=simple_field, width=3, font=SMALL_FONT)
            self.d4_cord_one.insert(0, sensor_locs[3][0])
            self.d4_cord_one.pack(side=tk.RIGHT, padx=5, pady=4)
            label = ttk.Label(master=simple_field, text="Ubertooth_4", font=NORMAL_FONT)
            label.pack(side=tk.RIGHT, padx=4, pady=2)

            button = ttk.Button(text="Save & Quit", master=self.parameters_container, command=self.update_json)
            button.pack(side=tk.RIGHT, padx=5, pady=4)

        def animate(self, i):
            self.update()

        def update_json(self):
            conf_file = open("bp.json", "r")
            conf = json.load(conf_file)
            conf_file.close()

            conf['node1']['loc'] = [float(self.d1_cord_one.get()), float(self.d1_cord_two.get())]
            conf['node2']['loc'] = [float(self.d2_cord_one.get()), float(self.d2_cord_two.get())]
            conf['node3']['loc'] = [float(self.d3_cord_one.get()), float(self.d3_cord_two.get())]
            conf['node4']['loc'] = [float(self.d4_cord_one.get()), float(self.d4_cord_two.get())]
            conf['true_point'] = [float(self.true_point.get()), float(self.true_point_two.get())]
            conf['n_value'] = float(self.n_value.get())

            conf_file = open("bp.json", "w")
            json.dump(conf, conf_file, indent=4)
            conf_file.close()
            app.destroy()

    app = Configuration()
    app.geometry("320x320")
    ani = animation.FuncAnimation(fig, app.frames[ConfigurationPage].animate, interval=500)
    app.mainloop()
