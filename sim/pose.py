import cbor2
import numpy as np

class Pose(np.ndarray):
    CBOR_TAG = 4294980500

    def __new__(cls, data):
        assert len(data) == 7
        return np.asarray(data, dtype=float).view(cls)

    def __repr__(self):
        return f'sim.Pose({self.tolist()})'

    def __cbor__(self):
        return cbor2.CBORTag(Pose.CBOR_TAG, self.ravel(order='C').tolist())

    @staticmethod
    def fromcbor(tag: cbor2.CBORTag):
        if tag.tag == Pose.CBOR_TAG and len(tag.value) == 7:
            return np.array(tag.value, dtype=np.float64).view(Pose)
