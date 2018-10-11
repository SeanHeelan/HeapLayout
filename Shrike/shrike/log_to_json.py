#!/usr/bin/env python3

import sys
import re

HEX_NUM = '0x([a-fA-F0-9]+)'
ALLOC_RE = re.compile('vtx alloc (\d+) {}'.format(HEX_NUM))
FREE_RE = re.compile('vtx free {}'.format(HEX_NUM))
REALLOC_RE = re.compile('vtx realloc (\d+) {} {}'.format(HEX_NUM, HEX_NUM))
DST_RE = re.compile('vtx dst (\d+) {}'.format(HEX_NUM))
SRC_RE = re.compile('vtx src (\d+) {}'.format(HEX_NUM))

def parse(fd):
    print('[')
    first = True
    for line in fd:
        line = line.strip()
        m = ALLOC_RE.match(line)
        if m:
            size = int(m.group(1))
            addr = int(m.group(2), 16)

            if first:
                first = False
            else:
                print(',\n', end='')

            print(('{{ "type" : "alloc", "tag" : "malloc", "size" : {}, '
                '"address" : {} }}').format(size, addr), end='')
            continue
        m = FREE_RE.match(line)
        if m:
            addr = int(m.group(1), 16)
            print((',\n{{ "type" : "free", "tag" : "free", '
                '"address" : {} }}').format(addr), end='')
            continue
        m = REALLOC_RE.match(line)
        if m:
            size = int(m.group(1))
            addr0 = int(m.group(2), 16)
            addr1 = int(m.group(3), 16)

            if first:
                first = False
            else:
                print(',\n', end='')

            print(('{{ "type" : "free", "tag" : "realloc", '
                '"address" : {} }}').format(addr0), end='')
            print((',\n{{ "type" : "alloc", "tag" : "realloc", "size" : {}, '
                '"address" : {} }}').format(size, addr1), end='')
            continue
        m = DST_RE.match(line)
        if m:
            size = int(m.group(1))
            addr = int(m.group(2), 16)
            if first:
                first = False
            else:
                print(',\n', end='')
            print('{ "type" : "event", "tag" : "dst" }', end='')
            continue
        m = SRC_RE.match(line)
        if m:
            size = int(m.group(1))
            addr = int(m.group(2), 16)
            if first:
                first = False
            else:
                print(',\n', end='')
            print('{ "type" : "event", "tag" : "src" }', end='')
            continue

        raise Exception("No match for line {}".format(line))

    print(']')


with open(sys.argv[1]) as fd:
    parse(fd)
