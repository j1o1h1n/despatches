import os
import mmap

from multiprocessing.connection import Client
from multiprocessing.reduction import recv_handle
from socket import socket, AF_INET, SOCK_STREAM

def worker(server_address):
    serv = Client(server_address, authkey=b'peekaboo')
    serv.send(os.getpid())

    fd = recv_handle(serv)

    msg_bytes = mmap.mmap(fd, 1024, flags=mmap.MAP_PRIVATE, prot=mmap.PROT_READ)
    idx = msg_bytes.find(b'\0')
    print("Message: %s\n" % (msg_bytes[:idx].decode("utf8")));

if __name__ == '__main__':
    import sys
    if len(sys.argv) != 2:
        print('Usage: worker.py server_address', file=sys.stderr)
        raise SystemExit(1)

    worker(sys.argv[1])
