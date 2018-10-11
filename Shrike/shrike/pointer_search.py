#!/usr/bin/env python3

"""Search for code fragments that dynamically allocate structures containing
pointers.
"""

import argparse
import logging
import os
import sys

from shrike import php7

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument(
        'inputfiles', nargs='+',
        help=(
            'A list of pickle files mapping fragments to their summaries, '
            'or the result of a previous run of the script to dump'))
parser.add_argument(
        '-o', '--output',
        help="The output file to which results will be logged")
parser.add_argument(
        '-p', '--php',
        help="The PHP binary to use")
parser.add_argument(
        '-j', '--jobs', type=int, default=os.cpu_count(),
        help="The number of concurrent jobs to run")
parser.add_argument(
        '-d', '--dump', action='store_true', default=False,
        help="If provided, then dump the pointer info from a previous run")
parser.add_argument(
        '--pointer-offset', type=int, default=None,
        help=(
            "Dump full pointer records for sequences which have a pointer"
            "at this offset"))
parser.add_argument(
        '-f', '--fragment-id', type=int, default=0,
        help="The ID of the fragment on which to dump more details")
parser.add_argument(
        '--debug', action='store_true', default=False,
        help="Enable debug mode (verbose logging)")
args = parser.parse_args()

if args.debug:
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    logging.basicConfig(level=logging.DEBUG)

if not args.dump and (not args.php or not args.output):
    logger.error("You must specify a PHP binary and output directory")
    parser.print_help()
    sys.exit(-1)

if args.dump:
    pointer_offset = args.pointer_offset
    pointer_data = php7.load_from_files(args.inputfiles)
    s = reversed(sorted(pointer_data.items(), key=lambda t: len(t[1])))
    fid = 1
    for fragment, ptr_records in s:
        if not args.fragment_id:
            logger.info("FID: {}, Pointer Count: {} <= {}".format(
                fid, len(ptr_records), fragment))
            if pointer_offset is None:
                continue

            found = False
            for record in ptr_records:
                if record.offset_in_container == pointer_offset:
                    found = True

            if found:
                for record in ptr_records:
                    print((
                        "\tSize of allocation: {}, Offset of pointer: {}, "
                        "Pointer: 0x{:x}").format(
                            record.allocation_size,
                            record.offset_in_container,
                            record.pointer))
        elif args.fragment_id == fid:
            logger.info("FID: {}, Pointer Count: {} <= {}".format(
                fid, len(ptr_records), fragment))
            for record in ptr_records:
                print(
                        ("\tSize of allocation: {}, Offset of pointer: {}, "
                            "Pointer: 0x{:x}").format(
                                record.allocation_size,
                                record.offset_in_container,
                                record.pointer))
        fid += 1
    logger.info("{} fragments allocate pointers".format(fid - 1))
    sys.exit(0)

logger.info("Utilising {} cores".format(args.jobs))
logger.info("Analysing the PHP binary at {}".format(args.php))

fragment_data = php7.load_from_files(args.inputfiles)
fragments = fragment_data.keys()
logger.info("Loaded {} fragments".format(len(fragments)))
result, err_fatal, err_os, err_sec, err_no_pointers = \
        php7.pointer_search(fragments, args.jobs, args.php)

s = reversed(sorted(result.items(), key=lambda t: len(t[1])))
for fragment, ptr_count in s:
    logger.debug("{} <= {}".format(ptr_count, fragment))

logger.info("{} fatal errors".format(err_fatal))
logger.info("{} os errors".format(err_os))
logger.info("{} security errors".format(err_sec))
logger.info("{} fragments did not allocate pointers".format(err_no_pointers))
logger.info("{} fragments allocated pointers".format(len(result)))

logger.info("Saving results to {}".format(args.output))
php7.dump_to_file(result, args.output)
