import cbor2
import numpy as np

class Quaternion(np.ndarray):
    CBOR_TAG = 4294980000

    def __new__(cls, data):
        assert len(data) == 4
        return np.asarray(data, dtype=float).view(cls)

    def __repr__(self):
        return f'sim.Quaternion({self.tolist()})'

    def __cbor__(self):
        return cbor2.CBORTag(Quaternion.CBOR_TAG, self.ravel(order='C').tolist())

    @staticmethod
    def fromcbor(tag: cbor2.CBORTag):
        if tag.tag == Quaternion.CBOR_TAG and len(tag.value) == 4:
            return np.array(tag.value, dtype=np.float64).view(Quaternion)
