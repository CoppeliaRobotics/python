import cbor2
import numpy as np

class Pose(np.ndarray):
    CBOR_TAG = 4294980500

    def __cbor__(self):
        return cbor2.CBORTag(Pose.CBOR_TAG, self.ravel(order='C').tolist())

    @staticmethod
    def fromcbor(tag: cbor2.CBORTag):
        if tag.tag == Pose.CBOR_TAG and len(tag.value) == 7:
            return np.array(tag.value, dtype=np.float64).view(Pose)
