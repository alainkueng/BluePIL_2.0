import pickle
from dataclasses import dataclass
from enum import Enum

CONFIG_PORT = 8099

SINK_HOSTNAME_FIELD = "SINK_HOSTNAME"
SINK_REG_PORT_FIELD = "SINK_REG_PORT"
SINK_DATA_PORT_FIELD = "SINK_DATA_PORT"


def encode(data):
    return pickle.dumps(data)


def decode(data):
    return pickle.loads(data)


class ConfigType(Enum):
    STARTUP = 1
    SHUTDOWN = 2


class Mode(Enum):
    POSITIONING = 1
    RAW = 2
    RAW_LOCAL = 3

    def __str__(self):
        return self.name


@dataclass
class ConfigMsg:
    type: ConfigType
    mode: Mode
    data: object = None