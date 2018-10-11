import logging
import multiprocessing
import os
import pathlib
import pickle
import queue
import random
import re
import subprocess
import sys
import time
import uuid

from collections import defaultdict

from shrike import InteractionSequence

logger = logging.getLogger(__name__)

SHRIKE_START_CODE = 'shrike_sequence_start();'
SHRIKE_END_CODE = 'shrike_sequence_end();'

SHRIKE_START_POINTER_CODE = 'shrike_pointer_sequence_start();'
SHRIKE_END_POINTER_CODE = 'shrike_pointer_sequence_end();'

# Match 'some_function_call(...);'. Doesn't support nested calls.
FUNC_CALL_RE = re.compile(
        '^[a-zA-Z_]+[a-zA-Z0-9_]*\([^\)]*\);$',
        re.MULTILINE)
INT_RE = re.compile('(\d+)', re.MULTILINE)
STR_RE = re.compile('("[^"]*"|\'[^\']*\')', re.MULTILINE)

# Match '$x = some_function_call(...);'. Doesn't support nested calls,
# variables as arguments or heredocs
# Group 1: The function call including its argument list
# Group 2: The function name
ASSIGN_FUNC_CALL_RE = re.compile(
        (
            '^\$[a-zA-Z_]+[a-zA-Z0-9_]*\s*='
            '\s*(([a-zA-Z_]+[a-zA-Z0-9_]*)\([^\)<$]*\));$'),
        re.MULTILINE)

# Lines look as follows:
# vtx map ffffffffff600000-ffffffffff601000 r-xp 00000000 00:00 0 [vsyscall]
ADDR_RANGE_RE = re.compile('^vtx map ([0-9a-f]+)-([0-9a-f]+)')
# Lines look as follows:
# vtx ptr 40 16 0x2ab52ca628c0 0x2a79730
VTX_PTR_RE = re.compile('^vtx ptr (\d+) (\d+) 0x([0-9a-f]+) 0x([0-9a-f]+)$')

# PHP functions we want to blacklist. This must be a valid PHP .ini directive.
DISABLE_FUNCTIONS_INI = (
        'disable_functions = "apache_child_terminate, apache_setenv, '
        'define_syslog_variables, escapeshellarg, escapeshellcmd, eval, '
        'exec, fp, fput, ftp_connect, ftp_exec, ftp_get, ftp_login, '
        'ftp_nb_fput, ftp_put, ftp_raw, ftp_rawlist, highlight_file, '
        'ini_alter, ini_get_all, ini_restore, inject_code, mysql_pconnect, '
        'openlog, passthru, php_uname, phpAds_remoteInfo, phpAds_XmlRpc, '
        'phpAds_xmlrpcDecode, phpAds_xmlrpcEncode, popen, posix_getpwuid, '
        'posix_kill, posix_mkfifo, posix_setpgid, posix_setsid, posix_setuid, '
        'posix_setuid, posix_uname, proc_close, proc_get_status, proc_nice, '
        'proc_open, proc_terminate, shell_exec, syslog, system, '
        'xmlrpc_entity_decode, fopen, glob, mkdir, fsockopen, tempnam,'
        'stream_socket_server"')

# Fatal errors from PHP
ERR_FATAL = 1
# Security errors from PHP
ERR_SECURITY = 2
# OS/Popen errors from the OS/Python
ERR_OS = 3
# Timeout
ERR_TIMEOUT = 4
# Segmentation fault
ERR_SEGV = 5


def _process_text(path):
    """Extract fragments from the PHP test found at `path`.

    Args:
        path (pathlib.Path): The path to the test

    Returns:
        A tuple of type (pathlib.Path, dict) where the first item is the path
        that was provided and the second is a dict mapping from function names
        to a set of unique invocations of that function which have been found.
    """

    with path.open(encoding='latin-1') as fd:
        text = fd.read()

    functions = defaultdict(set)
    for m in ASSIGN_FUNC_CALL_RE.finditer(text):
        func = m.group(2)
        logger.debug("{} (from {})".format(m.group(0), path))
        if func.find("sleep") != -1:
            continue
        functions[func].add(m.group(1))

    return (path, functions)


