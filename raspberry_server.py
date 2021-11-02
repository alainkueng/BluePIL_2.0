import socket
import time

from run_node import main

host = ''
port = 5560
sleep = False

def setupServer():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    print('Socket created')
    try:
        s.bind((host, port))
    except socket.error as msg:
        print(msg)
    print("Socket bind complete")
    return s


def setupConnection():
    s.listen(1)
    conn, address = s.accept()
    print('connected to: ' + address[0] + ':' + str(address[1]))
    return conn


def start_node():
    main()


def dataTransfer(conn):
    # big loop to send/receive data
    while True:
        # receive
        data = conn.recv(1024)
        data = data.decode('utf-8')
        # split data to seperate command from the rest of data
        data_message = data.split(' ', 1)
        command = data_message[0]
        if command == 'START_NODE':
            print('Started Node')
            start_node()
            time.sleep(2)
            reply = 'Node Terminated, ready for another Task'
        elif command == 'EXIT':
            print('Client left')
            break
        elif command == 'KILL':
            print('Our server is shutting down.')
            s.close()
            break
        else:
            reply = 'Unknown Command'
        # Send the reply back to the client
        conn.sendall(str.encode(reply))
        print('Data Sent!')
    conn.close()


s = setupServer()

while True:
    try:
        conn = setupConnection()
        dataTransfer(conn)
    except:
        break
