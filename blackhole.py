import threading
import socket

MTU = 4096

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

    def stop(self):
        self.interrupted = True

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
            client = self.clientClass(c, addr, self.emiter)
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
        print("Forwarding %s:%d -> %s:%d" % (fromHost, fromPort, toHost, toPort))
        print("Packet: (%d)" % (len(data)))
        self.emiter.send(data)

class ForwarderServer(Connection):
    def __init__(self, interface, listenerPort):
        self.socket = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.htons(3))
        self.addr = (interface, 0)
        super(ForwarderServer, self).__init__(self.socket, self.addr)
        self.socket.bind(self.addr)
        self.listener = socket.socket()
        self.listener.bind(('', listenerPort))
        self.listener.listen(5)
        self.clientHandler = SocketAcceptor(self.listener, ForwarderConnection, self)
        self.clientHandler.start()

    def onRecv(self, data):
        for c in self.clientHandler.clients:
            fromHost, fromPort = self.addr
            toHost, toPort = c.addr
            print("Broadcast from %s:%d to %s:%d" % (fromHost, fromPort, toHost, toPort))
            print("Packet: (%d)" %(len(data)))
            c.send(data)

    def stop(self):
        self.clientHander.stop()
        super(ForwarderServer, self).stop()

class ForwarderClient(Connection):
    def __init__(self, interface, hostname, port):
        self.socket = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.htons(3))
        self.addr = (interface, 0)
        super(ForwarderClient, self).__init__(self.socket, self.addr)
        self.socket.bind(self.addr)
        self.remoteAddr = (hostname, port)
        self.remoteSocket = socket.socket()
        self.remoteSocket.connect(self.remoteAddr)
        self.client = ForwarderConnection(self.remoteSocket, self.remoteAddr, self)
        self.client.start()

    def onRecv(self, data):
        fromHost, fromPort = self.addr
        toHost, toPort = self.remoteAddr
        print("Broadcast from %s:%d to %s:%d" %(fromHost, fromPort, toHost, toPort))
        print("Packet: (%d)" % (len(data)))
        self.client.send(data)

    def stop(self):
        self.client.stop()
        super(ForwarderClient, self).stop()

if __name__ == '__main__':
    import argparse
    import sys
    import signal

    parser = argparse.ArgumentParser(description="Blackhole PVPN")
    parser.add_argument('--interface', required=True, help='interface wich will be tunneled')
    parser.add_argument('--connect', help='connect to a blackholeServer')
    parser.add_argument('--server', action='store_const', const=True, help='start a blackholeServer')
    parser.add_argument('--port', type=int, default=8080, help='tcp port')

    args = parser.parse_args()
    if not(args.connect) and not(args.server):
        print("nothing to do.")
        sys.exit(-1)

    interface = args.interface
    port = args.port

    blackhole = None
    if(args.server):
        print("Server tunneling if:%s hosting on port: %d" %(interface, port))
        blackhole = ForwarderServer(interface, port)
    else:
        hostname=args.connect
        print("Client tunneling if:%s connectiong to %s:%d" % (interface, hostname, port))
        blackhole = ForwarderClient(interface, hostname, port)

    blackhole.start()

    def signal_handler(sig, frame):
        print("Stopping blackhole")
        blackhole.stop()
    sys.exit(0)