def extract_fragments(test_dir, processes):
    """Recursively iterates over the .phps files in `test_dir` and extracts
    fragements which can later be fuzzed.

    Args:
        test_dir (str): The directory containing the source of the PHP tests
        processes (int): The number of processes to utilise

    Returns:
        A dict mapping from function names to a set of examples of calls to
        that function. e.g. { 'foo': set('foo(1, 2, 3)', 'foo(4, 5)'}
    """

    paths = pathlib.Path(test_dir).rglob('*.phps')

    with multiprocessing.Pool(processes=processes) as pool:
        for path in paths:
            results = pool.map(_process_text, paths)

    no_result_count = processed_count = 0
    call_examples = defaultdict(set)
    for path, functions in results:
        processed_count += 1
        if not functions:
            no_result_count += 1
            continue
        for function_name, examples in functions.items():
            for e in examples:
                call_examples[function_name].add(e)

    logger.info("Processed {} files".format(processed_count))
    logger.info("No results from {} files".format(no_result_count))
    logger.info(
            "{} extracted functions".format(len(call_examples)))
    for k, v in call_examples.items():
        e = v.pop()
        v.add(e)
        logging.debug("\t{} (e.g. {})".format(k, e))

    return call_examples


def _complete_fragment(fragment, pointer_search):
    if pointer_search:
        return "\n".join([
            SHRIKE_START_POINTER_CODE,
            '$vtx_var = ' + fragment + ';',
            SHRIKE_END_POINTER_CODE,
            ])

    return "\n".join([
        SHRIKE_START_CODE,
        '$vtx_var = ' + fragment + ';',
        SHRIKE_END_CODE,
        ])


def _run_script(contents, php):
    fpath = pathlib.Path("/tmp") / str(uuid.uuid4())
    with open(fpath.as_posix(), 'w') as fd:
        fd.write("<?php\n")
        fd.write(contents)
        fd.write("\n?>")

    p = subprocess.run(
            [php, '-d', DISABLE_FUNCTIONS_INI, fpath.as_posix()],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            timeout=5)

    os.remove(fpath.as_posix())

    return p.returncode, p.stdout


def _analyse_fragment(fragment, php, pointer_search=False):
    script = _complete_fragment(fragment, pointer_search)
    try:
        retcode, stdout = _run_script(script, php)
    except OSError:
        return fragment, None, ERR_OS
    except subprocess.TimeoutExpired:
        return fragment, None, ERR_OS

    if retcode:
        return fragment, None, ERR_FATAL

    output = stdout.decode().splitlines()
    interactions = []
    for o in output:
        if o.find('disabled for security reasons') != -1:
            return fragment, None, ERR_SECURITY

        if o.startswith("vtx "):
            interactions.append(o.strip())

    return fragment, interactions, None


def get_interaction_sequences(fragments, processes, php):
    """Execute each of the `fragments` provided using the PHP interpreter at
    `php` and record the resulting allocator interaction sequences.

    Args:
        fragments (list of str): The code fragments to execute
        processes (int): The number of concurrent processes to use
        php (str): The path to the PHP binary to use

    Returns:
        A dict (str to SequenceSummary)) mapping from the fragments to
        summaries of the resulting allocator interaction sequences.
    """

    results = []
    with multiprocessing.Pool(processes=processes) as pool:
        for t in fragments:
            results.append(pool.apply_async(_analyse_fragment, (t, php)))
        pool.close()
        pool.join()

    sequences = {}
    err_fatal = err_os = err_sec = err_no_interaction = 0
    for result_obj in results:
        fragment, interactions, err = result_obj.get(timeout=1)
        if err:
            if err == ERR_FATAL:
                # Some sort of fatal error was reported by the interpreter.
                # Probably an attempt to use an undefined function.
                err_fatal += 1
            elif err == ERR_SECURITY:
                # Used a disabled function
                err_sec += 1
            elif err == ERR_OS:
                err_os += 1
            continue

        if not interactions:
            # No allocator interactions
            err_no_interaction += 1
            continue

        sequences[fragment] = InteractionSequence(interactions).summary

    return sequences, err_fatal, err_os, err_sec, err_no_interaction


def dump_to_file(sequences, fname):
    """Pickle `sequences` and store in the file specified by `fname`.

    Args:
        sequences (dict of str to SequenceSummary): A mapping from a code
            fragment to the resulting interaction sequence triggered by it.
        fname (str): The path to store `sequences` as a pickled object

    """

    with open(fname, 'wb') as fd:
        pickle.dump(sequences, fd)


