#!/usr/bin/env python3

"""Fuzz a given set of fragments to discover new interaction sequences.

Currently fuzzing consists of manipulating string lengths and integer values.
"""

import argparse
import logging
import os
import pathlib

from shrike import FragmentStore
from shrike import php7

OUT_PREFIX = 'fuzzed_'
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument(
        'fragments',
        help=(
            "The pickle file containing the fragments to fuzz. The result"
            "will be stored in a file with the name fuzzed_NAME.pkl"))
parser.add_argument(
        '-p', '--php', required=True,
        help="The PHP binary to use")
parser.add_argument(
        '-t', '--time-limit', type=int, default=60,
        help="The amount of time to fuzz for")
parser.add_argument(
        '-j', '--jobs', type=int, default=os.cpu_count(),
        help="The number of concurrent jobs to run")
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

fragment_path = pathlib.Path(args.fragments)
fragment_store = FragmentStore(fragment_path)
logger.info("{} unique sequences across {} fragments loaded from {}".format(
    fragment_store.num_sequences(), fragment_store.num_fragments(),
    fragment_path))

res = php7.fuzz(fragment_store, args.jobs, args.php, args.time_limit)
logger.info("{} new interaction sequence discovered".format(len(res)))
out_path = fragment_path.with_name(OUT_PREFIX + fragment_path.name)
logger.info("Writing fuzzing results to {}".format(out_path))
php7.dump_to_file(res, out_path.as_posix())
