import cbor2
import numpy as np

class Color(np.ndarray):
    CBOR_TAG = 4294970000

    def __new__(cls, data):
        assert len(data) == 3
        return np.asarray(data, dtype=float).view(cls)

    def __repr__(self):
        return f'sim.Color({self.ravel().tolist()})'

    def __cbor__(self):
        return cbor2.CBORTag(Color.CBOR_TAG, self.ravel(order='C').tolist())

    @staticmethod
    def fromcbor(tag: cbor2.CBORTag):
        if tag.tag == Color.CBOR_TAG:
            return np.array(tag.value, dtype=np.float64).view(Color)