def _get_fuzz_int():
    x = random.random()
    if x < .5:
        return random.randint(0, 64)
    elif x < .7:
        return random.randint(65, 256)
    elif x < .95:
        return random.randint(257, 1024)
    else:
        return random.randint(1025, 32768)


def _fuzz_int_args(function_name, arg_list, count=100):
    int_split = INT_RE.split(arg_list)
    int_indices = []
    i = 0
    while i < len(int_split):
        try:
            int(int_split[i])
            int_indices.append(i)
        except ValueError:
            pass
        i += 1

    if not int_indices:
        # No int arguments
        return []

    result = []
    for _ in range(count):
        indices_to_fuzz = set()
        if len(int_indices) > 1:
            num_to_fuzz = range(random.randint(1, len(int_indices)))
            for _ in num_to_fuzz:
                indices_to_fuzz.add(
                        int_indices[random.randint(0, len(int_indices) - 1)])
        else:
            indices_to_fuzz.add(0)

        for index in indices_to_fuzz:
            fuzz_val = str(_get_fuzz_int())
            int_split[index] = fuzz_val

        new_arg_list = ''.join(int_split)
        result.append(function_name + '(' + new_arg_list)

    return result


def _get_fuzz_str():
    x = random.random()
    if x < .5:
        v = random.randint(0, 64)
    elif x < .7:
        v = random.randint(65, 256)
    elif x < .95:
        v = random.randint(257, 1024)
    else:
        v = random.randint(1025, 32768)

    return '"' + "A" * v + '"'


def _fuzz_str_args(function_name, arg_list, count=100):
    str_split = STR_RE.split(arg_list)
    str_indices = []
    i = 0
    while i < len(str_split):
        s = str_split[i]
        if s.startswith("'") or s.startswith('"'):
            str_indices.append(i)
        i += 1

    if not str_indices:
        # No str arguments
        return []

    result = []
    for _ in range(count):
        indices_to_fuzz = set()
        if len(str_indices) > 1:
            num_to_fuzz = range(random.randint(1, len(str_indices)))
            for _ in num_to_fuzz:
                indices_to_fuzz.add(
                        str_indices[random.randint(0, len(str_indices) - 1)])
        else:
            num_to_fuzz = 1
            indices_to_fuzz.add(0)

        for index in indices_to_fuzz:
            fuzz_val = str(_get_fuzz_str())
            str_split[index] = fuzz_val

        new_arg_list = ''.join(str_split)
        result.append(function_name + '(' + new_arg_list)

    return result


