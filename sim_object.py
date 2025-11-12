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

        ptype, pflags, descr = sim.getPropertyInfo(self._handle, k)
        if ptype:
            return getattr(sim, sim.getPropertyGetter(ptype, True))(self._handle, k)

        pname, pclass = sim.getPropertyName(self._handle, 0, {'prefix': f'{k}.'})
        if pname:
            return PropertyGroup(self._handle, {'prefix': k})

    def __setattr__(self, k, v):
        assert isinstance(k, str)

        if k in self._localProperties:
            assert 'set' in self._localProperties[k], f"local property {k} can't be written"
            return self._localProperties[k]['set'](v)

        prefix = self._opts.get('prefix', '')
        if prefix != '':
            k = prefix + '.' + k

        ptype, pflags, descr = sim.getPropertyInfo(self._handle, k)
        if 'newPropertyForcedType' in self._opts:
            ptype = self._opts['newPropertyForcedType']
        if ptype:
            return getattr(sim, sim.getPropertySetter(ptype, True))(self._handle, k, v)
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
            pname, pclass = sim.getPropertyName(self._handle, i, {'prefix': prefix})
            if not pname: break
            pname = pname[len(prefix):]
            import re
            pname2 = re.sub(r'\..*', '', pname)
            if pname == pname2:
                ptype, pflags, descr = sim.getPropertyInfo(self._handle, prefix + pname)
                if readable := ((pflags & 2) == 0):
                    try:
                        props[pname2] = getattr(sim, sim.getPropertyGetter(ptype, True))(self._handle, prefix + pname)
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

        import json
        super().__setattr__('_objMetaInfo', json.loads(sim.getStringProperty(self._handle, 'objectMetaInfo')))
        for ns, opts in self._objMetaInfo['namespaces'].items():
            super().__setattr__(ns, PropertyGroup(handle, prefix=ns, **opts))
        super().__setattr__('_methods', self._objMetaInfo['methods'])

    def __getattr__(self, k):
        assert isinstance(k, str)

        if k in self._methods:
            if isinstance(self._methods[k], str):
                mod, *fields = self._methods[k].split('.')
                modName, modVersion = mod, None
                if '-' in mod:
                    modName, modVersion = mod.split('-', 1)
                globals()[modName] = require(mod)
                func = globals()[modName]
                for field in fields:
                    func = getattr(func, field, None)
                    if not func: break
                self._methods[k] = lambda *args: func(self._handle, *args)
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
