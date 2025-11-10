from builtins import require
from copy import copy

sim = require('sim-2')

class PropertyGroup:
    def __init__(self, handle, **kwargs):
        super().__setattr__('_handle', handle)
        super().__setattr__('_opts', copy(kwargs))
        super().__setattr__('_localProperties', {})

    def __getattr__(self, k):
        assert isinstance(k, str)

        if k in self._localProperties:
            assert 'get' in self._localProperties[k], f"local property {k} can't be read"
            return self._localProperties[k]['get']()

        prefix = self._opts.get('prefix', '')
        if prefix != '':
            k = prefix + '.' + k

        if pinfo := sim.getPropertyInfo(self._handle, k):
            ptype, pflags, descr = pinfo
            t = sim.getPropertyTypeString(ptype, True)
            return getattr(sim, f'get{t[0].upper()}{t[1:]}Property')(self._handle, k)

        if sim.getPropertyName(self._handle, 0, {'prefix': f'{k}.'}):
            return PropertyGroup(self._handle, {'prefix': k})

    def __setattr__(self, k, v):
        assert isinstance(k, str)

        if k in self._localProperties:
            assert 'set' in self._localProperties[k], f"local property {k} can't be written"
            return self._localProperties[k]['set'](v)

        prefix = self._opts.get('prefix', '')
        if prefix != '':
            k = prefix + '.' + k

        ptype = sim.getPropertyInfo(self._handle, k)
        if ptype:
            t = sim.getPropertyTypeString(ptype, True)
            return getattr(sim, f'set{t[0].upper()}{t[1:]}Property')(self._handle, k, v)
        else:
            sim.setProperty(self._handle, k, v)

    def __str__(self):
        opts_arg = (', ' + self._opts) if self._opts else ''
        return f'sim.PropertyGroup({self._handle}{opts_arg})'

    def __dir__(self):
        prefix = self._opts.get('prefix', '')
        if prefix != '':
            prefix += '.'
        props = {}
        for i in range(100000):
            if not (pinfo := sim.getPropertyName(self._handle, i, {'prefix': prefix})): break
            pname, pclass = pinfo
            pname = pname[len(prefix):]
            import re
            pname2 = re.sub(r'\..*', '', pname)
            if pname == pname2:
                ptype, pflags, descr = sim.getPropertyInfo(self._handle, prefix + pname)
                if readable := ((pflags & 2) == 0):
                    t = sim.getPropertyTypeString(ptype, True)
                    try:
                        props[pname2] = getattr(sim, f'get{t[0].upper()}{t[1:]}Property')(self._handle, prefix + pname)
                    except Exception as e:
                        raise Exception(f'error reading property {pname} ({pflags=}): {e}')
                elif pname2 not in props:
                    props[pname2] = PropertyGroup(self._handle, prefix=(prefix + pname))
        return props.keys()

    def registerLocalProperty(self, k, getter, setter):
        self._localProperties[k] = {}
        for lpk, f in {'get': getter, 'set': setter}.items():
            self._localProperties[k][lpk] = f

class Object:
    def __init__(self, handle):
        super().__setattr__('_handle', handle)
        super().__setattr__('_methods', {})
        super().__setattr__('_properties', PropertyGroup(handle))

    def __getattr__(self, k):
        assert isinstance(k, str)

        if k in self._methods:
            return self._methods[k]
        else:
            return self._properties.__getattr__(k)

    def __setattr__(self, k, v):
        assert isinstance(k, str)
        self._properties.__setattr__(k, v)

    def __str__(self):
        return f'sim.Object({self._handle})'

    def __dir__(self):
        return dir(self._properties)

    @property
    def handle(self):
        return self._handle
