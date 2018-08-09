import time
from typing import List, Union

import random
from abc import ABCMeta, abstractmethod

from heapexp import logutils
from heapexp.interactiontypes import Alloc, Free, stringify_sequence


def get_php_str_repeat_generator(first_size, second_size):
    return PHPStrRepeatGenerator(first_size, second_size)


def get_synth_no_noise_small(first_size, second_size):
    return SynthBase(first_size, second_size)


def get_first_second_sizes_no_noise(first_size, second_size):
    return FirstSecondSizes(first_size, second_size)


def get_adjusting_fsnn(time_limit, first_size, second_size):
    return AdjustingFSNN(time_limit, first_size, second_size)


def get_sl1024afr55(first_size, second_size):
    return SL1024AFR55(first_size, second_size)


def get_sl256afr98(first_size, second_size):
    return SL256AFR98(first_size, second_size)


def get_sl8192afr100(first_size, second_size):
    return SL8192AFR100(first_size, second_size)


def get_sl1024afr98(first_size, second_size):
    return SL1024AFR98(first_size, second_size)


def get_g1sl1024afr98(first_size, second_size):
    return G1SL1024AFR98(first_size, second_size)


def get_g4sl1024afr98(first_size, second_size):
    return G4SL1024AFR98(first_size, second_size)


def get_g16sl1024afr98(first_size, second_size):
    return G16SL1024AFR98(first_size, second_size)


def get_hsg4sl1024afr98(first_size, second_size):
    return HSG4SL1024AFR98(first_size, second_size)


class InteractionGenerator(metaclass=ABCMeta):
    def __init__(self, first_named_alloc: int, second_named_alloc: int,
                 min_intervening_len: int = 0, max_intervening_len: int = 16,
                 min_seq_len: int = 0, max_seq_len: int = 256,
                 alloc_free_ratio: float = .55, guard_count: int = 0,
                 guard_size: int = 0):
        self._first_named_alloc = first_named_alloc
        self._second_named_alloc = second_named_alloc
        self._min_seq_len = min_seq_len
        self._max_seq_len = max_seq_len
        self._min_intervening_len = min_intervening_len
        self._max_intervening_len = max_intervening_len
        self._alloc_free_ratio = alloc_free_ratio
        self._guard_count = guard_count

        if guard_size:
            self._guard_size = guard_size
        else:
            self._guard_size = self._second_named_alloc

    @abstractmethod
    def generate(self) -> List[str]:
        pass

    @property
    def first_named_alloc(self):
        return self._first_named_alloc

    @property
    def second_named_alloc(self):
        return self._second_named_alloc


