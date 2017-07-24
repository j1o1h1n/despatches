"""
Example memfd_create(2) client application.
"""
import mmap
import socket
import struct

LOCAL_SOCKET_NAME = "./unix_socket"

def recv_fd(sock):
    '''
    Receive a single file descriptor
    '''
    msg, ancdata, flags, addr = sock.recvmsg(1,
                                     socket.CMSG_LEN(struct.calcsize('i')))

    cmsg_level, cmsg_type, cmsg_data = ancdata[0]
    assert cmsg_level == socket.SOL_SOCKET and cmsg_type == socket.SCM_RIGHTS
    return struct.unpack('i', cmsg_data)[0]

def connect_to_server_and_get_memfd_fd():
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.connect(LOCAL_SOCKET_NAME)
    return recv_fd(sock)

def main():
    shm_size = 1024
    fd = connect_to_server_and_get_memfd_fd()
    shm = mmap.mmap(fd, shm_size, flags=mmap.MAP_PRIVATE, prot=mmap.PROT_READ)
    idx = shm.find(b'\0')
    print("Message: %s\n" % (shm[:idx]));

if __name__ == "__main__":
    main()
