from copy import copy
from types import SimpleNamespace
from typing import Any, Callable
from typing import TYPE_CHECKING

from . import const as sim

if TYPE_CHECKING:
    from .object import Object


class PropertyGroup:
    def __init__(self, obj: Object, **kwargs: Any):
        super().__setattr__('_object', obj)
        super().__setattr__('_opts', copy(kwargs))
        super().__setattr__('_localProperties', {})

    def __getattr__(self, k: str) -> Any:
        assert isinstance(k, str)

        if k in self._localProperties:
            assert 'get' in self._localProperties[k], f"local property {k} can't be read"
            if getter := self._localProperties[k]['get']:
                return getter()

        prefix = self._opts.get('prefix', '')
        if prefix != '':
            k = prefix + '.' + k

        obj = self._object
        ptype, pflags, descr = obj.getPropertyInfo(k, {'noError': True})
        if ptype == sim.propertytype_method:
            return lambda *args: obj.callMethod(k, *args)
        elif ptype == sim.propertytype_group:
            return PropertyGroup(obj, prefix=k)
        elif ptype:
            v = obj.callMethod('getProperty', k, {'type': ptype})
            # TODO: freeze matrix/quaternion values
            return v
        else:
            raise AttributeError(f"object has no attribute '{k}'")

    def __setattr__(self, k: str, v: Any) -> None:
        assert isinstance(k, str)

        if k in self._localProperties:
            assert 'set' in self._localProperties[k], f"local property {k} can't be written"
            if setter := self._localProperties[k]['set']:
                return setter(v)

        prefix = self._opts.get('prefix', '')
        if prefix != '':
            k = prefix + '.' + k

        obj = self._object
        obj.callMethod('setProperty', k, v, type=self._opts.get('newPropertyForcedType'))

    def __str__(self) -> str:
        opts_arg = (', ' + str(self._opts)) if self._opts else ''
        return f'sim.PropertyGroup({self._object.handle}{opts_arg})'

    r'''
    def __dir__(self):
        prefix = self._opts.get('prefix', '')
        if prefix != '':
            prefix += '.'
        props = {}
        for i in range(100000):
            pname, pclass = self.getPropertyName(i, {'prefix': prefix})
            if not pname: break
            pname = pname[len(prefix):]
            import re
            pname2 = re.sub(r'\..*', '', pname)
            if pname == pname2:
                ptype, pflags, descr = self.getPropertyInfo(prefix + pname)
                if readable := ((pflags & 2) == 0):
                    try:
                        props[pname2] = self.getProperty(prefix + pname)
                    except Exception as e:
                        raise Exception(f'error reading property {pname} ({pflags=}): {e}')
                elif pname2 not in props:
                    props[pname2] = PropertyGroup(self._object, prefix=(prefix + pname))
        return props.keys()
    '''

    def registerLocalProperty(
            self,
            k: str,
            getter: Callable[[], Any] | None = None,
            setter: Callable[[Any], None] | None = None,
    ) -> None:
        self._localProperties[k] = {}
        for lpk, f in {'get': getter, 'set': setter}.items():
            self._localProperties[k][lpk] = f
