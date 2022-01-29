from common import Mode
from sink.bp_sink import main


def run_sink():
    import json

    with open("bp.json") as f:
        conf = json.load(f)

    if conf["mode"] == "RAW":
        mode = Mode.RAW
    elif conf["mode"] == "RAW_LOCAL":
        mode = Mode.RAW_LOCAL
    elif conf["mode"] == "POSITIONING":
        mode = Mode.POSITIONING
    else:
        raise NotImplementedError("An invalid Mode was set in the config file")
    print(mode)

    sensor_ips = []
    sensor_locs = []
    number_of_nodes = conf["number_of_nodes"]
    for i in range(1, number_of_nodes+1):
        sensorconf = conf[f'node{i}']
        ip = sensorconf["ip"]
        loc = sensorconf["loc"]
        sensor_ips.append(ip)
        sensor_locs.append(loc)

    main(mode, sensor_ips, sensor_locs)
