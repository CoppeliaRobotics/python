"""
CBOR encoding/decoding for the CoppeliaSim Python API.

Public interface
----------------
    Tags.Array.*      CBOR tags for raw typed numpy arrays (from the C++ bridge)
    Tags.Sim.*        CBOR tags for CoppeliaSim high-level types (Matrix, …)
    encode(obj, *, extra_hooks=None) -> bytes
    decode(data, *, extra_hooks=None) -> Any

`extra_hooks` is *combined* with the handlers provided by this module
(user hooks take precedence).  See `encode` / `decode` docstrings.
"""

import cbor2
import numpy as np
from typing import Any, Callable, Dict, Optional

import sim


# ---------------------------------------------------------------------------
# Tag constants
# ---------------------------------------------------------------------------

class _SimTagsMeta(type):
    """Lazily resolve CoppeliaSim high-level type tags.

    `Tags.Sim.Matrix` returns `sim.Matrix.CBOR_TAG`, etc.  Doing this lazily
    allows this module to be imported before the sim classes have finished
    being defined in `sim/__init__.py`.
    """
    _NAMES = frozenset({'Matrix', 'Object', 'ObjectArray',
                        'Color', 'Quaternion', 'Pose'})

    def __getattr__(cls, name: str) -> int:
        if name in cls._NAMES:
            return getattr(sim, name).CBOR_TAG
        raise AttributeError(name)


class Tags:
    class Array:
        """Tags for raw typed arrays (RFC8746 typed-arrays)."""
        U8      = 64
        U16BE   = 65
        U32BE   = 66
        U64BE   = 67
        U8C     = 68
        U16LE   = 69
        U32LE   = 70
        U64LE   = 71
        S8      = 72
        S16BE   = 73
        S32BE   = 74
        S64BE   = 75
        S16LE   = 77
        S32LE   = 78
        S64LE   = 79
        F16BE   = 80
        F32BE   = 81
        F64BE   = 82
        F128BE  = 83
        F16LE   = 84
        F32LE   = 85
        F64LE   = 86
        F128LE  = 87

    class Sim(metaclass=_SimTagsMeta):
        """Tags for CoppeliaSim property types."""
        pass


_TAG_TO_DTYPE: Dict[int, np.dtype] = {
    Tags.Array.U8:     np.dtype("u1"),
    Tags.Array.U16BE:  np.dtype(">u2"),
    Tags.Array.U32BE:  np.dtype(">u4"),
    Tags.Array.U64BE:  np.dtype(">u8"),
    Tags.Array.U8C:    np.dtype("u1"),  # same as U8, often char buffer
    Tags.Array.U16LE:  np.dtype("<u2"),
    Tags.Array.U32LE:  np.dtype("<u4"),
    Tags.Array.U64LE:  np.dtype("<u8"),
    Tags.Array.S8:     np.dtype("i1"),
    Tags.Array.S16BE:  np.dtype(">i2"),
    Tags.Array.S32BE:  np.dtype(">i4"),
    Tags.Array.S64BE:  np.dtype(">i8"),
    Tags.Array.S16LE:  np.dtype("<i2"),
    Tags.Array.S32LE:  np.dtype("<i4"),
    Tags.Array.S64LE:  np.dtype("<i8"),
    Tags.Array.F16BE:  np.dtype(">f2"),
    Tags.Array.F32BE:  np.dtype(">f4"),
    Tags.Array.F64BE:  np.dtype(">f8"),
    #Tags.Array.F128BE: np.dtype(">f16"),  # may not be supported everywhere
    Tags.Array.F16LE:  np.dtype("<f2"),
    Tags.Array.F32LE:  np.dtype("<f4"),
    Tags.Array.F64LE:  np.dtype("<f8"),
    #Tags.Array.F128LE: np.dtype("<f16"),  # platform dependent
}


# ---------------------------------------------------------------------------
# Built-in encoders / default / tag hook
# ---------------------------------------------------------------------------

def _sim_encoders() -> Dict[type, Callable]:
    return {
        sim.Object:      lambda e, v: e.encode(v.__cbor__()),
        sim.ObjectArray: lambda e, v: e.encode(v.__cbor__()),
        sim.Color:       lambda e, v: e.encode(v.__cbor__()),
        sim.Matrix:      lambda e, v: e.encode(v.__cbor__()),
        sim.Quaternion:  lambda e, v: e.encode(v.__cbor__()),
        sim.Pose:        lambda e, v: e.encode(v.__cbor__()),
        np.ndarray:      lambda e, v: e.encode(v.view(sim.Matrix).__cbor__()),
    }


