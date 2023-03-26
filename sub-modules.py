# !/usr/bin/env python

from socket import AF_INET, SOCK_DGRAM

import socket

import struct, time


def getNTPTime(host, gmt):
    port = 123

    buf = 1024

    address = (host, port)

    msg = '\x1b' + 47 * '\0'

    # reference time (in seconds since 1900-01-01 00:00:00)

    TIME1970 = 2208992400 - (3600*gmt)  # 1970-01-01 00:00:00

    # connect to server

    client = socket.socket(AF_INET, SOCK_DGRAM)

    client.sendto(msg.encode('utf-8'), address)

    msg, address = client.recvfrom(buf)

    t = struct.unpack("!12I", msg)[10]

    t -= TIME1970

    return time.ctime(t).replace("  ", " ")
