#!/usr/bin/env python3

"""Script for running all of the experiments for the standalone evaluation"""

import argparse
import jsonpickle
import os
import pathlib
import sys
import time

from heapexp import logutils, startgen, interactiongen, executor, drivers

parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument(
        '-j', '--jobs', type=int, default=os.cpu_count(),
        help="The number of concurrent jobs to run")
parser.add_argument(
        '-o', '--output-dir',
        help=(
            "The directory to write the results directory to. Must "
            "already exist"))
parser.add_argument(
        '-t', '--time-limit', type=int, default=None,
        help="The time to run the experiment for")
parser.add_argument(
        '-e', '--execution-limit', type=int, default=None)
parser.add_argument(
        '-f', '--first-size', type=int, required=True,
        help="The size of the first type to allocate")
parser.add_argument(
        '-s', '--second-size', type=int, required=True,
        help="The size of the second type to allocate")
parser.add_argument(
        '-c', '--cutoff', type=int, default=4,
        help=(
            "A lower bound for the search, which when reached for both the"
            "positive and negative distance will result in the search ending"))
parser.add_argument(
        '--debug', action='store_true', default=False,
        help="Enable debug logging")
parser.add_argument(
        '--starting-state', required=True,
        choices=['random', 'php-malloc', 'php-emalloc', 'python-malloc',
                 'ruby-malloc', 'default'],
        help="The starting state into which the allocator will be initialised")
parser.add_argument(
        '--interaction-sequences', required=True,
        choices=['random', 'php_str_repeat', 'synth_no_noise_small',
                 'first_second_sizes_no_noise', 'adjusting_fsnn',
                 'sl1024afr55', 'sl256afr98', 'sl8192afr100', 'sl1024afr98',
                 'g1sl1024afr98', 'g4sl1024afr98', 'g16sl1024afr98',
                 'hsg4sl1024afr98'],
        help="The allocator interaction sequences to make available")
parser.add_argument(
        '--allocator', required=True,
        choices=['avrlibc-r2537', 'dlmalloc-2.8.6', 'jemalloc-5.0.1',
                 'tcmalloc-2.6.1', 'default'],
        help="The allocator to use")

args = parser.parse_args()

if not args.output_dir:
    result_path = pathlib.Path('/tmp') / pathlib.Path(
            'expres-' + time.strftime('%Y-%m-%d-%H-%M-%S'))
    os.mkdir(result_path.as_posix())
else:
    result_path = pathlib.Path(args.output_dir)
    os.mkdir(result_path.as_posix())

logutils.configure_logger(result_path, args.debug)
logger = logutils.get_logger()

logger.info("Testing the {} allocator".format(args.allocator))
if args.allocator == 'jemalloc-5.0.1':
    driver = drivers.get_jemalloc_5_0_1()
elif args.allocator == 'dlmalloc-2.8.6':
    driver = drivers.get_dlmalloc_2_8_6()
elif args.allocator == 'tcmalloc-2.6.1':
    driver = drivers.get_tcmalloc_2_6_1()
elif args.allocator == 'avrlibc-r2537':
    driver = drivers.get_avrlibc_r2537()
elif args.allocator == 'default':
    driver = drivers.get_default()
else:
    logger.error("Unhandled allocator {}".format(args.allocator))
    sys.exit(1)

if args.starting_state == 'random':
    starting_config = startgen.get_random()
    logger.info("Utilising a random starting state ({} events)".format(
            len(starting_config)))
elif args.starting_state == 'php-malloc':
    starting_config = startgen.get_php_malloc()
    logger.info("Utilising PHP's malloc starting state ({} events)".format(
            len(starting_config)))
elif args.starting_state == 'php-emalloc':
    starting_config = startgen.get_php_emalloc()
    logger.info("Utilising PHP's emalloc starting state ({} events)".format(
            len(starting_config)))
elif args.starting_state == 'ruby-malloc':
    starting_config = startgen.get_ruby_malloc()
    logger.info("Utilising Ruby's malloc starting state ({} events)".format(
            len(starting_config)))
elif args.starting_state == 'python-malloc':
    starting_config = startgen.get_python_malloc()
    logger.info("Utilising Python's malloc starting state ({} events)".format(
            len(starting_config)))
elif args.starting_state == 'default':
    logger.info("Utilising a default starting state")
    starting_config = startgen.get_default()
else:
    logger.error("Unhandled starting state configuration: {}".format(
            args.starting_state))
    sys.exit(1)

if args.interaction_sequences == 'php_str_repeat':
    logger.info("Using PHP str_repeat interaction sequences")
    interaction_generator = interactiongen.get_php_str_repeat_generator(
            args.first_size, args.second_size)
elif args.interaction_sequences == 'synth_no_noise_small':
    interaction_generator = interactiongen.get_synth_no_noise_small(
            args.first_size, args.second_size)
elif args.interaction_sequences == 'first_second_sizes_no_noise':
    interaction_generator = interactiongen.get_first_second_sizes_no_noise(
            args.first_size, args.second_size)
elif args.interaction_sequences == 'adjusting_fsnn':
    interaction_generator = interactiongen.get_adjusting_fsnn(
            args.time_limit, args.first_size, args.second_size)
elif args.interaction_sequences == 'sl1024afr55':
    interaction_generator = interactiongen.get_sl1024afr55(
            args.first_size, args.second_size)
elif args.interaction_sequences == 'sl256afr98':
    interaction_generator = interactiongen.get_sl256afr98(
            args.first_size, args.second_size)
elif args.interaction_sequences == 'sl8192afr100':
    interaction_generator = interactiongen.get_sl8192afr100(
            args.first_size, args.second_size)
elif args.interaction_sequences == 'sl1024afr98':
    interaction_generator = interactiongen.get_sl1024afr98(
            args.first_size, args.second_size)
elif args.interaction_sequences == 'g1sl1024afr98':
    interaction_generator = interactiongen.get_g1sl1024afr98(
            args.first_size, args.second_size)
elif args.interaction_sequences == 'g4sl1024afr98':
    interaction_generator = interactiongen.get_g4sl1024afr98(
            args.first_size, args.second_size)
elif args.interaction_sequences == 'g16sl1024afr98':
    interaction_generator = interactiongen.get_g16sl1024afr98(
            args.first_size, args.second_size)
elif args.interaction_sequences == 'hsg4sl1024afr98':
    interaction_generator = interactiongen.get_hsg4sl1024afr98(
            args.first_size, args.second_size)
else:
    logger.error("Unhandle sequence generator: {}".format(
            args.interaction_sequences))
    sys.exit(1)

logger.info((
    "Running experiment on {} cores (time limit: {}, execution limit: {}, "
    "cutoff: {})").format(
        args.jobs, args.time_limit, args.execution_limit, args.cutoff))

res = executor.ExpResult(args)
executor.run_experiment(
        res, driver, interaction_generator, starting_config, result_path,
        args.jobs, args.time_limit, args.execution_limit, args.cutoff)

logger.info("Min. negative distance: {}".format(res.min_neg_dist))
logger.info("Min. positive distance: {}".format(res.min_pos_dist))

json_log_path = result_path / "result.json"
with open(json_log_path.as_posix(), 'w') as fd:
    fd.write(jsonpickle.encode(res))
