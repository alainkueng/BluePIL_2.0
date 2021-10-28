import struct
import datetime as dt
import pandas as pd
from scapy.all import rdpcap

timestamp_col = 'timestamp'
lap_col = 'lap'
channel_col = 'channel'
signal_col = 'signal'
noise_col = 'noise'

def s8(value):
    return struct.unpack('>b', struct.pack('>B', value))[0]

def from_decimal_seconds(timestamp):
    return dt.datetime.fromtimestamp(0) + dt.timedelta(microseconds=int(timestamp * 1000000))

#%%

def get_signal(packet):
    return s8(packet.load[1])

def get_noise(packet):
    return s8(packet.load[2])

def get_channel(packet):
    return s8(packet.load[0])

def get_lap(packet):
    return struct.pack('<4b', *struct.unpack('>4b', packet.load[8:12])).hex()

def get_datetime(packet):
    return from_decimal_seconds(packet.time)


def get_row_for_packet(packet):
    channel = get_channel(packet)
    signal = get_signal(packet)
    noise = get_noise(packet)
    timestamp = get_datetime(packet)
    lap = get_lap(packet)
    return {timestamp_col: timestamp, lap_col: lap, channel_col: channel, signal_col: signal, noise_col: noise}


def get_df_for_pcap(pcap, lap):
    data = []
    for packet in pcap:
        data.append(get_row_for_packet(packet))
    df = pd.DataFrame(data, columns=[timestamp_col, lap_col, channel_col, signal_col, noise_col]).set_index(
        timestamp_col, drop=False)

    return df[df["lap"] == lap]

def read_pcap_to_df(pcap_file, lap):
    pcap = rdpcap(pcap_file)
    return get_df_for_pcap(pcap, lap)