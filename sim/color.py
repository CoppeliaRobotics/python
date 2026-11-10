import cbor2
import numpy as np


class Color(np.ndarray):
    """
    RGB color (3 floats in [0, 1]).

    On the wire the Lua side represents a color as tag 4294970000 with a 4-byte
    RGBA8 payload (see sim/Color.lua's Color:__tocbor and sim/cbor.lua's tag
    handler, which decodes the bytes with unpackUInt8Table). The Python API is
    RGB, so alpha is implicitly 1.0 when encoding and dropped when decoding.
    """

    CBOR_TAG = 4294970000

    def __new__(cls, data):
        assert len(data) == 3
        return np.asarray(data, dtype=float).view(cls)

    def __repr__(self):
        return f'sim.Color({self.ravel().tolist()})'

    def __cbor__(self):
        rgb = np.clip(np.asarray(self.ravel(order='C'), dtype=float), 0.0, 1.0)
        r, g, b = (np.rint(rgb * 255.0)).astype(np.uint8).tolist()
        return cbor2.CBORTag(Color.CBOR_TAG, bytes((r, g, b, 255)))

    @staticmethod
    def fromcbor(tag: cbor2.CBORTag):
        if tag.tag != Color.CBOR_TAG:
            return None
        value = tag.value
        if isinstance(value, (bytes, bytearray)) and len(value) >= 3:
            # Lua's RGBA8 payload (4 bytes incl. alpha)
            return np.asarray([c / 255.0 for c in value[:3]], dtype=float).view(Color)
        if isinstance(value, str) and len(value) >= 3:
            # a text-decoded byte string (should cbor2 ever hand us one)
            return np.asarray([ord(c) / 255.0 for c in value[:3]],
                              dtype=float).view(Color)
        # older peers may send a list of (3 or 4) floats
        return np.asarray(list(value)[:3], dtype=float).view(Color)
