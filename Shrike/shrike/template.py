"""Template parsing for version 2"""

import pathlib
import random
import re

from pathlib import Path
from typing import List
from typing import Set

import shrike

from shrike import FragmentStore


class UnknownComponentError(Exception):
    pass


class Code:

    def __init__(self, code: str):
        self.code = code

    def as_code(self, frag_store: FragmentStore) -> str:
        return self.code

    def as_directive(self) -> str:
        return self.code

    def last_instantiation(self) -> str:
        return self.code


class HeapManip:

    def __init__(self, sizes: List[int]):
        self.sizes = sizes
        self._accepted_solution = None
        self._last_instantiation = ""
        self._length = 0

    def __len__(self):
        return self._length

    def as_directive(self) -> str:
        self._last_instantiation = "#X-SHRIKE HEAP-MANIP {}".format(
                " ".join([str(x) for x in self.sizes]))
        return self._last_instantiation

    def as_code(self, frag_store: FragmentStore) -> str:
        if self._accepted_solution is not None:
            return self._accepted_solution

        sequence = []
        still_alloced = set()
        self._length = 0
        for i in range(random.randint(1, 1024)):
            self._length += 1
            if still_alloced and random.random() > .98:
                # Free
                to_free = random.sample(still_alloced, 1)[0]
                sequence.append("$var_vtx_{} = 0;".format(to_free))
                still_alloced.remove(to_free)
                continue

            # Alloc
            size = random.choice(self.sizes)
            if random.random() > .995:
                # .5 % of the time select at random from the list of candidates
                candidates = frag_store.get_fragments_for_size(size)
                sequence.append("# Randomly selecting from size {}".format(
                    size))
                sequence.append("$var_vtx_{} = {};".format(
                        i, random.choice(candidates)[0]))
            else:
                # 99.5% of the time use the shortest sequence in the candidates
                candidates = frag_store.get_shortest_fragments_for_size(size)
                seq = random.choice(candidates)
                sequence.append(
                        "# Selecting sequence {} for size {}".format(
                            seq[1], size))
                sequence.append("$var_vtx_{} = {};".format(i, seq[0]))

            still_alloced.add(i)

        self._last_instantiation = "\n".join(sequence)
        return self._last_instantiation

    def accept_solution(self):
        self._accepted_solution = self._last_instantiation

    def last_instantiation(self) -> str:
        return self._last_instantiation


class TemplateVersion:

    def __init__(self, version: int):
        self.version = version

    def as_directive(self) -> str:
        self._last_instantiation = "#X-SHRIKE TEMPLATE-VERSION {}".format(
                self.version)
        return self._last_instantiation

    def as_code(self, frag_store: FragmentStore) -> str:
        self._last_instantiation = ""
        return self._last_instantiation

    def last_instantiation(self) -> str:
        return self._last_instantiation


class RecordAlloc:

    def __init__(self, index: int, identifier: int):
        self.index = index
        self.identifier = identifier

    def as_directive(self) -> str:
        self._last_instantiation = "#X-SHRIKE RECORD-ALLOC {} {}".format(
                self.index, self.identifier)
        return self._last_instantiation

    def as_code(self, frag_store: FragmentStore) -> str:
        self._last_instantiation = "shrike_record_alloc({}, {});".format(
                self.index, self.identifier)
        return self._last_instantiation

    def last_instantiation(self) -> str:
        return self._last_instantiation


class RequireDistance:

    def __init__(
            self, id0: int, id1: int, distance: int,
            heap_manips: List[HeapManip]):
        self.id0 = id0
        self.id1 = id1
        self.distance = distance
        self.solved = False
        self.heap_manips = heap_manips

    def as_directive(self) -> str:
        self._last_instantiation = (
                "#X-SHRIKE REQUIRE-DISTANCE {} {} "
                "{}").format(self.id0, self.id1, self.distance)
        return self._last_instantiation

    def _get_as_code(self):
        code = []
        if not self.solved:
            code.append('shrike_print_distance({}, {});'.format(
                    self.id0, self.id1))
        code += [
                '$distance = shrike_get_distance({}, {});'.format(
                    self.id0, self.id1),
                'if ($distance != {}) {{'.format(self.distance),
                '    exit("Invalid layout. Distance: $distance\\n");',
        ]

        if not self.solved:
            code += [
                    '} else {',
                    '    exit("Valid layout. Distance: $distance\\n");',
                    '}'
            ]
        else:
            code += ['}']

        return "\n".join(code)

    def as_code(self, frag_store: FragmentStore) -> str:
        if self.solved:
            return self._last_instantiation
        self._last_instantiation = self._get_as_code()
        return self._last_instantiation

    def mark_as_solved(self):
        self.solved = True
        self._last_instantiation = self._get_as_code()

    def last_instantiation(self) -> str:
        return self._last_instantiation


