import asyncio
import concurrent
import csv
import dataclasses
from dataclasses import dataclass
from datetime import datetime

import streamz as sz

from sink.bp_kalman import BpKalman
from sink.bp_quadlateration import BpQuadlateration

_NUM_UBERTEETH = 4

@sz.Stream.register_api(staticmethod)
class merge_rssi_streams(sz.Stream):
    """

    """
    _graphviz_orientation = 270
    _graphviz_shape = 'triangle'

    @dataclass
    class Output:
        values: [float]
        timestamp: datetime

    def __init__(self, *upstreams, **kwargs):

        self.last = [None for _ in upstreams]
        self.metadata = [None for _ in upstreams]
        self.emit_on = upstreams
        self.waiting: [merge_rssi_streams.Output] = []
        sz.Stream.__init__(self, upstreams=upstreams, **kwargs)

    def _add_upstream(self, upstream):
        # Override method to handle setup of last and missing for new stream
        self.last.append(None)
        self.metadata.append(None)
        super(merge_rssi_streams, self)._add_upstream(upstream)

    def _remove_upstream(self, upstream):
        self.last.pop(self.upstreams.index(upstream))
        self.metadata.pop(self.upstreams.index(upstream))
        super(merge_rssi_streams, self)._remove_upstream(upstream)

    def update(self, x: (datetime, float), who=None, metadata=None):
        self._retain_refs(metadata)
        idx = self.upstreams.index(who)
        if self.metadata[idx]:
            self._release_refs(self.metadata[idx])
        self.metadata[idx] = metadata

        old_last = self.last[idx]

        if old_last is not None:
            def get_interpolation_func(last, current):
                last_s = last[0].timestamp()
                current_s = current[0].timestamp()
                gradient = (current[1] - last[1]) / (current_s - last_s)

                def interpolation_func(timestamp):
                    timestamp_s = timestamp.timestamp()
                    return last[1] + gradient * (timestamp_s - last_s)

                return interpolation_func

            interpol_func = get_interpolation_func(old_last, x)

            ready_for_emission = []
            new_waiting = []

            for waiting_emission in self.waiting:
                if waiting_emission.values[idx] is None:
                    waiting_emission.values[idx] = interpol_func(waiting_emission.timestamp)
                if None not in waiting_emission.values:
                    ready_for_emission.append(waiting_emission)
                else:
                    new_waiting.append(waiting_emission)

            self.waiting = new_waiting

            for emission in ready_for_emission:
                self._emit(emission)

        self.last[idx] = x

        if None not in self.last:
            values = [None for _ in self.upstreams]
            values[idx] = x[1]
            new_waiting_emission = merge_rssi_streams.Output(values, x[0])
            self.waiting.append(new_waiting_emission)

@sz.Stream.register_api()
class position(sz.Stream):

    @dataclass
    class Input:
        values: [float]
        dt: float
        timestamp: datetime

    @dataclass
    class Output:
        position: (float, float)
        timestamp: datetime

    def __init__(self, upstream, positions, n, initial_x, *args, **kwargs):
        self._quad = BpQuadlateration(*positions, n)
        self._kalman = BpKalman(initial_x)
        self._dim = len(positions)

        # this is one of a few stream specific kwargs
        stream_name = kwargs.pop('stream_name', None)
        self.kwargs = kwargs
        self.args = args

        sz.Stream.__init__(self, upstream, stream_name=stream_name)

    # x[0] should be values, x[1] should be dt, x[2] should be timestamp
    def update(self, input: Input, who=None, metadata=None):
        values = input.values
        dt = input.dt
        timestamp = input.timestamp
        if len(values) != self._dim:
            result = None
        else:
            try:
                x, y, _ = self._quad.quadlaterate(values[0], values[1], values[2], values[3]).x
                # x_filt, _, y_filt, _ = self._kalman.predict_update(x, y, dt)
                # result = (x_filt, y_filt)
                result = (x, y)
                # print(f'values: {values}, res: {result}')
            except Exception as e:
                sz.logger.exception(e)
                raise

        return self._emit(position.Output(result, timestamp), metadata=metadata)


