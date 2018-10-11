#!/usr/bin/env python3

"""Basic script for extracting standalone fragments which might be suitable for
fuzzing in order to find allocation sequences.

Currently it does not support any kind of multi-statement code.
"""

import argparse
import itertools
import logging
import os

from collections import defaultdict

from shrike import php7

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument(
        'tests',
        help="The directory containing the source PHP tests")
parser.add_argument(
        '-o', '--output', required=True,
        help="The output file to which results will be logged")
parser.add_argument(
        '-p', '--php', required=True,
        help="The PHP binary to use")
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
logger.info("Processing tests from {}".format(args.tests))

fragments = php7.extract_fragments(args.tests, args.jobs)
tests = set(itertools.chain.from_iterable(fragments.values()))
logger.info("Extracting sequences from {} fragments".format(len(tests)))

interaction_sequences, err_fatal, err_os, err_sec, err_no_interaction = \
        php7.get_interaction_sequences(tests, args.jobs, args.php)

logger.info("{}/{} tests contained fatal errors".format(
    err_fatal, len(tests)))
logger.info("{}/{} tests triggered OS errors".format(
    err_os, len(tests)))
logger.info("{}/{} tests contained disabled functions".format(
    err_sec, len(tests)))
logger.info("{}/{} tests triggered no heap interaction".format(
    err_no_interaction, len(tests)))

uniq_sequences = defaultdict(set)
for fragment, sequence in interaction_sequences.items():
    logger.debug("{} => {}".format(fragment, sequence))
    uniq_sequences[sequence].add(fragment)

logger.info("{} unique allocator interaction sequences out of {} total".format(
    len(uniq_sequences), len(interaction_sequences)))

logger.info("Logging sequences to {}".format(args.output))
php7.dump_to_file(interaction_sequences, args.output)
