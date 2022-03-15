import socket
import multiprocessing

from run_node import main

host = ''
port = 5560


class Server:
    def __init__(self):
        self.socket = self.setupServer()
        self.node_process = multiprocessing.Process(target=start_node)

    def setupServer(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        print('Socket created')
        try:
            s.bind((host, port))
        except socket.error as msg:
            print(msg)
        print("Socket bind complete")
        return s

    def loop(self):
        while True:
            try:
                conn = self.setupConnection()
                self.dataTransfer(conn)
            except:
                break

    def setupConnection(self):
        self.socket.listen(1)
        conn, address = self.socket.accept()
        print('Connected to: ' + address[0] + ':' + str(address[1]))
        return conn

    def dataTransfer(self,conn):
        # big loop to send/receive data
        while True:
            # receive
            data = conn.recv(1024)
            data = data.decode('utf-8')
            # split data to separate command from the rest of data
            data_message = data.split(' ', 1)
            command = data_message[0]
            # kills process if new client connects, ensures if something goes wrong the process can still be restarted
            if self.node_process.is_alive():
                self.node_process.terminate()
            # different commands
            if command == 'START_NODE':
                reply = 'Starting node..'
                conn.sendall(str.encode(reply))
                self.node_process = multiprocessing.Process(target=start_node)
                self.node_process.start()
                break
            elif command == 'EXIT':
                break
            elif command == 'KILL':
                self.socket.close()
                break
            else:
                reply = 'Unknown Command'
                conn.sendall(str.encode(reply))
        conn.close()

def start_node():
    main()

s = Server()
s.loop()