class SynthBase(InteractionGenerator):
    """Provides the most powerful set of interaction sequences. Each
    interaction sequence has length 1 and there is a sequence for each
    multiple of 4 in the range 4-256"""

    def __init__(self, *args, **kwargs):
        super(SynthBase, self).__init__(*args, **kwargs)

        self._first_id = 1
        self._second_id = 2
        self._next_alloc_id = 3
        self._still_alloced = set()

        self._available_alloc_sizes = []
        self.set_available_alloc_sizes()

    @abstractmethod
    def set_available_alloc_sizes(self):
        pass

    def _get_next_alloc_id(self) -> int:
        r = self._next_alloc_id
        self._next_alloc_id += 1
        return r

    def _get_alloc_sequence(self) -> Alloc:
        alloc_id = self._get_next_alloc_id()
        self._still_alloced.add(alloc_id)
        return Alloc(alloc_id, random.choice(self._available_alloc_sizes))

    def _get_free_sequence(self) -> Free:
        to_free = random.sample(self._still_alloced, 1)[0]
        self._still_alloced.remove(to_free)
        return Free(to_free)

    def _reset(self):
        self._next_alloc_id = 3
        self._still_alloced = set()

    def _get_interactions(self, count: int) -> List[Union[Alloc, Free]]:
        res = []
        for _ in range(count):
            if (len(self._still_alloced) == 0 or
                    random.random() <= self._alloc_free_ratio):
                # Allocate
                res.append(self._get_alloc_sequence())
            else:
                # Free
                res.append(self._get_free_sequence())

        return res

    def _get_first_named_alloc(self) -> Alloc:
        return Alloc(self._first_id, self._first_named_alloc,
                     Alloc.FIRST_NAMED)

    def _get_second_named_alloc(self) -> Alloc:
        return Alloc(self._second_id, self._second_named_alloc,
                     Alloc.SECOND_NAMED)

    def _get_guard_alloc(self) -> Alloc:
        alloc_id = self._get_next_alloc_id()
        # We don't add the ID to the _still_alloced set as we don't want the
        # guards to be free'able
        return Alloc(alloc_id, self._guard_size)

    def _add_guarded_first_named_alloc(self, res: List[Union[Alloc, Free]]):
        for _ in range(self._guard_count):
            res.append(self._get_guard_alloc())

        res.append(self._get_first_named_alloc())

        for _ in range(self._guard_count):
            res.append(self._get_guard_alloc())

    def generate(self) -> List[str]:
        """Generate a sequence of interaction sequences to be fed to an
        allocator
        """

        self._reset()

        res = self._get_interactions(
                random.randint(self._min_seq_len, self._max_seq_len))

        self._add_guarded_first_named_alloc(res)

        if random.randint(0, 1):
            # Add some noise between source and destination
            # Is this helpful? Why?
            noise = self._get_interactions(
                    random.randint(self._min_intervening_len,
                                   self._max_intervening_len))
            res.extend(noise)

        res.append(self._get_second_named_alloc())

        return stringify_sequence(res)


class SynthNoNoiseSmall(SynthBase):
    """Provides the most powerful set of interaction sequences. Each
    interaction sequence has length 1 and there is a sequence for each
    multiple of 4 in the range 4-256"""

    def set_available_alloc_sizes(self):
        self._available_alloc_sizes = [s for s in range(4, 256 + 4, 4)]


class PHPStrRepeatGenerator(SynthBase):
    """The str_repeat function of PHP allows one to allocate any size,
    starting from 33 bytes. Because of this we can just subclass the
    SynthNoNoiseSmall generator and replace the available allocation
    sizes with whatever we want.
    """

    def set_available_alloc_sizes(self):
        self._available_alloc_sizes = [33]

        for repeat_count in range(48 - 32, 2048 - 32 + 1, 16):
            self._available_alloc_sizes.append(repeat_count)

        # 4KB -> 128KB
        for repeat_count in range(4096 - 32, 2 ** 17 - 32 + 1, 4096):
            self._available_alloc_sizes.append(repeat_count)

        # 262KB
        self._available_alloc_sizes.append(2 ** 18 - 32)
        # 4MB
        self._available_alloc_sizes.append(2 ** 22 - 32)


class FirstSecondSizes(SynthBase):
    """Generator where the available allocation sizes are just those in
    use as the overflow source and target.
    """

    def set_available_alloc_sizes(self):
        self._available_alloc_sizes = [
            self.first_named_alloc, self.second_named_alloc]


class SL1024AFR55(FirstSecondSizes):
    def __init__(self, *args, **kwargs):
        """Generator where the available allocation sizes are just those in
        use as the overflow source and target.
        """
        super(SL1024AFR55, self).__init__(
                max_seq_len=1024, alloc_free_ratio=.55, *args, **kwargs)


class SL256AFR98(FirstSecondSizes):
    def __init__(self, *args, **kwargs):
        """Generator where the available allocation sizes are just those in
        use as the overflow source and target.
        """
        super(SL256AFR98, self).__init__(
                max_seq_len=256, alloc_free_ratio=.98, *args, **kwargs)


