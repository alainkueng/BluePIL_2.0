import socket
from run_node import main

host = ''
port = 5560

storedValue = 'YOOYOO'


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
    reply = 'Stopped Node'
    return reply


def REPEAT(data_message):
    reply = data_message[1]
    return reply


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
            reply = start_node()
        elif command == 'REPEAT':
            reply = REPEAT(data_message)
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
