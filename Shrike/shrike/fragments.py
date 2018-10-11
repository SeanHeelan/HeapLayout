"""Fragment and interaction sequence related functionality"""

import logging
import pathlib
import pickle

from typing import List
from typing import Tuple
from typing import Dict
from typing import Union
from typing import Iterable
from typing import Set

from collections import Sequence
from collections import defaultdict

logger = logging.getLogger(__name__)


class SequenceConstructionError(Exception):
    pass


class FragmentStoreException(Exception):
    pass


class SequenceSummary:
    """Provides a summary of an interaction sequence which can be used by
    analysis components to quickly check various properties of that
    sequence."""

    def __init__(self, sequence):
        self._seq_hash = hash(sequence)
        self._length = len(sequence)
        self.has_frees = False
        self.has_reallocs = False
        self.alloc_size_classes = set()
        self.leaks_mem = False
        self.self_contained = True

        i = 0
        live_allocs = set()
        for interaction in sequence:
            if isinstance(interaction, Free):
                self.has_frees = True
                if interaction.sequence_id:
                    live_allocs.remove(interaction.index)
                else:
                    self.self_contained = False
            elif isinstance(interaction, Realloc):
                self.has_reallocs = True
                if interaction.sequence_id:
                    live_allocs.remove(interaction.index)
                else:
                    self.self_contained = False
                live_allocs.add(i)
            elif (isinstance(interaction, Alloc) or
                    isinstance(interaction, Calloc)):
                tmp = self._round8(interaction.size)
                self.alloc_size_classes.add(tmp)
                live_allocs.add(i)
            else:
                raise SequenceConstructionError("Unknown type: {}".format(
                    interaction))

            i += 1

        if len(live_allocs):
            self.leaks_mem = True

    def _round8(self, v):
        return (v + 7) & 0xfffffff8

    def _round16(self, v):
        return (v + 15) & 0xfffffff0

    def _round1024(self, v):
        return (v + 1024) & 0xfffffc00

    def __eq__(self, other):
        return (isinstance(other, self.__class__) and
                self._seq_hash == other._seq_hash)

    def __hash__(self):
        return self._seq_hash

    def __str__(self):
        return ("{}(hash={}, length={}, has_frees={}, has_reallocs={}, "
                "self_contained={}, leaks_memory={}, size_classes={})").format(
                    self.__class__.__name__, self._seq_hash, self._length,
                    self.has_frees, self.has_reallocs, self.self_contained,
                    self.leaks_mem, self.alloc_size_classes)


class FragmentStore:

    def __init__(self, paths: Union[pathlib.Path, Iterable[pathlib.Path]]):
        self._paths = paths
        # Map from fragments to summaries
        self._store: Dict[str, SequenceSummary] = {}
        # Map from sizes to a list of corresponding fragments, that make
        # allocations of that size, and a summary of that fragment's execution
        self._sorted_size_map: Dict[int, List[str, SequenceSummary]] = {}
        # Map from sizes to a list of fragments all of which have the same
        # length interaction sequence and are shorter than all other available
        # interaction sequences for that size
        self._shortest_per_size: Dict[int, List[str]] = {}

        if isinstance(paths, pathlib.Path):
            self._load_from_file(paths)
        else:
            for p in paths:
                self._load_from_file(p)

    def num_sequences(self) -> int:
        """Return the number of unique interaction sequences."""

        return len(set(self._store.values()))

    def num_fragments(self) -> int:
        """Return the number of fragments."""

        return len(self._store)

    def get_fragments(self) -> Set[str]:
        """Return all fragments"""

        return set(self._store.keys())

    def get_summaries(self) -> Set[SequenceSummary]:
        """Return all summaries"""

        return set(self._store.values())

    def get_fragments_for_size(
            self, size: int) -> List[Tuple[str, SequenceSummary]]:
        """Get the fragments, and their summaries, which make allocations of
        the given size.
        """

        if not self._sorted_size_map:
            self._preprocess_fragments()

        if size not in self._sorted_size_map:
            return None
        return self._sorted_size_map[size]

    def get_shortest_fragments_for_size(
            self, size: int) -> List[Tuple[str, SequenceSummary]]:
        """Get the fragment(s) that have the shortest corresponding interaction
        sequences for the given size.
        """

        if not self._shortest_per_size:
            self._preprocess_fragments()

        if size not in self._shortest_per_size:
            return None
        return self._shortest_per_size[size]

    def _load_from_file(self, fname: pathlib.Path):
        with fname.open('rb') as fd:
            data = pickle.load(fd)

        for fragment, summary in data.items():
            self._store[fragment] = summary

    def _preprocess_fragments(self):
        # First calculate a mapping from size classes to a list of (fragment,
        # sequence) Tuples which allocate something of that size
        size_map = defaultdict(list)
        for f, s in self._store.items():
            if not s.self_contained:
                continue

            for size in s.alloc_size_classes:
                size_map[size].append((f, s))

        # Now sort the list for each size class in ascending order based on the
        # length of the interaction sequence
        def key_access(frag_and_summary):
            return frag_and_summary[1]._length

        for size, fragments_and_summaries in size_map.items():
            sorted_seq = sorted(fragments_and_summaries, key=key_access)
            self._sorted_size_map[size] = [(f, s) for f, s in sorted_seq]

        # Finally compute the shortest fragments for each size
        for size, candidates in self._sorted_size_map.items():
            self._shortest_per_size[size] = self._get_shortest_candidates(
                    candidates)

    def _get_shortest_candidates(
            self, candidates: List[Tuple[str, SequenceSummary]]) -> List[
                    Tuple[str, SequenceSummary]]:
        idx = 1
        same_len_candidates = [candidates[0]]

        while (idx < len(candidates) and
                candidates[idx][1]._length == candidates[0][1]._length):
            same_len_candidates.append(candidates[idx])
            idx += 1

        return same_len_candidates


