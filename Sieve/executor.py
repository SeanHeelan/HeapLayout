import multiprocessing
import os
import pathlib
import queue
import shutil
import subprocess
import time
import uuid

from typing import List, Tuple, Optional

from heapexp import logutils, interactiongen

ERR_OS = 1
ERR_TIMEOUT = 2
ERR_EXEC = 3


class ExpResult:
    """An object containing the configuration parameters for a single
    experiment, as well as the results of that experiment.
    """

    def __init__(self, args):
        self._allocator = args.allocator
        self._starting_state = args.starting_state
        self._interaction_sequences = args.interaction_sequences
        self._time_limit = args.time_limit
        self._exec_limit = args.execution_limit
        self._distance_cutoff = args.cutoff
        self._jobs = args.jobs
        self._first_size = args.first_size
        self._second_size = args.second_size

        self._min_neg_dist = None
        self._min_pos_dist = None

        self._execs_to_neg_result = 0
        self._execs_to_pos_result = 0
        self._time_to_neg_result = 0
        self._time_to_pos_result = 0

        self._total_time = 0
        self._total_execs = 0

    @property
    def allocator(self):
        return self._allocator

    @property
    def starting_state(self):
        return self._starting_state

    @property
    def interaction_sequences(self):
        return self._interaction_sequences

    @property
    def cutoff(self):
        return self._distance_cutoff

    @property
    def first_size(self):
        return self._first_size

    @property
    def second_size(self):
        return self._second_size

    @property
    def min_neg_dist(self):
        return self._min_neg_dist

    @min_neg_dist.setter
    def min_neg_dist(self, v):
        self._min_neg_dist = v

    @property
    def min_pos_dist(self):
        return self._min_pos_dist

    @min_pos_dist.setter
    def min_pos_dist(self, v):
        self._min_pos_dist = v

    @property
    def execs_to_neg_result(self):
        return self._execs_to_neg_result

    @execs_to_neg_result.setter
    def execs_to_neg_result(self, v):
        self._execs_to_neg_result = v

    @property
    def execs_to_pos_result(self):
        return self._execs_to_pos_result

    @execs_to_pos_result.setter
    def execs_to_pos_result(self, v):
        self._execs_to_pos_result = v

    @property
    def time_to_neg_result(self):
        return self._time_to_neg_result

    @time_to_neg_result.setter
    def time_to_neg_result(self, v):
        self._time_to_neg_result = v

    @property
    def time_to_pos_result(self):
        return self._time_to_pos_result

    @time_to_pos_result.setter
    def time_to_pos_result(self, v):
        self._time_to_pos_result = v

    @property
    def total_time(self):
        return self._total_time

    @total_time.setter
    def total_time(self, v):
        self._total_time = v

    @property
    def total_execs(self):
        return self._total_execs

    @total_execs.setter
    def total_execs(self, v):
        self._total_execs = v

    @property
    def jobs(self):
        return self._jobs

    @property
    def time_limit(self):
        return self._time_limit

    @property
    def execution_limit(self):
        return self._exec_limit

    def record_neg_result(self, dist, time_to_result, execs):
        self.min_neg_dist = dist
        self.time_to_neg_result = time_to_result
        self.execs_to_neg_result = execs

    def record_pos_result(self, dist, time_to_result, execs):
        self.min_pos_dist = dist
        self.time_to_pos_result = time_to_result
        self.execs_to_pos_result = execs


def _exec_interactions(runner: pathlib.Path,
                       interaction_file: pathlib.Path) -> Tuple[int, bytes]:
    p = subprocess.run(
            [runner.as_posix(), interaction_file.as_posix()],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            timeout=5)

    return p.returncode, p.stdout


def _create_interaction_file(
        starting_config_path: pathlib.Path,
        interactions: List[str]) -> pathlib.Path:
    interaction_file = pathlib.Path("/tmp") / str(uuid.uuid4())
    shutil.copy(starting_config_path.as_posix(), interaction_file.as_posix())

    with open(interaction_file, 'a') as fd:
        fd.write("\n")
        for x in interactions:
            fd.write(x + "\n")

    return interaction_file


def _run_instance(
        runner: pathlib.Path, starting_config_path: pathlib.Path,
        interactions: List[str]) -> Tuple[Optional[int], Optional[int]]:
    interaction_file = _create_interaction_file(
            starting_config_path, interactions)
    try:
        retcode, stdout = _exec_interactions(runner, interaction_file)
    except OSError:
        return None, ERR_OS
    except subprocess.TimeoutExpired:
        return None, ERR_TIMEOUT

    if retcode:
        return None, ERR_EXEC

    output = stdout.decode().splitlines()
    for o in output:
        if o.startswith("vtx distance"):
            spl = o.split(" ")
            distance = int(spl[2])
            os.remove(interaction_file.as_posix())
            return distance, None

    return None, ERR_EXEC


