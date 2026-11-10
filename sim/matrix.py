import cbor2
import numpy as np


class Matrix(np.ndarray):
    CBOR_TAG = 40  # RFC8746 multi-dimensional array tag

    def __new__(cls, *args, dtype=float):
        if len(args) == 1:
            # Matrix(data)  — anything np.asarray understands
            arr = np.asarray(args[0], dtype=dtype)
        elif len(args) == 3:
            # Matrix(rows, cols, flatDataRowMajor)
            rows, cols, flat = args
            arr = np.asarray(flat, dtype=dtype).reshape(rows, cols, order='C')
        else:
            raise TypeError(
                f'Matrix() takes 1 or 3 positional arguments '
                f'(data | rows, cols, flatDataRowMajor); got {len(args)}'
            )
        return arr.view(cls)

    def __repr__(self):
        return np.ndarray.__repr__(self)

    # Without this, `print(m)` / `str(m)` uses numpy's plain array formatting
    # ("[]" or a bare list of numbers), while `m` inside a tuple/list container
    # is printed with repr() ("Matrix([], shape=(3, 0), dtype=float64)").
    __str__ = __repr__

    def __cbor__(self):
        return cbor2.CBORTag(Matrix.CBOR_TAG, [self.shape, self.ravel(order='C').tolist()])

    @staticmethod
    def fromcbor(tag: cbor2.CBORTag):
        if tag.tag != Matrix.CBOR_TAG:
            raise ValueError(
                f'unexpected CBOR tag {tag.tag} (expected the matrix tag {Matrix.CBOR_TAG})')
        value = tag.value
        if not isinstance(value, (list, tuple)) or len(value) == 0:
            raise ValueError(f'invalid CBOR matrix payload: {value!r}')
        dims = value[0]
        if not isinstance(dims, (list, tuple)) or len(dims) != 2:
            raise ValueError(f'invalid CBOR matrix dimensions: {dims!r}')
        rows, cols = int(dims[0]), int(dims[1])
        # An empty matrix (0x0, 1x0, 3x0, ... e.g. the ones returned by
        # dynamics.getContacts() when there is no contact) may be encoded with
        # an empty data array, with a null data field, or even without the data
        # field at all; all of those mean "no elements".
        data = value[1] if len(value) > 1 else None
        if data is None:
            data = ()
        arr = np.asarray(data, dtype=np.float64).ravel(order='C')
        if arr.size != rows * cols:
            raise ValueError(
                f'invalid CBOR matrix data: got {arr.size} element(s) for a '
                f'{rows}x{cols} matrix')
        return arr.reshape((rows, cols), order='C').view(Matrix)


def Vector(n: int, data: list[float] | None = None):
    if data is None:
        data = [0.] * n
    return Matrix(n, 1, data)
