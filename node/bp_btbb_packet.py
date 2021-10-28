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

import struct

from node.barker_correct_tables import BARKER_DISTANCE, barker_correct
from node.sw_check_tables import sw_check_table4, sw_check_table5, sw_check_table6, sw_check_table7

NUM_BREDR_CHANNELS = 79

RSSI_HISTORY_LEN = 10

INT8_MIN = -128

DEFAULT_AC = 0xcc7b7268ff614e1b

DEFAULT_CODEWORD = 0xb0000002c7820e7e

MAX_AC_ERRORS = 3

MAX_BARKER_ERRORS = 1

PN = '0x83848D96BBCC54FC'

syndrome_map = {}


def gen_syndrome(codeword):
    syndrome = codeword & int('0xffffffff', 16)
    codeword >>= 32
    syndrome ^= sw_check_table4[codeword & int('0xff', 16)]
    codeword >>= 8
    syndrome ^= sw_check_table5[codeword & int('0xff', 16)]
    codeword >>= 8
    syndrome ^= sw_check_table6[codeword & int('0xff', 16)]
    codeword >>= 8
    syndrome ^= sw_check_table7[codeword & int('0xff', 16)]
    return syndrome


def cycle(error, start, depth, codeword):
    # print "cycle ran"
    i = start
    base = 1
    depth -= 1
    while i < 58:
        new_error = (base << i)
        new_error |= error
        if depth:
            cycle(new_error, i + 1, depth, codeword)
        else:
            syndrome = gen_syndrome(codeword ^ new_error)
            syndrome_map[syndrome] = new_error
        i += 1


def gen_syndrome_map(bit_errors):
    i = 1
    while i <= bit_errors:
        cycle(0, 0, i, DEFAULT_AC)
        i += 1


gen_syndrome_map(MAX_AC_ERRORS)


class BtbbPacket(object):
    fields = ["LAP", "pkt_type", "status", "channel", "clkn_high",
                    "clk100ns", "rssi_max", "rssi_min", "rssi_avg",
                    "rssi_count", "timestamp", "signal"]

    def __init__(self, raw_data, timestamp):
        for field in BtbbPacket.fields:
            setattr(self, field, None)

        self.timestamp = timestamp

        pkt_header = raw_data[0:14]
        data = raw_data[14:64]

        self.air_bits = []
        for item in data:
            tmp = bin(item)[2:].zfill(8)
            for i in tmp:
                self.air_bits.append(i)

        self.barker = self.btbb_find_ac(data[7])
        self.LAP = self.detect_lap()

        self.pkt_type, self.status, self.channel, self.clkn_high, self.clk100ns, self.rssi_max, \
                self.rssi_min, self.rssi_avg, self.rssi_count, _, _ = \
                struct.unpack("<BBBBLbbbBBB", pkt_header)

    @staticmethod
    def count_bits(n):
        foo = bin(n)[2:]
        return foo.count('1')

    @staticmethod
    def btbb_find_ac(byte):
        # """not the best implementation, only looks at one rx data bank, does
        # not match ut c libs for all rx data banks.  Does match on ut c libs lap
        # hits when compairing nanoseconds. This implementation also has a direct
        # corilation with rx packet where ut c lib sends symbs/symbols.
        #
        # Also, I am consuming a byte here.  This was from my old ugly code"""
        barker = bin(byte)[2:].zfill(8)[1:7]
        barker = int(''.join(list(barker)[::-1]), 2)
        return barker

    @staticmethod
    def cc2400_rssi_to_dbm(rssi):
        if rssi < -48:
            return -120
        elif rssi <= -45:
            return 6 * (rssi + 28)
        elif rssi <= 30:
            return (99 * (rssi - 62)) / 110
        elif rssi <= 35:
            return (60 * (rssi - 35)) / 11
        else:
            return 0

    def detect_lap(self):
        barker = self.barker
        barker <<= 1
        # if we append other symbol bank we dont need to subtract 63...
        # for i in range(400 ):
        for i in range(400 - 63):
            barker >>= 1
            some_bit = int(self.air_bits[63 + i]) << 6
            barker |= some_bit
            if BARKER_DISTANCE[barker] <= MAX_BARKER_ERRORS:
                # """next 2 lines replace UT C method air_to_host_64.
                #     we do want to totaly fip 64 consecutive bits."""
                syncword = self.air_bits[i:i + 64]
                syncword.reverse()
                syncword = int(''.join(syncword), 2)
                corrected_barker = int(barker_correct[syncword >> 57], 16)
                syncword = syncword & int('0x01ffffffffffffff', 16) | corrected_barker
                codeword = syncword ^ int(PN, 16)
                syndrome = gen_syndrome(codeword)
                ac_errors = 0
                if syndrome:
                    errors = syndrome_map.get(syndrome, None)
                    if errors is not None:
                        syncword ^= errors
                        ac_errors = self.count_bits(errors)
                    else:
                        ac_errors = 0xff
                if ac_errors <= MAX_AC_ERRORS:
                    lap = (syncword >> 34) & 0xffffff
                    lap = hex(lap)[2:]
                    lap = lap.replace('L', '').zfill(6)
                    return lap

        return None

    def to_dict(self):
        return dict((f, getattr(self, f)) for f in BtbbPacket.fields)

    def __str__(self):
        # return str(self.to_dict())
        return str(dict((k, v) for k, v in self.to_dict().items() if v is not None))