class BpSinkStream:

    def __init__(self, streams_of_streams_for_laps, positions, n, initial_x):
        self._streams_for_laps = {}
        self._merged_streams_for_laps = {}
        self._all_streams = sz.Stream()

        self._streams_of_streams_for_laps = streams_of_streams_for_laps
        self._positions = positions
        self._n = n
        self._initial_x = initial_x

        [strm.sink(lambda lap_n_stream, i=idx: self._register_rssi_stream(lap_n_stream[0], i, lap_n_stream[1]))
         for idx, strm in enumerate(self._streams_of_streams_for_laps)]

    def _register_rssi_stream(self, lap, idx, stream):
        print("Registering stream {0} for LAP {1}".format(idx, lap))
        if lap not in self._streams_for_laps:
            self._streams_for_laps[lap] = [None] * _NUM_UBERTEETH
            csvfile = open(f'laps.csv', 'a')
            csvfile.write(lap +'\n')
            csvfile.close()
        self._streams_for_laps[lap][idx] = stream
        if None not in self._streams_for_laps[lap]:
            self._merge_rssi_streams(lap)

    def _merge_rssi_streams(self, lap):
        def mergeOutputsToPositioningInput(wes: [merge_rssi_streams.Output]):
            t0 = wes[0].timestamp
            we = wes[1]
            t1 = we.timestamp
            dt = (t1 - t0).total_seconds()
            return position.Input(we.values, dt, t1)
        print("Starting positioning stream for LAP {0}".format(lap))
        merged = sz.Stream.merge_rssi_streams(*self._streams_for_laps[lap]) \
            .sliding_window(2,  return_partial=False) \
            .map(mergeOutputsToPositioningInput) \
            .position(self._positions, self._n, self._initial_x)
        self._merged_streams_for_laps[lap] = merged

        def to_dict_with_lap(x, lap):
            dict = dataclasses.asdict(x)
            dict["LAP"] = lap
            return dict
        merged.sink(lambda x, l=lap, allstrms=self._all_streams: allstrms.emit(to_dict_with_lap(x, l)))

    def get_results_stream(self):
        return self._all_streams

# def main():
#     uberteeth = get_uberteeth()
#     assert len(uberteeth) == _NUM_UBERTEETH
#
#     positions = []
#
#     for ubertooth in uberteeth:
#         ubertooth.cmd_set_usrled(1)
#         print("Enter the coordinates for the device {0}:".format(ubertooth.serial))
#         x = float(input("x = "))
#         print("input {0}".format(x))
#         y = float(input("y = "))
#         print("input {0}".format(y))
#         positions.append((x, y))
#         ubertooth.cmd_set_usrled(0)
#
#     assert (len(uberteeth) == _NUM_UBERTEETH)
#     assert (len(positions) == _NUM_UBERTEETH)
#
#     ustreams = list(map(lambda x: UbertoothStream(x), uberteeth))
#
#     streams_of_streams_for_laps = [us.get_stream_of_streams_for_laps() for us in ustreams]
#
#     QuadlaterationStream(streams_of_streams_for_laps, positions, 1.8, (0.5, 0, 0.5, 0))
#
#     tasks = [x.start() for x in ustreams]
#
#     async def start():
#         await asyncio.wait(tasks, return_when=concurrent.futures.FIRST_EXCEPTION)
#
#     def stop():
#         [x.stop() for x in ustreams]
#
#     loop = asyncio.get_event_loop()
#     try:
#         loop.create_task(start())
#         loop.run_forever()
#     except KeyboardInterrupt:
#         print("\n\nStopping...\n\n")
#         pass
#     finally:
#         stop()
#
#         loop.stop()
#         print("Done\n\n")
#
# if __name__ == '__main__':
#     main()