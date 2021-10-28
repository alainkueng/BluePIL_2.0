import pandas as pd

class DfMerger:
    signal_col = ""
    timestamp_col = ""

    def __init__(self, _signal_col, _timestamp_col):
        self.signal_col = _signal_col
        self.timestamp_col = _timestamp_col

    def merge_dfs(self, dfs):
        signal_series = []
        for i in range (0, len(dfs)):
            signal_series.append(dfs[i][self.signal_col].rename(self.signal_col + str(i + 1)))
        mrgd = pd.concat(signal_series, axis=1)
        mrgd[self.timestamp_col] = mrgd.index
        return mrgd