def _default_encode(encoder: cbor2.CBOREncoder, value: Any) -> None:
    raise cbor2.CBOREncodeTypeError(f'cannot serialize type {type(value)}')


def _decode_tag(tag: cbor2.CBORTag, immutable: bool) -> Any:
    """Built-in tag hook (numpy array tags + sim type tags)."""
    if tag.tag == Tags.Sim.Matrix:
        return sim.Matrix.fromcbor(tag)
    if tag.tag in _TAG_TO_DTYPE:
        dtype = _TAG_TO_DTYPE[tag.tag]
        payload = tag.value
        if isinstance(payload, memoryview):
            payload = payload.tobytes()
        elif isinstance(payload, list):
            payload = bytes(payload)
        return np.frombuffer(payload, dtype=dtype)
    if tag.tag == Tags.Sim.Object:
        return sim.Object.fromcbor(tag)
    if tag.tag == Tags.Sim.ObjectArray:
        return sim.ObjectArray.fromcbor(tag)
    if tag.tag == Tags.Sim.Color:
        return sim.Color.fromcbor(tag)
    if tag.tag == Tags.Sim.Quaternion:
        return sim.Quaternion.fromcbor(tag)
    if tag.tag == Tags.Sim.Pose:
        return sim.Pose.fromcbor(tag)
    return tag


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def encode(obj: Any, *, extra_hooks=None) -> bytes:
    """
    Encode `obj` as CBOR bytes.

    The built-in encoders handle the CoppeliaSim types (Matrix, Object, …)
    and numpy arrays.

    `extra_hooks` is combined with the built-in handlers and consulted
    **before** them.  It may be:

      * a callable `(encoder, value) -> None`, used as the fallback `default`
        handler.  It should call `encoder.encode(...)` or raise
        `cbor2.CBOREncodeTypeError` to fall through to the built-in default
        (which raises).  This is what `ZMQRemoteAPI` uses to serialize
        arbitrary callables.

      * a dict that may contain:
            - Python *type* keys  -> `callable(encoder, value)`
              (merged with / overrides the built-in encoders)
            - the key `'default'` -> `callable(encoder, value)`
              (chained before the built-in default)
    """
    encoders = _sim_encoders()
    default: Callable[[cbor2.CBOREncoder, Any], None] = _default_encode

    if extra_hooks is not None:
        if callable(extra_hooks):
            _user_default = extra_hooks
            def default(encoder, value):  # noqa: F811
                try:
                    _user_default(encoder, value)
                except cbor2.CBOREncodeTypeError:
                    _default_encode(encoder, value)
        elif isinstance(extra_hooks, dict):
            for k, v in extra_hooks.items():
                if k == 'default':
                    _user_default = v
                    _prev = default
                    def default(encoder, value, _prev=_prev, _user=_user_default):  # noqa: F811
                        try:
                            _user(encoder, value)
                        except cbor2.CBOREncodeTypeError:
                            _prev(encoder, value)
                elif isinstance(k, type):
                    encoders[k] = v
                else:
                    raise TypeError(f'invalid extra_hooks key: {k!r}')
        else:
            raise TypeError('extra_hooks must be callable or dict')

    return cbor2.dumps(obj, encoders=encoders, default=default)


def decode(data: bytes, *, extra_hooks: Optional[Dict[int, Callable[[cbor2.CBORTag, bool], Any]]] = None) -> Any:
    """
    Decode CBOR-encoded `data`.

    `extra_hooks`, when provided, is a dict mapping a CBOR tag (int) to a
    callable `(tag, immutable) -> value`.  These are consulted **before**
    the built-in tag hook, so callers can both extend and override it.
    """
    if extra_hooks:
        def tag_hook(tag: cbor2.CBORTag, immutable: bool) -> Any:
            handler = extra_hooks.get(tag.tag)
            if handler is not None:
                return handler(tag, immutable)
            return _decode_tag(tag, immutable)
    else:
        tag_hook = _decode_tag

    return cbor2.loads(data, tag_hook=tag_hook)