class Template:
    """Parse template files to an intermediate representation. Supports
    iteration.
    """

    def __init__(self, path: Path, frag_store: FragmentStore):
        self._path = path
        self._frag_store = frag_store
        self._template = []
        self._group_count = 0
        self._current_require_distance: RequireDistance = None
        self._solved_stages = 0
        self._total_stages = 0
        self._heap_manips_for_require = []

        self._de_heap_manip = re.compile(
                r'^#X-SHRIKE HEAP-MANIP\s+(\d+(\s+\d+)*)\s*$')
        self._de_template_version = re.compile(
                r'^#X-SHRIKE TEMPLATE-VERSION\s+(\d+)\s*$')
        self._de_record_alloc = re.compile(
                r'^#X-SHRIKE RECORD-ALLOC\s+((\d+)\s+(\d+))\s*$')
        self._de_require_distance = re.compile(
                r'^#X-SHRIKE REQUIRE-DISTANCE\s+((\d+)\s+(\d+)\s+(\d+))\s*$')

        self._parse_handlers = {
                self._de_heap_manip: self._add_heap_manip,
                self._de_template_version: self._add_template_version,
                self._de_record_alloc: self._add_record_alloc,
                self._de_require_distance: self._add_require_distance
        }

        self._parse()

    def save_to(self, output: pathlib.Path):
        with open(output.as_posix(), 'w') as fd:
            fd.write(self._last_instantiation())

    def instantiate(self) -> str:
        """Produce a valid PHP file with an attempted solution to the next
        require-distance problem.
        """

        res = []
        require_distance_encountered = False

        for component in self._template:
            if isinstance(component, shrike.template.Code):
                res.append(component.as_code(self._frag_store))
                continue

            if isinstance(component, shrike.template.TemplateVersion):
                res.append(component.as_directive())
                continue

            if require_distance_encountered:
                res.append(component.as_directive())
                continue

            res.append(component.as_code(self._frag_store))
            if (isinstance(component, shrike.template.RequireDistance) and
                    not component.solved):
                require_distance_encountered = True

        return '\n'.join(res)

    def current_required_distance(self) -> int:
        return self._current_require_distance.distance

    def mark_current_stage_as_solved(self):
        self._current_require_distance.mark_as_solved()
        for heap_manip in self._current_require_distance.heap_manips:
            heap_manip.accept_solution()

        self._current_require_distance = None

        for component in self._template:
            if not isinstance(component, shrike.template.RequireDistance):
                continue
            if component.solved:
                continue
            self._current_require_distance = component
            break

        self._solved_stages += 1

    def is_solved(self) -> bool:
        return self._solved_stages == self._total_stages

    def num_remaining_stages(self) -> int:
        return self._total_stages - self._solved_stages

    def current_stage(self) -> int:
        return self._solved_stages

    def components(self) -> List:
        """Retrieve the template components"""

        return self._template

    def hlm_sizes_in_use(self) -> Set[int]:
        """Return a list of the sizes used for HLM in this template."""

        sizes = set()
        for component in self._template:
            if not isinstance(component, shrike.template.HeapManip):
                continue
            sizes.update(component.sizes)

        return sizes

    def __iter__(self):
        self._iter_idx = 0
        return self

    def __next__(self):
        if self._iter_idx >= len(self._template):
            raise StopIteration

        v = self._template[self._iter_idx]
        self._iter_idx += 1

        return v

    def __len__(self):
        res = 0
        for heap_manip in self._current_require_distance.heap_manips:
            res += len(heap_manip)

        return res

    def _last_instantiation(self) -> str:
        return '\n'.join([c.last_instantiation() for c in self._template])

    def _add_code(self, code: List[str]):
        self._template.append(Code(''.join(code)))

    def _add_heap_manip(self, args: List[str]):
        component = HeapManip([int(x) for x in args])
        self._template.append(component)
        self._heap_manips_for_require.append(component)

    def _add_template_version(self, args: List[str]):
        self._template.append(TemplateVersion(int(args[0])))

    def _add_record_alloc(self, args: List[str]):
        self._template.append(RecordAlloc(int(args[0]), int(args[1])))

    def _add_require_distance(self, args: List[str]):
        component = RequireDistance(
                int(args[0]), int(args[1]), int(args[2]),
                self._heap_manips_for_require)
        self._heap_manips_for_require = []
        self._template.append(component)

        if not self._current_require_distance:
            self._current_require_distance = component

        self._total_stages += 1

    def _is_shrike_directive(self, line: str):
        return line.startswith('#X-SHRIKE ')

    def _parse(self):
        with open(self._path) as fd:
            in_data = fd.readlines()

        curr_code = []
        for line in in_data:
            if not self._is_shrike_directive(line):
                curr_code.append(line)

            for regex, handler in self._parse_handlers.items():
                m = regex.match(line)
                if not m:
                    continue
                self._add_code(curr_code)
                curr_code = []

                args = [x for x in m.groups()[0].split()]
                handler(args)

        self._add_code(curr_code)
