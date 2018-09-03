import os
import pathlib
import random
import re

from abc import ABCMeta, abstractmethod
from typing import List, Union

from sieve.interactiontypes import Calloc, Alloc, Free, Realloc
from sieve.interactiongen import stringify_sequence
from sieve.logutils import get_logger


class StartingConfigError(Exception):
    pass


class StartingConfig(metaclass=ABCMeta):
    def __init__(self):
        self._generate_called = False
        self._sequence: List[str] = []

    @abstractmethod
    def generate(self, starting_id: int):
        """Generate the starting configuration and store it in the instances
        `_sequence` variable. This sequence will then be returned when `get` is
        called. `generate` should only be called once
        """
        pass

    @staticmethod
    def _stringify(
            interactions: List[Union[Alloc, Free, Realloc]]) -> List[str]:
        return [x.stringify() for x in interactions]

    def get(self) -> List[str]:
        if not self._generate_called:
            raise StartingConfigError("generate() must be called before get()")
        return self._sequence


class RandomStart(StartingConfig):
    def __init__(self, min_events: int, max_events: int,
                 min_size: int, max_size: int):
        super(RandomStart, self).__init__()

        self._min_events = min_events
        self._max_events = max_events
        self._min_size = min_size
        self._max_size = max_size

    def generate(self, starting_id: int):
        res = []
        next_alloc_id = starting_id
        still_allocd = set()
        for _ in range(random.randint(self._min_events, self._max_events)):
            if not still_allocd or random.random() <= .65:
                # Alloc
                size = random.randint(self._min_size, self._max_size)
                alloc = Alloc(next_alloc_id, size)
                still_allocd.add(next_alloc_id)
                next_alloc_id += 1
                res.append(alloc)
            else:
                # Free
                free = Free(random.sample(still_allocd, 1)[0])
                still_allocd.remove(free.uid)
                res.append(free)

        self._sequence = stringify_sequence(res)
        self._generate_called = True


class TraceGen(StartingConfig):
    def __init__(self, data_path: str):
        super(TraceGen, self).__init__()

        self._data_path = data_path

    def generate(self, starting_id: int):
        logger = get_logger()
        alloc_re = re.compile('vtx alloc (\d+) 0x([0-9a-f]+)')
        free_re = re.compile('vtx free 0x([0-9a-f]+)')
        realloc_re = re.compile(
                'vtx realloc (\d+) 0x([0-9a-f]+) 0x([0-9a-f]+)')
        calloc_re = re.compile('vtx calloc (\d+) (\d+) 0x([0-9a-f]+)')

        res = []
        next_alloc_id = starting_id
        addresses_to_ids = {}

        with open(self._data_path) as fd:
            for line in fd:
                line = line.strip()
                # Alloc
                m = re.fullmatch(alloc_re, line)
                if m:
                    sz = int(m.group(1))
                    addr = int(m.group(2), 16)

                    res.append(Alloc(next_alloc_id, sz))
                    addresses_to_ids[addr] = next_alloc_id
                    next_alloc_id += 1
                    continue

                # Calloc
                m = re.fullmatch(calloc_re, line)
                if m:
                    nmemb = int(m.group(1))
                    sz = int(m.group(2))
                    addr = int(m.group(3), 16)

                    res.append(Calloc(next_alloc_id, nmemb, sz))
                    addresses_to_ids[addr] = next_alloc_id
                    next_alloc_id += 1
                    continue

                # Free
                m = re.fullmatch(free_re, line)
                if m:
                    addr = int(m.group(1), 16)
                    if addr not in addresses_to_ids:
                        logger.error(
                                "Free of {} which was not allocated".format(
                                        addr))
                        continue
                    res.append(Free(addresses_to_ids[addr]))
                    del addresses_to_ids[addr]
                    continue

                # Realloc
                m = re.fullmatch(realloc_re, line)
                if m:
                    sz = int(m.group(1))
                    old_addr = int(m.group(2), 16)
                    new_addr = int(m.group(3), 16)

                    if old_addr != 0 and old_addr not in addresses_to_ids:
                        logger.error(
                                "Realloc of {} which was not allocated".format(
                                        old_addr))
                        continue

                    if old_addr != 0:
                        realloc = Realloc(addresses_to_ids[old_addr],
                                          next_alloc_id, sz)
                        del addresses_to_ids[old_addr]
                    else:
                        realloc = Realloc(0, next_alloc_id, sz)

                    res.append(realloc)
                    addresses_to_ids[new_addr] = next_alloc_id
                    next_alloc_id += 1
                    continue

                raise StartingConfigError(
                        "Unknown event type '{}'".format(line))

        self._sequence = stringify_sequence(res)
        self._generate_called = True


def get_random(starting_id: int = 32768, min_events: int = 64,
               max_events: int = 512, min_size: int = 8,
               max_size: int = 4096) -> List[str]:
    r = RandomStart(min_events, max_events, min_size, max_size)
    r.generate(starting_id)
    return r.get()


def get_php_emalloc(starting_id: int = 32768) -> List[str]:
    config_dir = pathlib.Path(os.environ['HEAP_STARTING_CONFIGS'])
    r = TraceGen(config_dir / 'php-emalloc.txt')
    r.generate(starting_id)
    return r.get()


def get_php_malloc(starting_id: int = 32768) -> List[str]:
    config_dir = pathlib.Path(os.environ['HEAP_STARTING_CONFIGS'])
    r = TraceGen(config_dir / 'php-malloc.txt')
    r.generate(starting_id)
    return r.get()


def get_ruby_malloc(starting_id: int = 32768) -> List[str]:
    config_dir = pathlib.Path(os.environ['HEAP_STARTING_CONFIGS'])
    r = TraceGen(config_dir / 'ruby-malloc.txt')
    r.generate(starting_id)
    return r.get()


def get_python_malloc(starting_id: int = 32768) -> List[str]:
    config_dir = pathlib.Path(os.environ['HEAP_STARTING_CONFIGS'])
    r = TraceGen(config_dir / 'python-malloc.txt')
    r.generate(starting_id)
    return r.get()


def get_default() -> List[str]:
    return []


def get_starting_config(config):
    if config == 'random':
        return get_random()
    elif config == 'php-malloc':
        return get_php_malloc()
    elif config == 'php-emalloc':
        return get_php_emalloc()
    elif config == 'ruby-malloc':
        return get_ruby_malloc()
    elif config == 'python-malloc':
        return get_python_malloc()
    elif config == 'default':
        return get_default()

    raise StartingConfigError("Unknown config: {}".format(config))
