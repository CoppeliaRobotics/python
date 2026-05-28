from copy import copy
from types import SimpleNamespace
from typing import Any, Callable

from . import const as sim
from .propertygroup import PropertyGroup


propertyInfo = {}  # cache for property info, by objectType

LOCAL_ATTRS = ('_properties', '_handle', '_objectType')


class Object:
    _callMethod = None

    def __init__(self, handle: int):
        if isinstance(handle, Object):
            handle = handle.handle
        assert isinstance(handle, int)
        self._properties = None
        self._handle = handle
        self._objectType = ''

    def _setupPropertyGroups(self):
        if self._properties: return

        if self._handle == sim.handle_self:
            self._handle = Object._callMethod(self._handle, 'getLongProperty', 'handle')

        handle = self._handle

        self._objectType = Object._callMethod(handle, 'getStringProperty', 'objectType')

        self._properties = PropertyGroup(self)

        # TODO: add _methods local property

        namespaces = Object._callMethod(handle, 'getStringArrayProperty', 'metaInfo.namespaces')
        for ns in namespaces:
            super().__setattr__(ns, PropertyGroup(handle, prefix=ns))

    def __getattr__(self, k: str) -> Any:
        assert isinstance(k, str)

        if k in LOCAL_ATTRS:
            return super().__getattr__(k)

        self._setupPropertyGroups()

        attr = getattr(super(), k, None)
        if attr is not None:
            return attr

        return self._properties.__getattr__(k)

    def __setattr__(self, k: str, v: Any) -> None:
        assert isinstance(k, str)

        if k in LOCAL_ATTRS:
            return super().__setattr__(k, v)

        self._setupPropertyGroups()

        self._properties.__setattr__(k, v)

    def __str__(self) -> str:
        return f'sim.Object({self.handle})'

    def __dir__(self) -> list[str]:
        return dir(self._properties)

    @property
    def handle(self) -> int:
        self._setupPropertyGroups()
        return self._handle

    @property
    def objectType(self) -> int:
        self._setupPropertyGroups()
        return self._objectType

    def callMethod(self, method: str, *args: Any) -> Any:
        return Object._callMethod(self.handle, method, *args)

    def isValid(self) -> bool:
        return self.callMethod('isValid')

    def getPropertyInfo(
            self,
            pname: str,
            opts: dict[str, Any] | None = None,
    ) -> tuple[int, int, str]:
        if self.objectType not in propertyInfo:
            propertyInfo[self.objectType] = {}
        if pname in propertyInfo[self.objectType]:
            ptype, pflags, descr = propertyInfo[self.objectType][pname]
        else:
            ptype, pflags, descr = self.callMethod('getPropertyInfo', pname, opts or {})
            if pflags and (pflags & sim.propertyinfo_removable) > 0:
                return ptype, pflags, descr
            if not ptype:
                pn, pc = self.callMethod('getPropertyName', 0, {'prefix': pname + '.'})
                if pn:
                    ptype, pflags, descr = 'group', 0, ''
                else:
                    ptype, pflags, descr = None, None, None
            if ptype:
                propertyInfo[self.objectType][pname] = (ptype, pflags, descr)
        return ptype, pflags, descr