class InteractionSequence(Sequence):
    """Represents a series of allocator interactions."""

    def __init__(
            self, sequence_as_strs: List[str], sequence_id: int = 1,
            summarise: bool = False):
        """Initialise the InteractionSequence from a list of strings
        representing a trace as provided by the SHRIKE extension for the
        interpreter."""

        self.sid = sequence_id
        self._sequence = None
        self._working_sequence = []

        self._construct(sequence_as_strs)
        if summarise:
            self.summary = SequenceSummary(self)
        else:
            self.summary = None

    @property
    def summary(self) -> SequenceSummary:
        if not self._summary:
            self._summary = SequenceSummary(self)

        return self._summary

    @summary.setter
    def summary(self, s: SequenceSummary):
        self._summary = s

    def _construct(self, sequence_as_strs: List[str]):
        ptr_to_idx = {}
        for interaction_str in sequence_as_strs:
            if interaction_str.startswith('vtx alloc'):
                _, _, sz_str, ptr_str = interaction_str.split(' ')
                self._append(Alloc(int(sz_str)))
                ptr_to_idx[ptr_str] = len(self) - 1
            elif interaction_str.startswith('vtx calloc'):
                # Treat it like an alloc
                _, _, sz_str, ptr_str = interaction_str.split(' ')
                self._append(Alloc(int(sz_str)))
                ptr_to_idx[ptr_str] = len(self) - 1
            elif interaction_str.startswith('vtx realloc'):
                _, _, sz_str, orig_ptr_str, ptr_str = interaction_str.split(
                        ' ')
                if int(orig_ptr_str, 16) == 0:
                    # Treat it like an alloc
                    self._append(Alloc(int(sz_str)))
                    continue

                index = ptr_to_idx.get(orig_ptr_str, None)
                if index is not None:
                    del ptr_to_idx[orig_ptr_str]
                    self._append(Realloc(int(sz_str), self.sid, index))
                else:
                    self._append(Realloc(int(sz_str), 0, None))
                ptr_to_idx[ptr_str] = len(self) - 1
            elif interaction_str.startswith('vtx free'):
                _, _, ptr_str = interaction_str.split(' ')
                if int(ptr_str, 16) == 0:
                    # Ignore free(0)
                    continue

                index = ptr_to_idx.get(ptr_str, None)
                if index is not None:
                    del ptr_to_idx[ptr_str]
                    self._append(Free(self.sid, index))
                else:
                    self._append(Free(0, None))
            else:
                raise SequenceConstructionError(
                        "Could not parse interaction string: {}".format(
                            interaction_str))

        self._finalise()

    def _finalise(self):
        self._sequence = tuple(self._working_sequence)
        self._working_sequence = None

    def _append(self, item):
        self._working_sequence.append(item)

    def __str__(self):
        contents = '(' + ",".join([str(s) for s in self._sequence]) + ')'
        return 'Sequence{}{}'.format(id(self), contents)

    def __getitem__(self, index):
        return self._sequence[index]

    def __len__(self):
        if self._sequence:
            return len(self._sequence)
        return len(self._working_sequence)

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False

        return (self._sequence == other._sequence and
                self._working_sequence == other._working_sequence)

    def __hash__(self):
        return hash(self._sequence)


class Interaction:
    pass


class Alloc(Interaction):

    def __init__(self, size):
        self.size = size

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False
        return self.size == other.size

    def __hash__(self):
        return hash(self.size)

    def __str__(self):
        return 'Alloc({})'.format(self.size)

    def __format__(self, fmt):
        return self.__str__()


class Calloc(Interaction):

    def __init__(self, size):
        self.size = size

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False
        return self.size == other.size

    def __hash__(self):
        return hash(self.size)

    def __str__(self):
        return 'Calloc({})'.format(self.size)

    def __format__(self, fmt):
        return self.__str__()


class Free(Interaction):

    def __init__(self, sequence_id, index):
        self.sequence_id = sequence_id
        self.index = index

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False
        return (self.sequence_id == other.sequence_id and
                self.index == other.index)

    def __hash__(self):
        return hash((self.sequence_id, self.index))

    def __str__(self):
        if self.sequence_id:
            return 'Free({}:{})'.format(self.sequence_id, self.index)
        return 'Free(None:None)'

    def __format__(self, fmt):
        return self.__str__()


class Realloc(Interaction):

    def __init__(self, size, sequence_id, index):
        self.size = size
        self.sequence_id = sequence_id
        self.index = index

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False
        return (self.size == other.size and
                self.sequence_id == other.sequence_id and
                self.index == other.index)

    def __hash__(self):
        return hash((self.size, self.sequence_id, self.index))

    def __str__(self):
        if self.sequence_id:
            return 'Realloc({}:{}, {})'.format(
                    self.sequence_id, self.index, self.size)
        return 'Realloc(None, None, {})'.format(self.size)

    def __format__(self, fmt):
        return self.__str__()