def _fuzz_fragment(fragment, count=100):
    function_name, arg_list = fragment.split('(', 1)
    if arg_list == ')':
        # No arguments
        return []

    int_result = _fuzz_int_args(function_name, arg_list, count//2)
    if int_result:
        str_result = _fuzz_str_args(function_name, arg_list, count//2)
        if str_result:
            int_result.extend(str_result)
            return int_result
        else:
            int_result.extend(_fuzz_int_args(
                function_name, arg_list, count//2))
            return int_result

    return _fuzz_str_args(function_name, arg_list, count)


def _fuzz_process(fragment_store, php, time_limit):
    new_sequences = {}
    existing_summaries = fragment_store.get_summaries()
    existing_fragments = fragment_store.get_fragments()

    total_execs = total_duplicates = total_errors = 0
    start_time = time.time()
    while time.time() - start_time < time_limit:
        fragment = random.sample(existing_fragments, 1)[0]
        new_fragments = _fuzz_fragment(fragment)

        if not new_fragments:
            continue

        for new_fragment in new_fragments:
            fragment, interactions, err = _analyse_fragment(new_fragment, php)
            total_execs += 1
            if err or not interactions:
                total_errors += 1
                continue

            sequence = InteractionSequence(interactions)
            if sequence.summary in existing_summaries:
                total_duplicates += 1
                continue

            logger.debug("{} => {}".format(new_fragment, sequence))
            new_sequences[new_fragment] = sequence.summary
            existing_summaries.add(sequence.summary)

    return new_sequences, total_execs, total_duplicates, total_errors


def fuzz(fragment_store, processes, php, time_limit):
    """Fuzz the code fragments given by the keys of `interaction_sequences` to
    find new interaction sequences.

    Args:
        interaction_sequences (dict of str to SequenceSummary): A mapping from
            code fragments to a summary of the allocator interaction sequences
            triggered by each fragment
        processes (int): The number of concurrent processes to use
        time (int): The total runtime to use, in seconds

    Returns:
        A dict of str to SequenceSummary specifying new interaction sequences
        discovered during fuzzing, and the fragments to trigger them.
    """

    async_results = []
    with multiprocessing.Pool(processes=processes) as pool:
        for _ in range(processes):
            async_results.append(pool.apply_async(
                _fuzz_process, (fragment_store, php, time_limit)))

        pool.close()
        pool.join()

    new_sequences = {}
    existing_summaries = fragment_store.get_summaries()

    total_execs = total_duplicates = total_errors = 0
    for async_result in async_results:
        result, execs, duplicates, errors, = async_result.get(timeout=1)
        total_execs += execs
        total_duplicates += duplicates
        total_errors += errors
        for fragment, summary in result.items():
            if summary in existing_summaries:
                total_duplicates += 1
                continue
            new_sequences[fragment] = summary
            existing_summaries.add(summary)

    logger.info("{} total executions ({} per second)".format(
        total_execs, total_execs/time_limit))
    logger.info("{} duplicates discovered".format(total_duplicates))
    logger.info("{} errors".format(total_errors))
    return new_sequences


def _gen_str_repeat_fragments():
    for repeat_count in range(1, 8192 + 1, 8):
        fragment = "str_repeat('A', {})".format(repeat_count)
        yield fragment

    # 2**17 == 131072
    for repeat_count in range(8192, 2**17 + 1, 4096):
        fragment = "str_repeat('A', {})".format(repeat_count)
        yield fragment

    # 262 KB
    yield "str_repeat('A', {})".format(2**18)
    # 4 MB
    yield "str_repeat('A', {})".format(2**22)


def _gen_imagecreatetruecolor_fragments():
    fragment = "imagecreatetruecolor(1, 1)"
    yield fragment

    for i in range(0, 16 + 1):
        fragment = "imagecreatetruecolor({}, 32)".format(2**i)
        yield fragment
        fragment = "imagecreatetruecolor({}, 64)".format(2**i)
        yield fragment
        fragment = "imagecreatetruecolor({}, 128)".format(2**i)
        yield fragment
        fragment = "imagecreatetruecolor({}, 256)".format(2**i)
        yield fragment


def controlled_gen(processes, php, only_str_repeat=False):
    """Generate a controlled set of sequences based on imagecreatetruecolor and
    str_repeat.
    """

    sequences = {}
    total_execs = total_errors = total_duplicates = 0
    for fragment in _gen_str_repeat_fragments():
        fragment, interactions, err = _analyse_fragment(fragment, php)
        total_execs += 1
        if err or not interactions:
            total_errors += 1
            continue

        sequence = InteractionSequence(interactions)
        if sequence.summary in sequences:
            total_duplicates += 1
            continue

        logger.debug("{} => {}".format(fragment, sequence))
        sequences[fragment] = sequence.summary

    logger.info("{} execs, {} errors, {} duplicates from str_repeat".format(
            total_execs, total_errors, total_duplicates))

    if only_str_repeat:
        return sequences

    total_execs = total_errors = total_duplicates = 0
    for fragment in _gen_imagecreatetruecolor_fragments():
        fragment, interactions, err = _analyse_fragment(fragment, php)
        total_execs += 1
        if err or not interactions:
            total_errors += 1
            continue

        sequence = InteractionSequence(interactions)
        if sequence.summary in sequences:
            total_duplicates += 1
            continue

        logger.debug("{} => {}".format(fragment, sequence))
        sequences[fragment] = sequence.summary

    logger.info(("{} execs, {} errors, {} duplicates from "
                 "imagecreatetruecolor").format(
            total_execs, total_errors, total_duplicates))
    return sequences


def load_from_files(fnames):
    """Unpickle the contents of the one or more paths found in `fnames`

    Args:
        fnames (list of str): The paths to unpickle.

    Returns:
        A dict of str to SequenceSummary.
    """

    paths = [pathlib.Path(p) for p in fnames]
    for p in paths:
        if not p.exists():
            logger.error("Path does not exist: {}".format(p))
            return None

    log_str = ", ".join([p.name for p in paths])
    logger.info("Loading data from {}".format(log_str))

    data = [load_from_file(p) for p in paths]
    result = {}
    for d in data:
        for fragment, info in d.items():
            result[fragment] = info

    return result


def load_from_file(fname):
    """Unpickle the contents of `fname` and return it.

    Args:
        fname (pathlib.Path): The path to unpickle. Most likely stored via
            `dump_to_file`.

    Returns:
        A dict of str to SequenceSummary.
    """

    with fname.open('rb') as fd:
        return pickle.load(fd)


class PointerRecord:

    def __init__(self, size, offset, ptr):
        self.allocation_size = size
        self.offset_in_container = offset
        self.pointer = ptr


def _get_pointers(fragment, interactions):
    """Parse the output lines in `interactions`, which contains both candidate
    pointers and a dump of /proc/self/maps, to determine if the fragment which
    generated this data allocated any valid-looking pointers or not.
    """

    mapped_memory = []
    candidate_pointers = set()
    for i in interactions:
        m = ADDR_RANGE_RE.match(i)
        if m:
            # vtx map line
            mapped_memory.append((int(m.group(1), 16), int(m.group(2), 16)))
            continue
        m = VTX_PTR_RE.match(i)
        if m:
            # vtx ptr line
            allocation_size = int(m.group(1), 10)
            offset = int(m.group(2), 10)
            found_pointer = int(m.group(4), 16)
            candidate_pointers.add(
                    PointerRecord(allocation_size, offset, found_pointer))
            continue

    real_pointers = []
    for record in candidate_pointers:
        for start, end in mapped_memory:
            if record.pointer >= start and record.pointer < end:
                real_pointers.append(record)
                break

    return fragment, real_pointers


def pointer_search(fragments, processes, php):
    """Execute the provided fragments to determine which result in the
    allocation of pointers on the heap.

    Args:
        fragments (set of str): The code fragments to check
        processes (int): The number of concurrent processes to use
        php (str): The PHP binary to use

    Returns:
        A dict of str to int, mapping from fragments that allocate pointers to
        the number of pointers allocated.
    """

    # First, run each fragment in pointer-search mode
    async_results = []
    with multiprocessing.Pool(processes=processes) as pool:
        for fragment in fragments:
            async_results.append(pool.apply_async(
                _analyse_fragment, (fragment, php, True)))

        pool.close()
        pool.join()

    fragment_interactions = {}
    err_fatal = err_sec = err_os = err_no_pointers = 0
    for result_obj in async_results:
        fragment, interactions, err = result_obj.get(timeout=1)
        if err:
            if err == ERR_FATAL:
                # Some sort of fatal error was reported by the interpreter.
                # Probably an attempt to use an undefined function.
                err_fatal += 1
            elif err == ERR_SECURITY:
                # Used a disabled function
                err_sec += 1
            elif err == ERR_OS:
                err_os += 1
            continue
        fragment_interactions[fragment] = interactions

    # Second, process the output of each of the above runs to find out which
    # allocate pointers
    async_results = []
    with multiprocessing.Pool(processes=processes) as multiprocessing.Pool:
        for fragment, interactions in fragment_interactions.items():
            async_results.append(multiprocessing.Pool.apply_async(
                _get_pointers, (fragment, interactions)))

        multiprocessing.Pool.close()
        multiprocessing.Pool.join()

    pointer_fragments = {}
    for result_obj in async_results:
        fragment, pointers = result_obj.get(timeout=1)
        if len(pointers):
            pointer_fragments[fragment] = pointers
        else:
            err_no_pointers += 1

    return pointer_fragments, err_fatal, err_os, err_sec, err_no_pointers


def _run_candidate(candidate: str, php: str):
    err = None
    interactions = []

    fpath = pathlib.Path("/tmp") / str(uuid.uuid4())
    with open(fpath.as_posix(), 'w') as fd:
        fd.write(candidate)

    try:
        p = subprocess.run(
                [php, '-d', DISABLE_FUNCTIONS_INI, fpath.as_posix()],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                timeout=5)
        if p.returncode:
            if p.returncode == -11:
                err = ERR_SEGV
            else:
                err = ERR_FATAL

        output = p.stdout.decode().splitlines()
        for o in output:
            if o.find('disabled for security reasons') != -1:
                err = ERR_SECURITY

            if o.startswith("vtx "):
                interactions.append(o.strip())
    except OSError:
        err = ERR_OS
        logger.error("OSError running {}".format(fpath))
    except subprocess.TimeoutExpired:
        logger.error("Timeout running {}".format(fpath))
        err = ERR_TIMEOUT
    except ValueError as e:
        logger.error("ValueError running {}: {}".format(fpath, e))
        err = ERR_OS

    return fpath, interactions, err


def _extract_distance(output):
    dist = None

    for line in output:
        if line.startswith("vtx distance"):
            split = line.split(" ")
            dist = int(split[2], 10)
            break
    if dist and dist < 0:
        return None
    return dist


def _minimise_distance_worker(
        template, php, in_q, report_q, result_q, keep_candidates=False):
    global_shortest = None
    global_seq_len = None
    num_executes = num_errors = 0
    last_report_time = time.time()
    while True:
        if (time.time() - last_report_time > 10
                and (num_errors or num_executes)):
            report_q.put((num_executes, num_errors))
            num_executes = num_errors = 0
            last_report_time = time.time()

        try:
            in_data = in_q.get_nowait()
            if in_data is None:
                if num_errors or num_executes:
                    report_q.put((num_executes, num_errors))
                    in_q.close()
                    report_q.close()
                    result_q.close()
                return
            global_shortest, global_seq_len = in_data
        except queue.Empty:
            pass

        candidate = template.instantiate()
        fpath, interactions, err = _run_candidate(candidate, php)
        if not err and not interactions:
            logger.error("No output generated from {}".format(fpath))
            sys.exit(1)

        if not keep_candidates:
            os.remove(fpath.as_posix())

        if err:
            num_errors += 1
        num_executes += 1

        distance = _extract_distance(interactions)
        if distance and (
                not global_shortest or distance < global_shortest or
                (distance == global_shortest and
                    len(candidate) < global_seq_len)):
            global_shortest = distance
            global_seq_len = len(candidate)
            result_q.put((pickle.loads(pickle.dumps(template)), distance))
            report_q.put((num_executes, num_errors))
            num_executes = num_errors = 0
            last_report_time = time.time()


def _shutdown_workers(workers):
    for worker, in_q, report_q in workers:
        in_q.put(None)

    logger.info("Shutdown notification sent. Waiting 30 seconds ...")
    time.sleep(30)

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

        worker.join(timeout=0.01)
        if worker.is_alive():
            still_alive.append((worker, report_q))

    still_alive2 = []
    if still_alive:
        logger.info(
            "{} workers still running. Waiting 30 seconds ...".format(
                len(still_alive)))
        time.sleep(30)

        for worker, report_q in still_alive:
            try:
                while True:
                    execs, errors = report_q.get_nowait()
                    total_executions += execs
                    total_errors += errors
            except queue.Empty:
                pass
            worker.join(timeout=0.01)
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

    return total_executions, total_errors


def minimise_distance_single_process(
        php, template, time_limit, keep_candidates=False):
    """Run distance minimisation in the current process"""

    total_executions = total_errors = 0
    shortest_distance = None
    best_prog = None
    start_time = time.time()
    progress_report = []
    cut_off = template.current_required_distance()
    last_report_time = time.time()

    template = pickle.loads(pickle.dumps(template))
    while time.time() - start_time < time_limit:
        candidate = template.instantiate()
        fpath, interactions, err = _run_candidate(candidate, php)
        if not interactions:
            logger.error("No output generated from {}".format(fpath))
            sys.exit(1)

        if not keep_candidates:
            os.remove(fpath.as_posix())

        if err:
            total_errors += 1
        total_executions += 1

        new_dist = _extract_distance(interactions)
        if not new_dist:
            continue

        # Check if this candidate is an improvement
        if (not shortest_distance or new_dist < shortest_distance or
                (new_dist == shortest_distance and
                    len(template) < len(best_prog))):
            if not shortest_distance or new_dist < shortest_distance:
                logger.info("Shortest distance is now {}".format(
                    shortest_distance))
            else:
                logger.info((
                    "Shortest sequences for distance {} is "
                    "now {}").format(new_dist, len(template)))

            shortest_distance = new_dist
            best_prog = pickle.loads(pickle.dumps(template))

            run_time = int(time.time() - start_time)
            progress_report.append((
                run_time, shortest_distance, total_executions, total_errors))

        # Status update
        if time.time() - last_report_time > 10:
            run_time = time.time() - start_time
            logger.info((
                "Shortest distance {}. Run time {:.2f}s. "
                "{:.2f} executions per second. {} successful executions. "
                "{} errors.").format(
                    shortest_distance, run_time,
                    (total_executions + total_errors) / run_time,
                    total_executions - total_errors, total_errors))
            last_report_time = time.time()

        # Are we done?
        if cut_off and shortest_distance and shortest_distance <= cut_off:
            break

    if cut_off and shortest_distance and shortest_distance <= cut_off:
        logger.info((
            "Discovered distance less than the cut off. "
            "Shutting down workers ..."))
    else:
        logger.info("Time limit expired. Shutting down workers ...")
        return False, best_prog

    logger.info("{} successful executions. {} errors.".format(
        total_executions - total_errors, total_errors))

    logger.info("=== Progress Report ===")
    for t, d, ex, er in progress_report:
        logger.info(
                "Time: {}, Distance: {}, Executions: {}, Errors: {}".format(
                    t, d, ex - er, er))
    logger.info("=== End Progress Report ===")

    return True, best_prog


def minimise_distance(
        processes, php, template, time_limit, keep_candidates=False):
    """Execute the provided fragments to determine which result in the
    allocation of pointers on the heap.
    """

    worker_result_q = multiprocessing.Queue()
    cut_off = template.current_required_distance()

    workers = []
    logger.info("Starting {} workers".format(processes))
    for _ in range(processes):
        in_q = multiprocessing.Queue()
        report_q = multiprocessing.Queue()
        workers.append((
                multiprocessing.Process(
                    target=_minimise_distance_worker, args=(
                        template, php, in_q,
                        report_q, worker_result_q,
                        keep_candidates)),
                in_q, report_q))
    for w in workers:
        w[0].start()

    logger.info("Workers started")

    total_executions = total_errors = 0
    shortest_distance = None
    best_prog = pickle.loads(pickle.dumps(template))
    start_time = time.time()
    progress_report = []
    while time.time() - start_time < time_limit:
        report_change = False
        for worker, _, _ in workers:
            if not worker.is_alive():
                logger.error("A worker has died. Exiting.")
                _shutdown_workers(workers)
                sys.exit(1)

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
                "Shortest distance {}. Run time {:.2f}s. "
                "{:.2f} executions per second. {} successful executions. "
                "{} errors.").format(
                    shortest_distance, run_time,
                    (total_executions + total_errors) / run_time,
                    total_executions - total_errors, total_errors))

        try:
            new_prog, new_dist = worker_result_q.get(timeout=10)
            if (not shortest_distance or new_dist < shortest_distance or
                    (new_dist == shortest_distance and
                        len(new_prog) < len(best_prog))):
                if not shortest_distance or new_dist < shortest_distance:
                    logger.info("Shortest distance is now {}".format(
                        shortest_distance))
                else:
                    logger.info((
                        "Shortest sequences for distance {} is "
                        "now {}").format(new_dist, len(new_prog)))

                shortest_distance = new_dist
                best_prog = new_prog

                run_time = int(time.time() - start_time)
                progress_report.append((
                    run_time, shortest_distance,
                    total_executions, total_errors))

                # Distribute the new shortest distance to the other workers
                for _, worker_in_q, _ in workers:
                    worker_in_q.put((shortest_distance, len(best_prog)))
        except queue.Empty:
            pass

        if cut_off and shortest_distance and shortest_distance <= cut_off:
            break

    if cut_off and shortest_distance and shortest_distance <= cut_off:
        logger.info((
            "Discovered distance less than the cut off. "
            "Shutting down workers ..."))
        solved = True
    else:
        logger.info("Time limit expired. Shutting down workers ...")
        solved = False

    execs, errors = _shutdown_workers(workers)
    total_executions += execs
    total_errors += errors

    logger.info("{} successful executions. {} errors.".format(
        total_executions - total_errors, total_errors))

    logger.info("=== Progress Report ===")
    for t, d, ex, er in progress_report:
        logger.info(
                "Time: {}, Distance: {}, Executions: {}, Errors: {}".format(
                    t, d, ex - er, er))
    logger.info("=== End Progress Report ===")

    return solved, best_prog
