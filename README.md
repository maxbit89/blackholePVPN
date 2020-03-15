# blackholePVPN
Partial VPN

Blackhole enables you to tunnel raw Ethernet through a socket connection.

Normal Ethernet Cable:
+---------+                                   +--------+
| Switch  | <---------- Cable --------------> | Switch |
+---------+                                   +--------+


Blackhole:         
+--------+         +----------------------------+                      +----------------------------+         +--------+
| Switch | <-----> | eth0 Blackhole Server eth1 | <---- Internet ----> | eth1 Blackhole Client eth0 | <-----> | Switch |
+--------+         +----------------------------+                      +----------------------------+         +--------+


eth0 is configured without an ip or other layer 3 protocol. (Only Layer 2 should be configured)
eth1 is configured to enable normal tcp ip traffik.

With blackhole the network is tunneled through a TCP Ip connection to share a network over the Internet.
