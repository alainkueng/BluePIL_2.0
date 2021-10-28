import matplotlib.pyplot as plt

def plot_rssi_2(df1, df2, title, **kwargs):
    ax = df1.plot(kind='line', x='timestamp', y='signal', style='.-', **kwargs)
    df2.plot(kind='line', x='timestamp', y='signal', ax = ax, color = 'blue', style='.-', **kwargs)
    plt.title(title)
    plt.interactive(False)
    plt.show()
    plt.clf()


def plot_rssi(df, title, **kwargs):
    plot_xy(df, 'timestamp', 'signal', **kwargs)
    plt.title(title)
    plt.interactive(False)
    plt.show()
    plt.clf()


def plot_xy(df, x_col, y_col, **kwargs):
    return df.plot(kind='line', x=x_col, y=y_col, style='.-', **kwargs)

def plot_dist(df, title, **kwargs):
    ax = plot_xy(df, 'timestamp', 'signal', **kwargs)
    ax.axhline(y=2.5, color='red')
    plt.title(title)
    plt.interactive(False)
    plt.show()
    plt.clf()