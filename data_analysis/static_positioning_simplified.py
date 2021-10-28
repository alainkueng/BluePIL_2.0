from sink.bp_quadlateration import BpQuadlateration

import pandas as pd


def position_dataset_with_methods(lap, d1, d2, d3, d4, d1_coord, d2_coord, d3_coord, d4_coord, n=2.0):


    def filter_lap(df):
        return df[df["LAP"] == lap]

    dfs = [filter_lap(d1), filter_lap(d2), filter_lap(d3), filter_lap(d4)]

    def get_avg_signal(df: pd.DataFrame):
        return df["signal"].max()

    signals = list(map(lambda x: get_avg_signal(x), dfs))

    quad = BpQuadlateration(d1_coord, d2_coord, d3_coord, d4_coord, n)

    res = quad.quadlaterate(*signals).x
    x, y, tx = res

    return x, y