def _minimise_distance_worker(
        runner: pathlib.Path,
        interaction_generator: interactiongen.InteractionGenerator,
        starting_config_path: pathlib.Path, in_q: multiprocessing.Queue,
        report_q: multiprocessing.Queue, result_q: multiprocessing.Queue):
    global_min_neg = global_min_pos = None
    num_executes = num_errors = 0
    last_report_time = time.time()
    while True:
        if (time.time() - last_report_time > 10 and
                (num_errors or num_executes)):
            report_q.put((num_executes, num_errors))
            num_executes = num_errors = 0
            last_report_time = time.time()

        try:
            while True:
                global_update = in_q.get_nowait()
                if global_update is None:
                    # We're being told to shutdown
                    if num_errors or num_executes:
                        report_q.put((num_executes, num_errors))
                    return

                if global_update > 0:
                    global_min_pos = global_update
                else:
                    global_min_neg = global_update
        except queue.Empty:
            pass

        interactions = interaction_generator.generate()
        distance, err = _run_instance(runner, starting_config_path,
                                      interactions)
        num_executes += 1

        if err:
            num_errors += 1
            continue

        if distance > 0:
            if global_min_pos is None or distance < global_min_pos:
                global_min_pos = distance
                result_q.put(
                        (interactions, distance, num_executes, num_errors))
                num_executes = num_errors = 0
                last_report_time = time.time()
        else:
            if global_min_neg is None or distance > global_min_neg:
                global_min_neg = distance
                result_q.put((interactions, distance, num_executes, num_errors))
                num_executes = num_errors = 0
                last_report_time = time.time()


def _shutdown_workers(
        workers: List[Tuple[multiprocessing.Process, multiprocessing.Queue,
                            multiprocessing.Queue]]) -> Tuple[int, int]:
    logger = logutils.get_logger()

    for worker, in_q, report_q in workers:
        in_q.put(None)

    total_errors = total_executions = 0
    still_alive = []
    for worker, _, report_q in workers:
        try:
            while True:
                execs, errors = report_q.get_nowait()
                total_executions += execs
                total_errors += errors
        except queue.Empty:
            pass

        worker.join(timeout=.1)
        if worker.is_alive():
            still_alive.append((worker, report_q))

    still_alive2 = []
    if still_alive:
        logger.info(
                "{} workers still running. Waiting a little longer ...".format(
                        len(still_alive)))
        for worker, report_q in still_alive:
            try:
                while True:
                    execs, errors = report_q.get_nowait()
                    total_executions += execs
                    total_errors += errors
            except queue.Empty:
                pass
            worker.join(timeout=.1)
            if worker.is_alive():
                still_alive2.append((worker, report_q))

    if still_alive2:
        logger.info("{} workers still running. Terminating ...".format(
                len(still_alive2)))
        for worker, report_q in still_alive2:
            try:
                while True:
                    execs, errors = report_q.get_nowait()
                    total_executions += execs
                    total_errors += errors
            except queue.Empty:
                pass

            worker.terminate()

    return total_errors, total_executions


def _write_starting_config(starting_config: List[str]) -> pathlib.Path:
    path = pathlib.Path("/tmp") / ("starting_config_" + str(uuid.uuid4()))
    with open(path.as_posix(), 'w') as fd:
        for x in starting_config:
            fd.write(x + "\n")

    return path

def _remove_starting_config(starting_config_path: pathlib.Path):
    os.remove(starting_config_path.as_posix())


