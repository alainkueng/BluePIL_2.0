"""Copyright 2013 - 2013 Ryan Holeman

This file is part of Project pyubertooth.

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2, or (at your option)
any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; see the file COPYING.  If not, write to
the Free Software Foundation, Inc., 51 Franklin Street,
Boston, MA 02110-1301, USA."""

import asyncio
import time
import struct
from collections import deque
from datetime import datetime

import usb.core

from node.bp_btbb_packet import BtbbPacket

USB_ID_VENDOR = 0x1D50
USB_ID_PRODUCT = 0x6002

USB_CTRL_READ = 0xc0
USB_CTRL_WRITE = 0x40
USB_ENDPT_2 = 0x82

NUM_BR_EDR_CHANNELS = 79


def get_devices():
    result = {}
    devices = usb.core.find(idVendor=USB_ID_VENDOR,
                            idProduct=USB_ID_PRODUCT, find_all=True)
    for device in devices:
        serial = cmd_get_serial(device)
        result[serial] = device
    return result

def get_uberteeth():
    devices = [x[1] for x in get_devices().items()]
    uberteeth = [Ubertooth(x) for x in devices]
    return uberteeth


def cmd_get_serial(device):
    serial = device.ctrl_transfer(USB_CTRL_READ, 14, 0, 0, 17)
    serial = ''.join([format(i, '02x') for i in serial[1:]])
    return serial


class Ubertooth(object):

    def __init__(self, device=None):
        if device:
            self.device = device
        else:
            self.device = usb.core.find(idVendor=USB_ID_VENDOR,
                                        idProduct=USB_ID_PRODUCT)
        self._init_device()
        self.serial = cmd_get_serial(self.device)
        self._is_closed = True
        rssi_hist_starting_values = [-1000] * 10
        self._rssi_hist_for_channel = [deque(rssi_hist_starting_values, maxlen=10)] * NUM_BR_EDR_CHANNELS

    def _init_device(self):
        self.device.default_timeout = 3000
        self.device.set_configuration()

    def set_channel(self, channel=9999):
        self.device.ctrl_transfer(USB_CTRL_WRITE, 12, 2402 + channel, 0)

    def set_rx_mode(self):
        self.device.ctrl_transfer(USB_CTRL_WRITE, 1, 0, 0)

    async def rx_stream(self, count=None, secs=None, channel=9999):
        self._is_closed = False
        self.set_rx_mode()
        self.set_channel(channel)
        i = 0
        start = time.time()
        loop = asyncio.get_event_loop()
        while True:
            if count is not None:
                if i >= count:
                    break
                i += 1
            if secs is not None:
                if time.time() >= start + secs:
                    break
            if self._is_closed:
                break
            usb_data = await loop.run_in_executor(None, self.device.read, USB_ENDPT_2, 64)
            packet = self._usb_to_btbbpacket(usb_data)
            if packet.LAP is not None:
                yield packet

    def rx_stream_sync(self, count=None, secs=None, channel=9999):
        self._is_closed = False
        self.set_rx_mode()
        self.set_channel(channel)
        i = 0
        start = time.time()
        while True:
            if count is not None:
                if i >= count:
                    break
                i += 1
            if secs is not None:
                if time.time() >= start + secs:
                    break
            if self._is_closed:
                break
            usb_data = self.device.read(USB_ENDPT_2, 64)
            packet = self._usb_to_btbbpacket(usb_data)
            if (packet.LAP is not None) & self._is_channel_sane(packet):
                yield packet

    def _usb_to_btbbpacket(self, usb_data):
        packet = BtbbPacket(usb_data, datetime.now())
        if self._is_channel_sane(packet):
            packet.signal = self._determine_signal(packet)
        return packet

    def _determine_signal(self, packet):
        rssi_hist = self._rssi_hist_for_channel[packet.channel]
        rssi_hist.pop()
        rssi_hist.appendleft(packet.rssi_max)
        rssi = max(rssi_hist)
        return BtbbPacket.cc2400_rssi_to_dbm(rssi)

    @staticmethod
    def _is_channel_sane(packet):
        return 0 <= packet.channel < NUM_BR_EDR_CHANNELS

    def close(self):
        self._is_closed = True
        self.device.ctrl_transfer(USB_CTRL_WRITE, 21)
        self.device.ctrl_transfer(USB_CTRL_WRITE, 13)

    def cmd_ping(self):
        # cmd ping
        # line 75 ubertooth_control.c
        result = self.device.ctrl_transfer(USB_CTRL_READ, 0, 0, 0, 0)
        return result

    def cmd_get_serial(self):
        cmd_get_serial(self.device)

    def cmd_set_modulation(self, modulation=0):
        # set modulation 0-2 where 0=BTBR 1=BTLE 2=80211_FHSS
        # line 303 ubertooth_control.c
        self.device.ctrl_transfer(USB_CTRL_WRITE, 23, modulation, 0)

    def cmd_reset(self):
        # reset ubertooth
        # line 334 ubertooth_control.c
        self.device.ctrl_transfer(USB_CTRL_WRITE, 13, 0, 0)

    def cmd_stop(self):
        # stop ubertooth
        # line 349 ubertooth_control.c
        self.device.ctrl_transfer(USB_CTRL_WRITE, 21, 0, 0)

    def cmd_set_squelch(self, level=0):
        # set squelch where level is ???
        # line 587 ubertooth_control.c
        self.device.ctrl_transfer(USB_CTRL_WRITE, 36, level, 0)

    def cmd_get_squelch(self):
        # get squelch where level is default 136
        # line 587 ubertooth_control.c
        level = self.device.ctrl_transfer(USB_CTRL_READ, 37, 0, 0, 1)
        level = struct.unpack('B', level)[0]
        return level

    def cmd_set_usrled(self, state=0):
        # set usrled where state is 0-1
        # line 127 ubertooth_control.c
        self.device.ctrl_transfer(USB_CTRL_WRITE, 4, state, 0)
