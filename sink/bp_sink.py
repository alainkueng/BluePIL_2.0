import asyncio
import csv
import socket
from dataclasses import dataclass

import streamz

from common import CONFIG_PORT, SINK_HOSTNAME_FIELD, SINK_REG_PORT_FIELD, \
    SINK_DATA_PORT_FIELD, encode, ConfigMsg, ConfigType, decode, Mode
from sink.bp_sink_stream import BpSinkStream

WRITTEN_TS = "written_timestamp"


@dataclass
class UbertoothConnection:
    hostname: str
    regport: int
    dataport: int
    position: (float, float)
    regstream: streamz.Stream
    datastream: streamz.Stream
    stream_of_streams: streamz.Stream


class BpSink:

    def __init__(self, ubertooth_hostnames, ubertooth_positions, mode: Mode):
        self._mode = mode
        assert len(ubertooth_hostnames) == len(ubertooth_positions)
        self._hostname = socket.gethostname()
        self._free_ports = set(range(8090, 8099))
        self.csvfiles = []
        self._init_ubertooth_configs(ubertooth_hostnames, ubertooth_positions)
        if self._mode == Mode.POSITIONING:
            self._init_quadlateration()
        elif self._mode == Mode.RAW:
            self._init_raw()
        elif self._mode == Mode.RAW_LOCAL:
            self._init_raw_local()

    def _init_ubertooth_configs(self, ubertooth_hostnames: [str], ubertooth_positions: [(float, float)]):

        def get_free_port():
            try:
                return self._free_ports.pop()
            except KeyError:
                raise ValueError("Too few ports available for number of uberteeth")

        def init_config(hostname, pos):
            regport = get_free_port()
            dataport = get_free_port()
            regstream = streamz.Stream(asynchronous=True)
            datastream = streamz.Stream(asynchronous=True)
            stream_of_streams = regstream.map(lambda x: (x, datastream.filter(lambda y, l=x: y[0] == l).map(lambda y: y[1])))
            return UbertoothConnection(hostname, regport, dataport, pos, regstream, datastream, stream_of_streams)

        self._ubertooth_connections = \
            [init_config(hostname, pos) for (hostname, pos) in zip(ubertooth_hostnames, ubertooth_positions)]

    def _init_quadlateration(self):

        def sink_to_file(file, writer, data):
            #print(f"writing data {data}")
            writer.writerow([data["position"][0], data["position"][1], data["timestamp"], data["LAP"]])
            file.flush()

        streams_of_streams = [connection.stream_of_streams for connection in self._ubertooth_connections]
        positions = [connection.position for connection in self._ubertooth_connections]

        self._sink_stream = BpSinkStream(streams_of_streams, positions, 1.8, (0.5, 0, 0.5, 0))
        csvfile = open(f'positions.csv', 'w')
        self.csvfiles.append(csvfile)
        csvcols = list(["x", "y", "timestamp", "LAP"])
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(csvcols)
        self._sink_stream.get_results_stream().sink(lambda x, y=csvwriter, z=csvfile: sink_to_file(z, y, x))

    def _init_raw(self):
        def sink_to_file(file, writer, data):
            #print(f"writing data {data}")
            writer.writerow(data)
            file.flush()

        for connection in self._ubertooth_connections:
            csvfile = open(f'{connection.hostname}.csv', 'w')
            csvcols = ["LAP", "rssi_max", "rssi_min", "clk100ns", "timestamp", "channel", "signal"]
            csvwriter = csv.writer(csvfile)
            self.csvfiles.append(csvfile)
            csvwriter.writerow(csvcols)
            #print(f"setting up writer for {connection.hostname}")
            connection.datastream.sink(lambda x, y=csvwriter, z=csvfile: sink_to_file(z, y, x))

    def _init_raw_local(self):
        pass

    def start(self):
        print("Starting")
        try:
            asyncio.run(self._startup())
        except KeyboardInterrupt:
            print('Stopping the nodes')
            self.stop()

    def stop(self):
        asyncio.run(self._shutdown())


    async def _startup(self):
        self._servers = []
        if self._mode == Mode.POSITIONING:
            await self._startup_positioning()
        elif self._mode == Mode.RAW:
            await self._startup_raw()
        elif self._mode == Mode.RAW_LOCAL:
            await self._startup_raw_local()

    async def _startup_positioning(self):
        await self._init_registration_buses()
        await self._init_data_buses()
        await self._configure_nodes_positioning()
        await self._start_servers()

    async def _startup_raw(self):
        await self._init_data_buses()
        await self._configure_nodes_raw()
        await self._start_servers()

    async def _startup_raw_local(self):
        await self._configure_nodes_raw_local()

    async def _configure_nodes_positioning(self):
        host_ip = socket.gethostbyname(self._hostname)

        async def configure_node(u_config):
            message = ConfigMsg(ConfigType.STARTUP,
                                self._mode,
                                {SINK_HOSTNAME_FIELD: host_ip,
                                    SINK_REG_PORT_FIELD: u_config.regport,
                                    SINK_DATA_PORT_FIELD: u_config.dataport})
            await self._send_on_config_bus(message, u_config)

        tasks = [configure_node(u_config) for u_config in self._ubertooth_connections]
        await asyncio.wait(tasks)

    async def _configure_nodes_raw(self):
        host_ip = socket.gethostbyname(self._hostname)

        async def configure_node(u_config):
            message = ConfigMsg(ConfigType.STARTUP,
                                self._mode,
                                {SINK_HOSTNAME_FIELD: host_ip, SINK_DATA_PORT_FIELD: u_config.dataport})
            await self._send_on_config_bus(message, u_config)

        tasks = [configure_node(u_config) for u_config in self._ubertooth_connections]
        await asyncio.wait(tasks)

    async def _configure_nodes_raw_local(self):

        configtype = None
        while configtype is None:
            inpt = int(input("what should i do? (1: start, 2: stop)"))
            if inpt == 1:
                configtype = ConfigType.STARTUP
            elif inpt == 2:
                configtype = ConfigType.SHUTDOWN

        async def configure_node(u_config):
            message = ConfigMsg(configtype,
                                self._mode)
            await self._send_on_config_bus(message, u_config)

        tasks = [configure_node(u_config) for u_config in self._ubertooth_connections]
        await asyncio.wait(tasks)

    async def _shutdown(self):
        await self._stop_nodes()
        for csvfile in self.csvfiles:
            csvfile.close()
        #print('Sink shuts down')

    async def _stop_nodes(self):

        async def stop_node(u_con: UbertoothConnection):
            message = ConfigMsg(ConfigType.SHUTDOWN, self._mode)
            await self._send_on_config_bus(message, u_con)

        tasks = [stop_node(u_config) for u_config in self._ubertooth_connections]
        await asyncio.wait(tasks)
        #print('Nodes terminated')

    @staticmethod
    async def _send_on_config_bus(message: ConfigMsg, u_config):

        _, config_writer = await asyncio.open_connection(u_config.hostname, CONFIG_PORT)
        msg_enc = encode(message)
        #print(f'Sending configuration: {message}')
        config_writer.write(msg_enc)
        await config_writer.drain()
        #print(f'sent message: {message}')
        config_writer.close()

    async def _init_registration_buses(self):

        async def init_registration_bus(port, stream):
            async def handle_reg_msg(reader, _):
                data = await reader.read(64)
                message = decode(data)
                stream.emit(message)

            #print(f"Starting Registration Server on port {port}")
            self._servers.append(await asyncio.start_server(handle_reg_msg, port=port))

        tasks = [init_registration_bus(uc.regport, uc.regstream) for uc in self._ubertooth_connections]
        await asyncio.wait(tasks)

    async def _init_data_buses(self):

        async def init_data_bus(port, stream):

            async def handle_data_msg(reader, _):
                data = await reader.read(256)
                message = decode(data)
                stream.emit(message)

            #print(f"Starting Data Server on port {port}")
            self._servers.append(await asyncio.start_server(handle_data_msg, port=port))

        tasks = [init_data_bus(uc.dataport, uc.datastream) for uc in self._ubertooth_connections]
        await asyncio.wait(tasks)

    async def _start_servers(self):
        async def start_server(server):
            async with server:
                await server.serve_forever()
        tasks = [await start_server(server) for server in self._servers]
        await asyncio.gather(*tasks)


def main(mode, ips, locs):
    qd = BpSink(ips, locs, mode)
    qd.start()