class SL8192AFR100(FirstSecondSizes):
    def __init__(self, *args, **kwargs):
        """Generator where the available allocation sizes are just those in
        use as the overflow source and target.
        """
        super(SL8192AFR100, self).__init__(
                max_seq_len=8192, alloc_free_ratio=1, *args, **kwargs)


class SL1024AFR98(FirstSecondSizes):
    def __init__(self, *args, **kwargs):
        """Generator where the available allocation sizes are just those in
        use as the overflow source and target.
        """
        super(SL1024AFR98, self).__init__(
                max_seq_len=1024, alloc_free_ratio=.98, *args, **kwargs)


class G1SL1024AFR98(SL1024AFR98):
    def __init__(self, *args, **kwargs):
        """Generator where the available allocation sizes are just those in
        use as the overflow source and target, the sequence length is 1024,
        the alloc-free ratio is .98 and the guard count is 1.
        """
        super(G1SL1024AFR98, self).__init__(guard_count=1, *args, **kwargs)


class G4SL1024AFR98(SL1024AFR98):
    def __init__(self, *args, **kwargs):
        """Generator where the available allocation sizes are just those in
        use as the overflow source and target, the sequence length is 1024,
        the alloc-free ratio is .98 and the guard count is 4.
        """
        super(G4SL1024AFR98, self).__init__(guard_count=4, *args, **kwargs)


class G16SL1024AFR98(SL1024AFR98):
    def __init__(self, *args, **kwargs):
        """Generator where the available allocation sizes are just those in
        use as the overflow source and target, the sequence length is 1024,
        the alloc-free ratio is .98 and the guard count is 16.
        """
        super(G16SL1024AFR98, self).__init__(guard_count=16, *args, **kwargs)


class HSG4SL1024AFR98(SL1024AFR98):
    def __init__(self, *args, **kwargs):
        """Generator where the available allocation sizes are just those in
        use as the overflow source and target, the sequence length is 1024,
        the alloc-free ratio is .98 and the guard count is 4. The guard size is
         set to half the second named alloc size.
        """
        super(HSG4SL1024AFR98, self).__init__(guard_count=4, *args, **kwargs)

        self._guard_size = self._second_named_alloc // 2


class AdjustingFSNN(FirstSecondSizes):
    def __init__(self, total_time, *args, **kwargs):
        """Generator where the available allocation sizes are just those in
        use as the overflow source and target.
        """
        super(AdjustingFSNN, self).__init__(*args, **kwargs)

        self._adjustment_distribution = [
            (.05, 32, .6),
            (.15, 64, .75),
            (.70, 1024, .98),
            (.10, 4096, .996)
        ]
        self._start_time = None
        self._next_adjustment_index = 0

        self._adjustments = [
            (0,
             self._adjustment_distribution[0][1],
             self._adjustment_distribution[0][2])]

        time_alloted_so_far = total_time * self._adjustment_distribution[0][0]
        idx = 1
        while idx < len(self._adjustment_distribution):
            self._adjustments.append(
                    (time_alloted_so_far,
                     self._adjustment_distribution[idx][1],
                     self._adjustment_distribution[idx][2]))
            this_allotment = self._adjustment_distribution[idx][0]
            time_alloted_so_far += total_time * this_allotment
            idx += 1

    def generate(self):
        if not self._start_time:
            self._start_time = time.time()

        if self._next_adjustment_index < len(self._adjustments):
            next_adjustment_time = self._adjustments[
                self._next_adjustment_index][0]
            passed_time = time.time() - self._start_time

            if passed_time >= next_adjustment_time:
                update_tpl = self._adjustments[
                    self._next_adjustment_index]
                self._max_seq_len = update_tpl[1]
                self._alloc_free_ratio = update_tpl[2]
                logger = logutils.get_logger()
                logger.info(("Updating interaction generator parameters: "
                             "max_seq_len: {}, alloc_free_ratio: {}").format(
                        self._max_seq_len, self._alloc_free_ratio))
                self._next_adjustment_index += 1

        return super(AdjustingFSNN, self).generate()
