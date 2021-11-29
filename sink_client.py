import socket
import time

from run_sink import run_sink

def get_ips():
    import json
    ips = []
    with open("bp.json") as f:
        conf = json.load(f)
        for i in range(1, 5):
            ip = conf[f'node{i}']["ip"]
            ips.append(ip)
    return ips


class SinkClient:

    def __init__(self):
        self.hosts = get_ips()
        self.ports = [5560, 5561, 5562, 5563]
        self.connections = {}

    def start(self):
        for host, port in zip(self.hosts, self.ports):
            while True:
                try:
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    s.connect((host, port))
                    self.connections[host] = s
                except Exception as msg:
                    time.sleep(2)
                    continue
                print('Successful connected to ' + host + ' with port ' + str(port))
                break
        print('All connections worked!')
        self.run()

    def run(self):
        while True:
            command = input('Enter your command: ')
            if command == 'EXIT':
                # Send EXIT request
                self.send(command)
                break
            elif command == 'KILL':
                self.send(command)
                break
            elif command == 'START_NODE':
                self.send_once(command)
                self.start_run_sink()
                break
            else:
                self.send(command)
        self.close()


    def send(self, command):
        for s in self.connections.values():
            s.send(str.encode(command))
            reply = s.recv(1024)
            print(reply.decode('utf-8'))

    def close(self):
        for s in self.connections.values():
            s.close()

    def start_run_sink(self):
        print('Wait for the nodes to start, sleeping for 6 seconds')
        time.sleep(6)
        run_sink()

    def send_once(self, command):
        for s in self.connections.values():
            s.send(str.encode(command))


SinkClient().start()
