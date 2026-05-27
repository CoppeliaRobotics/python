from copy import copy
from types import SimpleNamespace

def callMethod(handle, method, *args):
    raise NotImplemented

sim = SimpleNamespace(
    handle_scene = -12,
    handle_app = -13,
    handle_self = -4,
    propertytype_method = 240,
    propertyinfo_removable = 4,
)

propertyInfo = {}  # cache for property info, by objectType


class PropertyGroup:
    def __init__(self, obj, **kwargs):
        super().__setattr__('_object', obj)
        super().__setattr__('_opts', copy(kwargs))
        super().__setattr__('_localProperties', {})

    def __getattr__(self, k):
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
        elif ptype == 'group':
            return PropertyGroup(obj, prefix=k)
        elif ptype:
            v = obj.callMethod('getProperty', k, {'type': ptype})
            # TODO: freeze matrix/quaternion values
            return v
        else:
            raise AttributeError(f"object has no attribute '{k}'")

    def __setattr__(self, k, v):
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

    def __str__(self):
        opts_arg = (', ' + self._opts) if self._opts else ''
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

    def registerLocalProperty(self, k, getter=None, setter=None):
        self._localProperties[k] = {}
        for lpk, f in {'get': getter, 'set': setter}.items():
            self._localProperties[k][lpk] = f


class Object:
    def __init__(self, handle):
        if isinstance(handle, Object):
            handle = handle.handle
        assert isinstance(handle, int)
        super().__setattr__('_handle', handle)
        super().__setattr__('_properties', None)

    def _setupPropertyGroups(self):
        if self._properties: return

        if self._handle == sim.handle_self:
            super().__setattr__('_handle', callMethod(self._handle, 'getLongProperty', 'handle'))

        handle = self._handle

        super().__setattr__('_properties', PropertyGroup(self))

        self._properties.registerLocalProperty('handle', lambda: self._handle)

        # TODO: add _methods local property

        objectType = self.callMethod('getStringProperty', 'objectType')
        super().__setattr__('objectType', objectType)

        namespaces = self.callMethod('getStringArrayProperty', 'metaInfo.namespaces')
        for ns in namespaces:
            super().__setattr__(ns, PropertyGroup(handle, prefix=ns))

    def __getattr__(self, k):
        assert isinstance(k, str)

        self._setupPropertyGroups()

        attr = getattr(super(), k, None)
        if attr is not None:
            return attr

        return self._properties.__getattr__(k)

    def __setattr__(self, k, v):
        assert isinstance(k, str)

        self._setupPropertyGroups()

        self._properties.__setattr__(k, v)

    def __str__(self):
        return f'sim.Object({self._handle})'

    def __dir__(self):
        return dir(self._properties)

    @property
    def handle(self):
        self._setupPropertyGroups()

        return self._handle

    def callMethod(self, m, *args):
        return callMethod(self._handle, m, *args)

    def isValid(self):
        return callMethod(self._handle, 'isValid')

    def getPropertyInfo(self, pname, opts=None):
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


app = Object(sim.handle_app)
scene = Object(sim.handle_scene)
self = Object(sim.handle_self)

__all__ = ['PropertyGroup', 'Object', 'app', 'scene', 'self']
