import asyncio
import csv
import socket
from datetime import datetime

import streamz

from node.bp_btbb_packet import BtbbPacket
from common import CONFIG_PORT, SINK_HOSTNAME_FIELD, SINK_DATA_PORT_FIELD, SINK_REG_PORT_FIELD, decode, ConfigType, \
    encode, Mode
from node.bp_ubertooth import get_uberteeth
from node.bp_node_stream import BpNodeStream


class BpNode:

    def __init__(self):
        self._hostname = socket.gethostname()

    def start(self):
        try:
            asyncio.run(self._init_config_socket())
        except KeyboardInterrupt:
            self.stop()

    def stop(self):
        self._shutdown()

    async def _init_config_socket(self):
        async def handle_config_msg(reader, _):
            data = await reader.read(256)
            message = decode(data)
            await self._handle_config_message(message)

        print(f'Starting Config Bus on {self._hostname}:{CONFIG_PORT}')
        server = await asyncio.start_server(handle_config_msg, port=CONFIG_PORT)
        async with server:
            await server.serve_forever()


    async def _handle_config_message(self, message):

        if message.type == ConfigType.STARTUP:
            uberteeth = get_uberteeth()
            print(uberteeth)
            ubertooth = uberteeth[0]
            self._node_stream = BpNodeStream(ubertooth)
            self._mode = message.mode
            if self._mode == Mode.POSITIONING:
                data = message.data
                self._sink_hostname = data[SINK_HOSTNAME_FIELD]
                self._sink_dataport = data[SINK_DATA_PORT_FIELD]
                self._sink_regport = data[SINK_REG_PORT_FIELD]
                print(f'\nStartup signal received:\n'
                      f'\n\tMode: {message.mode}'
                      f'\n\tHostname: {self._sink_hostname}'
                      f'\n\tRegistration Port: {self._sink_regport}'
                      f'\n\tData Port: {self._sink_dataport}\n')
                self._init_registration_stream()
                self._init_data_stream()
            elif self._mode == Mode.RAW:
                data = message.data
                self._sink_hostname = data[SINK_HOSTNAME_FIELD]
                self._sink_dataport = data[SINK_DATA_PORT_FIELD]
                print(f'\nStartup signal received:\n'
                      f'\n\tMode: {message.mode}'
                      f'\n\tHostname: {self._sink_hostname}'
                      f'\n\tData Port: {self._sink_dataport}\n')
                self._init_raw_data_stream()
            elif self._mode == Mode.RAW_LOCAL:
                print(f'\nStartup signal received:\n'
                      f'\n\tMode: {message.mode}')
                self._init_raw_data_stream_local()
            await self._startup()
        elif message.type == ConfigType.SHUTDOWN:
            print('\nShutdown signal received\n')
            self._shutdown()

    async def _startup(self):
        print("Starting up...")
        print("\tStarting Ubertooth")
        await self._node_stream.start()
        print("Done")

    def _shutdown(self):
        print('Shutting down...')
        print("\tStopping Ubertooth")
        streamz.core._global_sinks.clear()
        self._node_stream.stop()
        if self._mode == Mode.RAW_LOCAL:
            self._csv_file.close()
        print("Done")

    def _init_registration_stream(self):
        self._node_stream.get_stream_of_streams_for_laps().sink(lambda x: self._send_registration(x[0]))

    def _init_data_stream(self):

        def init_data_stream_for_lap(lap, strm):
            strm.sink(lambda x: self._send_data((lap, x)))

        self._node_stream.get_stream_of_streams_for_laps().sink(lambda x: init_data_stream_for_lap(*x))

    def _init_raw_data_stream(self):
        self._node_stream.get_stream_of_packets_with_laps()\
            .map(lambda x: (x.LAP, x.rssi_max, x.rssi_min, x.clk100ns, x.timestamp, x.channel, x.signal))\
            .sink(lambda x: self._send_data(x))

    def _init_raw_data_stream_local(self):
        def datetime_to_string(dt):
            return f"{dt:%Y-%m-%d_%H:%M:%S.%f}"

        filename = f"/root/BluePILdata/{datetime_to_string(datetime.now())}.csv"
        self._csv_file = open(filename, 'w')
        writer = csv.DictWriter(self._csv_file, fieldnames=BtbbPacket.fields)
        writer.writeheader()

        def print_data_to_csv(btbb_packet):
            print(f"{datetime_to_string(datetime.now())}: writing for LAP {btbb_packet.LAP}")
            writer.writerow(btbb_packet.to_dict())
            self._csv_file.flush()

        self._node_stream.get_stream_of_packets_with_laps()\
            .sink(lambda x: print_data_to_csv(x))

    async def _send_registration(self, data):
        print(f"sending reg {data}")
        _, self._regwriter = await asyncio.open_connection(self._sink_hostname, self._sink_regport)
        self._regwriter.write(encode(data))
        self._regwriter.close()

    async def _send_data(self, data):
        print(f"sending data {data}")
        _, self._datawriter = await asyncio.open_connection(self._sink_hostname, self._sink_dataport)
        self._datawriter.write(encode(data))
        self._datawriter.close()


def main():
    ud = BpNode()
    ud.start()