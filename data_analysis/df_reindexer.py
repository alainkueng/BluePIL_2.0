import pandas

class DfReindexer:

    resampling_rate = ""
    signal_col = ""
    timestamp_col = ""

    def __init__(self, _resampling_rate, _signal_col, _timestamp_col):
        self.resampling_rate = _resampling_rate
        self.signal_col = _signal_col
        self.timestamp_col = _timestamp_col

    def get_new_idx(self, df1, df2, df3, df4):
        oidx = df1.index.union(df2.index).union(df3.index).union(df4.index)
        return pandas.date_range(oidx.min(), oidx.max(), freq=self.resampling_rate)

    def reindex_df(self, df, nidx):
        df_ri =  df[[self.signal_col]].reindex(nidx.union(df.index)).interpolate("index").reindex(nidx)
        df_ri[self.timestamp_col] = df_ri.index
        return df_ri

    def reindex_dfs(self, df1, df2, df3, df4):
        nidx = self.get_new_idx(df1, df2, df3, df4)
        df1_ri = self.reindex_df(df1, nidx)
        df2_ri = self.reindex_df(df2, nidx)
        df3_ri = self.reindex_df(df3, nidx)
        df4_ri = self.reindex_df(df4, nidx)
        return df1_ri, df2_ri, df3_ri, df4_ri
