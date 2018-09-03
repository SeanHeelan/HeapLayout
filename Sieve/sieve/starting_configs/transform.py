#!/usr/bin/env python3

import sys

EXPECTING_MALLOC_END = 1
EXPECTING_REALLOC_END = 2
EXPECTING_CALLOC_END = 3
EXPECTING_ANY = 4


def parse(fd):
    state = EXPECTING_ANY
    ln = 0

    for line in fd:
        ln += 1

        line = line.strip()
        if not line.startswith("vtx "):
            continue

        if line.startswith("vtx malloc start"):
            if (state == EXPECTING_REALLOC_END or
                    state == EXPECTING_CALLOC_END):
                continue

            if state != EXPECTING_ANY:
                print("Invalid state {} for malloc start on line {}".format(
                    state, ln))
                sys.exit(-1)

            spl = line.split()
            sz = int(spl[3])
            state = EXPECTING_MALLOC_END
        elif line.startswith("vtx malloc end"):
            if (state == EXPECTING_REALLOC_END or
                    state == EXPECTING_CALLOC_END):
                continue

            if state != EXPECTING_MALLOC_END:
                print("Invalid state {} for malloc end on line {}".format(
                    state, ln))
                sys.exit(-1)

            spl = line.split()
            addr = int(spl[3])
            state = EXPECTING_ANY

            print("vtx alloc {} 0x{:x}".format(sz, addr))
            sz = addr = None
        elif line.startswith("vtx realloc start"):
            if state != EXPECTING_ANY:
                print("Invalid state {} for realloc start on line {}".format(
                    state, ln))
                sys.exit(-1)

            spl = line.split()
            old_addr = int(spl[3])
            sz = int(spl[4])
            state = EXPECTING_REALLOC_END
        elif line.startswith("vtx realloc end"):
            if state != EXPECTING_REALLOC_END:
                print("Invalid state {} for realloc end on line {}".format(
                    state, ln))
                sys.exit(-1)

            spl = line.split()
            new_addr = int(spl[3])
            state = EXPECTING_ANY

            print("vtx realloc {} 0x{:x} 0x{:x}".format(
                sz, old_addr, new_addr))
            sz = old_addr = new_addr = None
        elif line.startswith("vtx free"):
            if state != EXPECTING_ANY:
                print("Invalid state {} for free on line {}".format(
                    state, ln))
                sys.exit(-1)

            spl = line.split()
            addr = int(spl[2])
            state = EXPECTING_ANY

            if addr == 0:
                addr = None
                continue
            print("vtx free 0x{:x}".format(addr))
            addr = None
        elif line.startswith("vtx calloc start"):
            if state != EXPECTING_ANY:
                print("Invalid state {} for calloc start on line {}".format(
                    state, ln))
                sys.exit(-1)

            spl = line.split()
            nmemb = int(spl[3])
            sz = int(spl[4])
            state = EXPECTING_CALLOC_END
        elif line.startswith("vtx calloc end"):
            if state != EXPECTING_CALLOC_END:
                print("Invalid state {} for calloc end on line {}".format(
                    state, ln))
                sys.exit(-1)

            spl = line.split()
            addr = int(spl[3])
            print("vtx calloc {} {} 0x{:x}".format(nmemb, sz, addr))
            state = EXPECTING_ANY
            sz = nmemb = None


with open(sys.argv[1]) as fd:
    parse(fd)
