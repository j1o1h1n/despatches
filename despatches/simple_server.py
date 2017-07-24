"""
Example memfd_create(2) server application.
"""
import sys
import os
import mmap
import socket
import struct
import time
import ctypes
import fcntl
import platform

machine = platform.machine()
__NR_memfd_create = 356
if machine == 'x86_64':
    __NR_memfd_create = 319
elif machine == '__i386__':
    __NR_memfd_create = 356
elif machine == 'armv7l':
    __NR_memfd_create = 385

MFD_CLOEXEC       = 0x0001
MFD_ALLOW_SEALING = 0x0002

F_LINUX_SPECIFIC_BASE = 1024
F_ADD_SEALS = F_LINUX_SPECIFIC_BASE + 9
F_GET_SEALS = F_LINUX_SPECIFIC_BASE + 10
F_SEAL_SEAL     = 0x0001  # prevent further seals from being set
F_SEAL_SHRINK   = 0x0002  # prevent file from shrinking
F_SEAL_GROW     = 0x0004  # prevent file from growing
F_SEAL_WRITE    = 0x0008  # prevent writes

LOCAL_SOCKET_NAME = "./unix_socket"
MAX_CONNECT_BACKLOG = 128


def memfd_create(name, flags):
    # int memfd_create(const char *name, unsigned int flags)
    syscall = ctypes.CDLL(None).syscall
    fd = syscall(385, name.encode("ascii"), flags)
    if fd == -1:
        raise OSError('memfd_create')
    return fd

def new_memfd_region(msg):
    shm_size = 1024
    fd = memfd_create("Server memfd", MFD_ALLOW_SEALING)
    os.truncate(fd, shm_size)
    fcntl.fcntl(fd, F_ADD_SEALS, F_SEAL_SHRINK)
    shm = mmap.mmap(fd, shm_size, flags=mmap.MAP_SHARED,
                    prot=(mmap.MAP_SHARED | mmap.PROT_WRITE))
    shm[:len(msg)] = msg.encode("ascii")
    shm.close()

    fcntl.fcntl(fd, F_ADD_SEALS, F_SEAL_WRITE)
    fcntl.fcntl(fd, F_ADD_SEALS, F_SEAL_SEAL);

    return fd


def send_fd(connection, fd):
    '''
    Send a single file descriptor.
    '''
    connection.sendmsg([b'x'],
                       [(socket.SOL_SOCKET, socket.SCM_RIGHTS,
                        struct.pack('i', fd))])


def main():
    """ start server and send memfd to clients """
     # Make sure the socket does not already exist
    try:
        os.unlink(LOCAL_SOCKET_NAME)
    except OSError:
        if os.path.exists(LOCAL_SOCKET_NAME):
            raise

    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.bind(LOCAL_SOCKET_NAME)
    sock.listen(MAX_CONNECT_BACKLOG)

    while True:
        print('waiting for a connection')

        connection, client_address = sock.accept()
        print('connection from', client_address)

        msg = "Secure zero-copy message from server: %s" % (time.ctime())
        fd = new_memfd_region(msg)

        send_fd(connection, fd)
        # TODO close(fd), connection.close()

if __name__ == "__main__":
    main()

