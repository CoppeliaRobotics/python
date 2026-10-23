from typing import Any

import cbor2

from . import const as sim


class ObjectArray:
    CBOR_TAG = 4294999998

    def __init__(self, arg: Any, count: int | None = None):
        from .object import Object

        if isinstance(arg, str):
            arg = Object(sim.handle_scene).getObject(arg)

        if isinstance(arg, int):
            arg = Object(arg)

        if isinstance(arg, tuple):
            arg = list(arg)

        if isinstance(arg, list):
            n = count if count is not None else len(arg)
            for i in range(n):
                v = arg[i]
                if isinstance(v, Object):
                    continue
                if v == -1 or v is None:
                    arg[i] = None
                else:
                    arg[i] = Object(v)

        if isinstance(arg, Object):
            # implicit object array (argument = first object of the array)
            object.__setattr__(self, '_object0', arg)
            assert self[0] == arg, (
                f'implicit {type(self).__name__} must point to first object of the array'
            )
        elif isinstance(arg, list):
            # explicit object array
            object.__setattr__(self, '_objects', arg)
            count = count if count is not None else len(arg)

        object.__setattr__(self, '_count', count)

    def __getitem__(self, k: int) -> Any:
        if not isinstance(k, int):
            raise TypeError(f'invalid index type: {type(k).__name__}')

        object0 = getattr(self, '_object0', None)
        if object0 is not None:
            # implicit object array: traverse siblings by name
            if k >= 0:
                from .object import Object
                parent = object0.parent
                siblings = parent.children if parent else Object(sim.handle_scene).orphans
                name = object0.name
                for child in siblings:
                    if child.name == name:
                        if k <= 0:
                            return child
                        k -= 1
            raise IndexError(k)
        else:
            objects = getattr(self, '_objects', None)
            if objects is None:
                raise IndexError(k)
            return objects[k]

    def __getattr__(self, k: str) -> Any:
        if k.startswith('_'):
            raise AttributeError(k)

        # object-array property access (return a list of values)
        ret = []
        for i in range(len(self)):
            obj = self[i]
            if obj is not None:
                ret.append(getattr(obj, k))
            elif k == 'handle':
                # handle is special: replace nil with -1
                ret.append(-1)
            else:
                ret.append(None)
        return ret

    def __setattr__(self, k: str, v: Any) -> None:
        if k.startswith('_'):
            return object.__setattr__(self, k, v)

        # set the property on every object in the array
        for i in range(len(self)):
            setattr(self[i], k, v)

    def __setitem__(self, k: Any, v: Any) -> None:
        raise TypeError(
            f'{type(self).__name__} contents cannot be modified. '
            f'Use method :tolist() to copy into a plain table.'
        )

    def __len__(self) -> int:
        count = getattr(self, '_count', None)
        if count is not None:
            return count

        from .object import Object
        object0 = self._object0
        parent = object0.parent
        siblings = parent.children if parent else Object(sim.handle_scene).orphans
        name = object0.name
        return sum(1 for child in siblings if child.name == name)

    def __str__(self) -> str:
        return f'{type(self).__name__}{self.tolist()}'

    def __cbor__(self):
        return cbor2.CBORTag(self.CBOR_TAG, self.tolist())

    @staticmethod
    def fromcbor(tag: cbor2.CBORTag):
        if tag.tag == ObjectArray.CBOR_TAG:
            return ObjectArray(tag.value)

    @staticmethod
    def isobjectarray(o: Any) -> bool:
        return isinstance(o, ObjectArray)

    @property
    def handle(self) -> list[int]:
        return self.tolist()

    def tolist(self) -> list[int]:
        ret = []
        for i in range(len(self)):
            obj = self[i]
            if obj is not None:
                ret.append(obj._handle)
            else:
                ret.append(-1)
        return ret

    def __dump__(self, maxDepth: int = 4) -> list:
        return [self[i].__dump__(maxDepth - 1) for i in range(len(self))]
