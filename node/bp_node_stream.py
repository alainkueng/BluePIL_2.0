import statistics
from datetime import timedelta

import streamz as sz
from filterpy.kalman import KalmanFilter
import numpy as np

from node.bp_ubertooth import Ubertooth


@sz.Stream.register_api()
class sliding_time_window(sz.Stream):

    _graphviz_shape = 'diamond'

    def __init__(self, upstream, timedelta_seconds, timestamp_field, **kwargs):
        self.timedelta = timedelta(seconds=timedelta_seconds)
        self._buffer = []
        self._metadata_buffer = []
        self.timestamp_field = timestamp_field
        sz.Stream.__init__(self, upstream, **kwargs)

    def update(self, x, who=None, metadata=None):
        self._retain_refs(metadata)
        new_buffer = []
        new_metadata_buffer = []
        for idx, packet in enumerate(self._buffer):
            diff = getattr(x, self.timestamp_field) - getattr(packet, self.timestamp_field)
            if diff <= self.timedelta:
                new_buffer.append(self._buffer[idx])
                new_metadata_buffer.append(self._metadata_buffer[idx])
        new_buffer.append(x)
        if not isinstance(metadata, list):
            metadata = [metadata]
        new_metadata_buffer.append(metadata)
        flat_metadata = [m for l in new_metadata_buffer for m in l]
        self._buffer = new_buffer
        self._metadata_buffer = new_metadata_buffer
        ret = self._emit(tuple(self._buffer.copy()), flat_metadata)
        return ret

@sz.Stream.register_api()
class kalman_filter(sz.Stream):

    kf = KalmanFilter(dim_x=1, dim_z=1)
    kf.x = None
    kf.F = np.eye(1)
    kf.H = np.eye(1)
    kf.R = 1
    kf.Q = 0.1

    def __init__(self, upstream, key, *args, **kwargs):
        self.key_selector = key
        # this is one of a few stream specific kwargs
        stream_name = kwargs.pop('stream_name', None)
        self.kwargs = kwargs
        self.args = args

        sz.Stream.__init__(self, upstream, stream_name=stream_name)

    def update(self, x, who=None, metadata=None):
        try:
            input = getattr(x, self.key_selector)
            if self.kf.x is None:
                self.kf.x = input
            self.kf.predict()
            self.kf.update(np.array([input]))
            result = self.kf.x[0, 0]
        except Exception:
            raise
        else:
            setattr(x, self.key_selector, result)
            return self._emit(x, metadata=metadata)


class BpNodeStream:

    def __init__(self, ubertooth: Ubertooth):
        self._ubertooth = ubertooth
        self._serial = ubertooth.serial

        self._source: sz.Stream = sz.Stream(asynchronous=True)

        self._unique_laps = self._source.map(lambda pkt: pkt.LAP).unique()

        def get_stream_of_packets_for_lap(lap):
            return self._source.filter(lambda pkt, l=lap: pkt.LAP == l)
        self._streams_of_packets_for_laps: sz.Stream = \
            self._unique_laps.map(lambda lap: (lap, get_stream_of_packets_for_lap(lap)))

        def get_stream_of_filtered_packets_for_lap(stream):

            def filter_with_max(packets):
                if len(packets) <= 1:
                    return packets
                signals = list(map(lambda x: x.signal, packets))
                max_rssi = max(signals)
                if packets[-1].signal >= max_rssi:
                    return [packets[-1]]
                else:
                    return []

            def filter_with_mean(packets):
                most_recent = packets[-1]
                if len(packets) == 1:
                    return (most_recent.timestamp, most_recent.signal)
                signals = list(map(lambda x: x.signal, packets))
                mean_signal = statistics.mean(signals)
                return (most_recent.timestamp, mean_signal)

            return stream.sliding_time_window(20, "timestamp") \
                .map(filter_with_max) \
                .flatten() \
                .sliding_time_window(20, "timestamp") \
                .map(filter_with_mean)

        self._streams_of_filtered_packets_for_laps: sz.Stream = \
            self._streams_of_packets_for_laps.map(lambda x: (x[0], get_stream_of_filtered_packets_for_lap(x[1])))

    async def start(self):
        async for packet in self._ubertooth.rx_stream():
            self._source.emit(packet, asynchronous=True)

    def stop(self):
        return self._ubertooth.close()

    def get_stream_of_streams_for_laps(self):
        return self._streams_of_filtered_packets_for_laps

    def get_stream_of_packets_with_laps(self):
        return self._source
