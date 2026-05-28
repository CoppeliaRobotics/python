from .propertygroup import PropertyGroup
from .object import Object
from . import const as sim

app = Object(sim.handle_app)
scene = Object(sim.handle_scene)
self = Object(sim.handle_self)

__all__ = ['PropertyGroup', 'Object', 'app', 'scene', 'self']
