import socket
import multiprocessing

from run_node import main

host = ''
port = 5560


class Server:
    def __init__(self):
        self.s = self.setupServer()
        self.p = multiprocessing.Process(target=start_node)

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
        self.s.listen(1)
        conn, address = self.s.accept()
        print('connected to: ' + address[0] + ':' + str(address[1]))
        return conn

    def dataTransfer(self,conn):
        # big loop to send/receive data
        while True:
            # receive
            data = conn.recv(1024)
            data = data.decode('utf-8')
            # split data to seperate command from the rest of data
            data_message = data.split(' ', 1)
            command = data_message[0]
            if self.p.is_alive():
                self.p.terminate()
            if command == 'START_NODE':
                reply = 'Starting node..'
                conn.sendall(str.encode(reply))
                self.p = multiprocessing.Process(target=start_node)
                self.p.start()
                break
            elif command == 'EXIT':
                break
            elif command == 'KILL':
                self.s.close()
                break
            elif command == 'INFO':
                conn.sendall(str.encode('Node terminated {0}'.format(not self.p.is_alive())))
            else:
                reply = 'Unknown Command'
                conn.sendall(str.encode(reply))
        conn.close()

def start_node():
    main()

s = Server()
s.loop()


