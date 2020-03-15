import threading
import socket

MTU = 1500

class Connection(threading.Thread):
    def __init__(self, socket, addr):
        super(Connection, self).__init__()
#        self.daemon = True
        self.socket = socket
        self.addr = addr
        self.interrupted = False
    def run(self):
        while not self.interrupted:
            data = self.socket.recv(MTU)
            if not data: break #socket is closed
            self.onRecv(data)
        self.socket.close()

    def onRecv(self, data):
        pass #override this

    def send(self, data):
        self.socket.send(data)

def connect(hostname, port, clientClass):
    addr = (hostname, port)
    s = socket.socket()
    s.connect(addr)
    client = clientClass(s, addr)
    client.start()
    return client

class SocketAcceptor(threading.Thread):
    def __init__(self, socket, ClientClass, emiter):
        super(SocketAcceptor, self).__init__()
#        self.daemon = True
        self.socket = socket
        self.emiter = emiter
        self.clientClass = ClientClass
        self.interrupted = False
        self.clients = []
    def run(self):
        while not self.interrupted:
            c, addr = self.socket.accept()
            print("New Client: %s:%d" % addr)
            client = self.clientClass(c, addr, emiter)
            client.start()
            self.clients.append(client)
        self.socket.close()

    def stop(self):
        for c in self.clients:
            c.interrupted = True
            c.socket.close()
        self.interrupted = True

class ForwarderConnection(Connection):
    def __init__(self, socket, addr, emiter):
        super(ForwarderConnection, self).__init__(socket, addr)
        self.emiter = emiter
        print("New Client: %s:%d" % addr)

    def onRecv(self, data):
        fromHost, fromPort = self.addr
        toHost, toPort = self.emiter.addr
        print("Forwarding %s:%d -> %s:%d" % (fromHost, fromPort, toHost, toPort)
        self.emiter.send(data)

class ForwarderServer(Connection):
    def __init__(self, interface="eth0", listenerPort):
        self.socket = socket.socket(AF_PACKET, SOCK_RAW)
        self.addr = (interface, 0)
        super(ForwarderServer, self).__init__(socket, addr)
        self.socket.bind(self.addr)
        self.listener = socket.socket()
        self.listener.bind('', listenerPort)
        self.listener.listen(5)
        self.clientHandler = SocketAcceptor(listener, ForwarderConnection, self)
        self.clientHandler.start()

    def onRecv(self, data):
        for c in self.clientHandler.clients:
            fromHost, fromPort = self.addr
            toHost, toPort = self.emiter.addr
            print("Sending from %s:%d to %s:%d" % (fromHost, fromPort, toHost, toPort))
            c.send(data)

class ForwarderClient(Connection):
    def __init__(self, interface="eth0", hostname, port):
        self.socket = socket.socket(AF_PACKET, SOCK_RAW)
        self.addr = (interface, 0)
        super(ForwarderClient, self).__init__(socket, addr)
        self.socket.bind(self.addr)
        self.remoteAddr = (hostname, port)
        self.client = ForwarderConnection(connect(hostname, port), self.remoteAddr, self.socket)
        self.client.start()

    def onRecv(self, data):
        self.client.send(data)

if __name__ == '__main__':
    isServer = True
    if isServer:
        blackhole = ForwarderServer("eth0", 8080)
        blackhole.start()
        blackhole.join()
    else:
        blackhole = ForwarderClient("eth0", "localhost", 8080)
