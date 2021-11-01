import socket
import time

from run_sink import main

hosts = ["192.168.1.101", "192.168.1.102", "192.168.1.103", "192.168.1.104"]

ports = [5560, 5561, 5562, 5563]

connections = {}

for host, port in hosts, ports:
    while True:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((host, port))

        except ConnectionRefusedError as msg:
            time.sleep(2)
            continue
        print('Successful connected to ' + host + ' with port ' + str(port))
        break
print('All connections worked!')
time.sleep(3)



s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((host1, port))

while True:
    command = input('Enter your command: ')
    if command == 'EXIT':
        # Send EXIT request
        s.send(str.encode(command))
        break
    elif command == 'KILL':
        s.send(str.encode(command))
        break
    elif command == 'START_NODE':
        s.send(str.encode(command))
        break
    s.send(str.encode(command))
    reply = s.recv(1024)
    print(reply.decode('utf-8'))

s.close()
