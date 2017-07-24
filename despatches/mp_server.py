"""
Server class that waits for a client connection, then sends a message over an
memfd file descriptor using the multiprocessing send_handle method.
"""
import time
import socket
from multiprocessing.connection import Listener
from multiprocessing.reduction import send_handle

import memfd

def server(work_address):
    # Wait for the worker to connect
    work_serv = Listener(work_address, authkey=b'peekaboo')

    while True:
        worker = work_serv.accept()
        worker_pid = worker.recv()
        print('SERVER: Got connection')

        msg = "Secure zero-copy こんにちわ from server: %s" % (time.ctime())
        msg_bytes = msg.encode("utf8")
        fd = memfd.new_memfd_region(msg_bytes)

        send_handle(worker, fd, worker_pid)
        worker.close()

if __name__ == '__main__':
    import sys
    if len(sys.argv) != 2:
        print('Usage: server.py server_address', file=sys.stderr)
        raise SystemExit(1)

    server(sys.argv[1])
