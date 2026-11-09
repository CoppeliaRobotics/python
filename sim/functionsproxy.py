from typing import Any, Callable
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .object import Object


class FunctionsProxy:
    """
    Python counterpart of the Lua `script:getFunctions()` meta object.

    Lua returns a table whose `__index` yields a function calling
    `script:callFunction(name, ...)`, so it cannot be transferred as-is (over the
    wire it would be an empty map). Attribute access here yields callables doing
    the same:

        script.getFunctions().someFunction(1, 2)

    From Python the purpose is to reach the script's **Lua** functions, so the
    call is made as `callFunction('@' + name, ...)`: the engine strips the
    leading '@' and calls the Lua function directly, without going through
    `sysCall_ext` (which, for a Python-scripted script, would route bare names to
    Python). That works for plain Lua scripts too.

    Instances are created by `Object.getFunctions()`, which also checks that the
    object is a script.
    """

    def __init__(self, obj: 'Object'):
        super().__setattr__('_object', obj)

    def __getattr__(self, name: str) -> Callable:
        if name.startswith('_'):
            raise AttributeError(name)
        obj = self._object
        return lambda *args: obj._callMethod(obj.handle, 'callFunction', '@' + name, *args)

    def __getitem__(self, name: str) -> Callable:
        return getattr(self, name)

    def __dir__(self) -> list[str]:
        return []

    def __repr__(self) -> str:
        return f'sim.FunctionsProxy({self._object!r})'
