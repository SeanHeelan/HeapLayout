from typing import List, Union


class Alloc:
    FIRST_NAMED = 1
    SECOND_NAMED = 2
    NORMAL = 3

    def __init__(self, uid: int, size: int, alloc_type: int = NORMAL):
        self._uid = uid
        self._size = size
        self._alloc_type = alloc_type

    @property
    def uid(self):
        return self._uid

    @uid.setter
    def uid(self, value):
        self._uid = value

    @property
    def size(self):
        return self._size

    @size.setter
    def size(self, value):
        self._size = value

    @property
    def alloc_type(self):
        return self._alloc_type

    @alloc_type.setter
    def alloc_type(self, value):
        self._alloc_type = value

    def stringify(self) -> str:
        if self.alloc_type == Alloc.NORMAL:
            return 'vtx alloc {} {}'.format(self.uid, self.size)
        elif self.alloc_type == Alloc.FIRST_NAMED:
            return 'vtx src {}'.format(self.size)
        elif self.alloc_type == Alloc.SECOND_NAMED:
            return 'vtx dst {}'.format(self.size)


class Calloc:
    def __init__(self, uid: int, nmemb: int, size: int):
        self._uid = uid
        self._nmemb = nmemb
        self._size = size

    @property
    def uid(self):
        return self._uid

    @uid.setter
    def uid(self, value):
        self._uid = value

    @property
    def nmemb(self):
        return self._nmemb

    @nmemb.setter
    def nmemb(self, value):
        self._nmemb = value

    @property
    def size(self):
        return self._size

    @size.setter
    def size(self, value):
        self._size = value

    def stringify(self) -> str:
        return 'vtx calloc {} {} {}'.format(self.uid, self.nmemb, self.size)


class Free:
    def __init__(self, uid: int):
        self._uid = uid

    @property
    def uid(self):
        return self._uid

    @uid.setter
    def uid(self, value):
        self._uid = value

    def stringify(self) -> str:
        return 'vtx free {}'.format(self.uid)


class Realloc:
    def __init__(self, old_uid: int, new_uid: int, size: int):
        self._old_uid = old_uid
        self._new_uid = new_uid
        self._size = size

    @property
    def new_uid(self):
        return self._new_uid

    @new_uid.setter
    def new_uid(self, value):
        self._new_uid = value

    @property
    def old_uid(self):
        return self._old_uid

    @old_uid.setter
    def old_uid(self, value):
        self._old_uid = value

    @property
    def size(self):
        return self._size

    @size.setter
    def size(self, value):
        self._size = value

    def stringify(self) -> str:
        return 'vtx realloc {} {} {}'.format(
                self.old_uid, self.new_uid, self.size)


def stringify_sequence(
        interactions: List[Union[Alloc, Calloc, Free, Realloc]]) -> List[str]:
    return [x.stringify() for x in interactions]
