#!/usr/bin/env python3

"""Generate a set of fragments from str_replace and imagecreatetruecolor
"""

import argparse
import logging
import os

import heapfuzzlib

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument(
        '-p', '--php', required=True,
        help="The PHP binary to use")
parser.add_argument(
        '-o', '--output', default="controlled_fragments.pkl",
        help="Output file path")
parser.add_argument(
        '-j', '--jobs', type=int, default=os.cpu_count(),
        help="The number of concurrent jobs to run")
parser.add_argument(
        '--only-str-repeat', action='store_true', default=False,
        help="If provided then only use str_repeat")
parser.add_argument(
        '--debug', action='store_true', default=False,
        help="Enable debug mode (verbose logging)")
args = parser.parse_args()

if args.debug:
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    logging.basicConfig(level=logging.DEBUG)

logger.info("Utilising {} cores".format(args.jobs))
logger.info("Analysing the PHP binary at {}".format(args.php))

res = heapfuzzlib.php7.controlled_gen(
        args.jobs, args.php, args.only_str_repeat)
logger.info("{} new interaction sequence discovered".format(len(res)))
logger.info("Writing fuzzing results to {}".format(args.output))
heapfuzzlib.php7.dump_to_file(res, args.output)
