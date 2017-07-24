"""
Expose the memfd create method.
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

syscall = ctypes.CDLL(None).syscall


def memfd_create(name, flags):
    " call memfd create with the given name and flags "
    if isinstance(name, str):
        name = name.encode("ascii")
    # int memfd_create(const char *name, unsigned int flags)
    fd = syscall(385, name, flags)
    if fd == -1:
        raise OSError('memfd_create')
    return fd


def new_memfd_region(msg_bytes, name="memfd_handle", region_size=1024):
    " create an memfd handle for the given message and seal it "
    fd = memfd_create(name, MFD_ALLOW_SEALING)

    os.truncate(fd, region_size)
    fcntl.fcntl(fd, F_ADD_SEALS, F_SEAL_SHRINK)

    shm = mmap.mmap(fd, region_size, flags=mmap.MAP_SHARED,
                    prot=(mmap.MAP_SHARED | mmap.PROT_WRITE))
    shm[:len(msg_bytes)] = msg_bytes
    shm.close()

    # seal memfd from further changs
    fcntl.fcntl(fd, F_ADD_SEALS, F_SEAL_WRITE)
    fcntl.fcntl(fd, F_ADD_SEALS, F_SEAL_SEAL);

    return fd
