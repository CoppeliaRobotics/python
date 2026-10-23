import cbor2
import numpy as np

class Matrix(np.ndarray):
    CBOR_TAG = 40

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

    def __cbor__(self):
        return cbor2.CBORTag(Matrix.CBOR_TAG, [self.shape, self.ravel(order='C').tolist()])

    @staticmethod
    def fromcbor(tag: cbor2.CBORTag):
        if tag.tag == Matrix.CBOR_TAG:
            dims, data = tag.value
            arr = np.array(data, dtype=np.float64)
            return arr.reshape(dims, order='C').view(Matrix)


def Vector(n: int, data: list[float] | None = None):
    if data is None:
        data = [0.] * n
    return Matrix(n, 1, data)
