from .propertygroup import PropertyGroup
from .object import Object
from .objectarray import ObjectArray
from . import const as sim

import cbor2
import numpy as np


class Color(np.ndarray):
    CBOR_TAG = 4294970000

    def __cbor__(self):
        return cbor2.CBORTag(Color.CBOR_TAG, self.ravel(order='C').tolist())

    @staticmethod
    def fromcbor(tag: cbor2.CBORTag):
        if tag.tag == Color.CBOR_TAG:
            return np.array(tag.value, dtype=np.float64).view(Color)


class Matrix(np.ndarray):
    CBOR_TAG = 40

    def __cbor__(self):
        return cbor2.CBORTag(Matrix.CBOR_TAG, [self.shape, self.ravel(order='C').tolist()])

    @staticmethod
    def fromcbor(tag: cbor2.CBORTag):
        if tag.tag == Matrix.CBOR_TAG:
            dims, data = tag.value
            arr = np.array(data, dtype=np.float64)
            return arr.reshape(dims, order='C').view(Matrix)


class Quaternion(np.ndarray):
    CBOR_TAG = 4294980000

    def __cbor__(self):
        return cbor2.CBORTag(Quaternion.CBOR_TAG, self.ravel(order='C').tolist())

    @staticmethod
    def fromcbor(tag: cbor2.CBORTag):
        if tag.tag == Quaternion.CBOR_TAG and len(tag.value) == 4:
            return np.array(tag.value, dtype=np.float64).view(Quaternion)


class Pose(np.ndarray):
    CBOR_TAG = 4294980500

    def __cbor__(self):
        return cbor2.CBORTag(Pose.CBOR_TAG, self.ravel(order='C').tolist())

    @staticmethod
    def fromcbor(tag: cbor2.CBORTag):
        if tag.tag == Pose.CBOR_TAG and len(tag.value) == 7:
            return np.array(tag.value, dtype=np.float64).view(Pose)


app = Object(sim.handle_app)
scene = Object(sim.handle_scene)
self = Object(sim.handle_self)

__all__ = ['PropertyGroup', 'Object', 'ObjectArray', 'Color', 'Matrix', 'Quaternion', 'Pose', 'app', 'scene', 'self']
