#!/usr/bin/env python3

import argparse
import jsonpickle
import logging
import multiprocessing
import os
import pathlib
import subprocess
import sys
import time

from typing import List

from heapexp import executor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_test(output_dir_prefix: pathlib.Path, output_dir_suffix: str,
        interaction_sequences: str, starting_state: str, allocator: str,
        first: int, second: int, jobs: int):
    execution_limit = 500_000
    time_limit = 3600

    if allocator == 'avrlibc-r2537':
        cut_off = 8
        if first == 0:
            first = 8
        if second == 0:
            second = 8
    else:
        cut_off = 16
        if first == 0:
            first = 32
        if second == 0:
            second = 32

    output_path = (output_dir_prefix /
                   pathlib.Path("{}_results{}".format(
                       interaction_sequences, output_dir_suffix)) /
                   pathlib.Path("{}-{}-{}-{}-{}".format(
                           starting_state, allocator,
                           interaction_sequences,
                           first, second)))
    logger.info("Running {}".format(output_path))

    start_time = time.time()
    try:
        p = subprocess.run(
                ["./runexp.py",
                 "-f", str(first),
                 "-s", str(second),
                 "-j", str(jobs),
                 "--allocator", allocator,
                 "--starting-state", starting_state,
                 "--interaction-sequences", interaction_sequences,
                 "--output", output_path.as_posix(),
                 "--time-limit", str(time_limit),
                 "--execution-limit", str(execution_limit),
                 "--cutoff", str(cut_off)],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                timeout=time_limit * 2)
        if p.returncode:
            logger.error("{} non-zero return code".format(output_path))
            logger.error("{}".format(p.stdout))
            logger.error("{}".format(p.stderr))
        else:
            logger.info("{} finished, run time: {}".format(
                    output_path, int(time.time() - start_time)))
    except subprocess.TimeoutExpired:
        logger.error("{} timeout expired")
    except OSError:
        logger.error("{} OS error")


def start(output_dir_prefix: pathlib.Path, output_dir_suffix: str,
        interaction_sequences: str):
    src_dst_sizes = [0, 64, 512, 4096, 16384, 65536]
    allocators = ['avrlibc-r2537', 'dlmalloc-2.8.6', 'tcmalloc-2.6.1']
    starting_states = [
        'php-emalloc', 'php-malloc', 'ruby-malloc', 'python-malloc']
    processes = 1
    jobs = os.cpu_count() // 2

    logger.info("Running with {} processes and {} jobs per process".format(
            processes, jobs))
    with multiprocessing.Pool(processes=processes) as pool:
        for starting_state in starting_states:
            for allocator in allocators:
                for first in src_dst_sizes:
                    for second in src_dst_sizes:
                        pool.apply_async(
                                run_test,
                                (output_dir_prefix, output_dir_suffix,
                                 interaction_sequences, starting_state,
                                 allocator, first,
                                 second,
                                 jobs))

        pool.close()
        pool.join()


def get_unsuccessful_configurations(
        path: pathlib.Path) -> List[executor.ExpResult]:
    unsuccessful_results = []

    errors = 0
    for subdir in path.iterdir():
        logger.debug("Processing {} ...".format(subdir.name))
        result_json = subdir / "result.json"
        if not result_json.exists():
            logger.error(
                    "The results file {} does not exist".format(result_json))
            errors += 1
            continue

        with open(result_json.as_posix()) as fd:
            data = fd.read()

        exp_res: executor.ExpResult = jsonpickle.decode(data)
        if (exp_res.min_neg_dist and exp_res.min_pos_dist and
                    abs(exp_res.min_neg_dist) <= exp_res.cutoff and
                    exp_res.min_pos_dist <= exp_res.cutoff):
            continue
        unsuccessful_results.append(exp_res)

    return unsuccessful_results


def rerun(config: executor.ExpResult, output_parent: pathlib.Path):
    output_path = (output_parent /
                   pathlib.Path("{}-{}-{}-{}-{}".format(
                           config.starting_state, config.allocator,
                           config.interaction_sequences,
                           config.first_size, config.second_size)))
    logger.info("Running {}".format(output_path))

    start_time = time.time()
    args = [
        "./runexp.py",
        "-f", str(config.first_size),
        "-s", str(config.second_size),
        "-j", str(config.jobs),
        "--allocator", config.allocator,
        "--starting-state", config.starting_state,
        "--interaction-sequences", config.interaction_sequences,
        "--output", output_path.as_posix(),
        "--cutoff", str(config.cutoff)]

    if config.time_limit:
        args.append("--time-limit")
        args.append(str(config.time_limit))
        timeout = config.time_limit * 2
    else:
        timeout = None

    if config.execution_limit:
        args.append("--execution-limit")
        args.append(str(config.execution_limit))

    try:
        p = subprocess.run(
                args,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                timeout=timeout)
        if p.returncode:
            logger.error("{} non-zero return code".format(output_path))
            logger.error("{}".format(p.stdout))
            logger.error("{}".format(p.stderr))
        else:
            logger.info("{} finished, run time: {}".format(
                    output_path, int(time.time() - start_time)))
    except subprocess.TimeoutExpired:
        logger.error("{} timeout expired")
    except OSError:
        logger.error("{} OS error")


def main():
    parser = argparse.ArgumentParser(
            formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--interaction-sequences")
    parser.add_argument(
            '--rerun',
            help=("A directory containing results, from which the unsuccessful"
                  "runs will be ran again"))
    parser.add_argument(
            '--output-dir-prefix', type=str, default='.',
            help="The directory into which to write the results")
    parser.add_argument(
            '--output-dir-suffix', type=str, default='',
            help="A suffix to append to the output directory name")

    args = parser.parse_args()
    if not args.rerun:
        if not args.interaction_sequences:
            logger.error("Interaction sequences must be specified")
            sys.exit(1)
        start(pathlib.Path(args.output_dir_prefix), args.output_dir_suffix,
                args.interaction_sequences)
        sys.exit(0)

    path = pathlib.Path(args.rerun)
    if not path.exists() or not path.is_dir():
        logger.error("{} is not a valid directory".format(path.as_posix()))
        sys.exit(1)

    logger.info("Rerunning experiments from {}".format(args.rerun))

    output_dir = pathlib.Path(path.parent / (path.name + "_rerun"))
    if output_dir.exists():
        logger.error("Directory {} already exists".format(output_dir))
        sys.exit(1)

    os.mkdir(output_dir.as_posix())
    logger.info("Results will be saved in {}".format(output_dir.as_posix()))

    configs = get_unsuccessful_configurations(path)
    logger.info("{} experiments to rerun".format(len(configs)))

    for c in configs:
        rerun(c, output_dir)


if __name__ == '__main__':
    main()