def run_experiment(
        exp_res: ExpResult, driver: pathlib.Path,
        interaction_generator: interactiongen.InteractionGenerator,
        starting_config: List[str], output_dir: pathlib.Path,
        jobs: int, time_limit: int, execution_limit: int,
        cutoff: int):
    logger = logutils.get_logger()
    # All workers will share this queue and write their results to it
    worker_result_q = multiprocessing.Queue()
    starting_config_path = _write_starting_config(starting_config)

    workers = []
    for _ in range(jobs):
        in_q = multiprocessing.Queue()
        report_q = multiprocessing.Queue()
        workers.append((
            multiprocessing.Process(
                    target=_minimise_distance_worker, args=(
                        driver, interaction_generator, starting_config_path,
                        in_q, report_q, worker_result_q)),
            in_q, report_q))
        workers[-1][0].start()

    neg_trigger_path = output_dir / "neg_trigger.txt"
    pos_trigger_path = output_dir / "pos_trigger.txt"
    total_executions = total_errors = 0
    min_pos_dist = min_neg_dist = None
    start_time = time.time()
    progress_report = []

    while True:
        if ((time_limit and time.time() - start_time > time_limit) or
                (execution_limit and total_executions > execution_limit)):
            break

        report_change = False
        for _, _, report_q in workers:
            try:
                execs, errors = report_q.get_nowait()
                total_executions += execs
                total_errors += errors
                report_change = True
            except queue.Empty:
                pass

        if report_change:
            run_time = time.time() - start_time
            logger.info((
                "Min. pos: {}. Min. neg: {}. Run time {:.2f}s. "
                "{:.2f} executions per second. {} successful executions. "
                "{} errors.").format(
                    min_pos_dist, min_neg_dist, run_time,
                    (total_executions + total_errors) / run_time,
                    total_executions, total_errors))

        try:
            new_seq, new_dist, execs, errors = worker_result_q.get(timeout=5)
            total_executions += execs
            total_errors += errors
            if new_dist < 0:
                # The first was allocated before the second so add the size of
                # the first
                adj_dist = new_dist +interaction_generator.first_named_alloc
                assert adj_dist <= 0
                if min_neg_dist is None or adj_dist > min_neg_dist:
                    # Handle a new minimum negative distance
                    min_neg_dist = adj_dist
                    exp_res.record_neg_result(
                            min_neg_dist, time.time() - start_time,
                            total_executions)

                    with open(neg_trigger_path, 'w') as fd:
                        for x in starting_config:
                            fd.write(x + "\n")

                        fd.write("\n")

                        fd.write(new_seq[0] + "\n")
                        fd.write("vtx gamestart\n")

                        for x in new_seq[1:]:
                            fd.write(x + "\n")

                    logger.info("Min. neg. distance is now {} ({})".format(
                            min_neg_dist, neg_trigger_path))

                    run_time = int(time.time() - start_time)
                    progress_report.append(
                            (run_time, total_executions, min_pos_dist,
                             min_neg_dist))

                    # Distribute the new shortest distance to the other workers
                    for _, worker_in_q, _ in workers:
                        worker_in_q.put(new_dist)
            elif new_dist > 0:
                # The first was allocated after the second so subtract the
                # size of the second
                adj_dist = new_dist - interaction_generator.second_named_alloc
                assert adj_dist >= 0
                if min_pos_dist is None or adj_dist < min_pos_dist:
                    # Handle a new minimum positive distance
                    min_pos_dist = adj_dist
                    exp_res.record_pos_result(
                            min_pos_dist, time.time() - start_time,
                            total_executions)

                    with open(pos_trigger_path, 'w') as fd:
                        for x in starting_config:
                            fd.write(x + "\n")

                        fd.write("\n")

                        fd.write(new_seq[0] + "\n")
                        fd.write("vtx gamestart\n")

                        for x in new_seq[1:]:
                            fd.write(x + "\n")

                    logger.info("Min. pos. distance is now {} ({})".format(
                            min_pos_dist, pos_trigger_path))

                    run_time = int(time.time() - start_time)
                    progress_report.append(
                            (run_time, total_executions, min_pos_dist,
                             min_neg_dist))

                    # Distribute the new shortest distance to the other workers
                    for _, worker_in_q, _ in workers:
                        worker_in_q.put(new_dist)
        except queue.Empty:
            pass

        if (cutoff is not None and
                min_neg_dist is not None and
                min_pos_dist is not None and
                abs(min_neg_dist) <= cutoff and min_pos_dist <= cutoff):
            break

    exp_res.total_time = time.time() - start_time

    if (cutoff is not None and
            min_neg_dist is not None and
            min_pos_dist and
            abs(min_neg_dist) <= cutoff and min_pos_dist <= cutoff):
        logger.info((
            "Discovered distances <= the cut off. "
            "Shutting down workers ..."))
    elif execution_limit and total_executions > execution_limit:
        logger.info("Execution limit exceeded. Shutting down workers ...")
    else:
        logger.info("Time limit expired. Shutting down workers ...")

    errors, execs = _shutdown_workers(workers)
    total_executions += execs
    total_errors += errors

    exp_res.total_execs = total_executions

    logger.info("{} successful executions. {} errors.".format(
            total_executions, total_errors))

    logger.info("=== Progress Report ===")
    for t, e, pos, neg in progress_report:
        logger.info("Time: {}, execs: {}, pos: {}, neg: {}".format(
                t, e, pos, neg))
    logger.info("=== End Progress Report ===")
