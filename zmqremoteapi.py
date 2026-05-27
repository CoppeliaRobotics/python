import uuid
import zmq
import cbor2
from typing import Any, Dict, Optional, Tuple, Union, Callable


class ZMQRemoteAPI:
    def __init__(self, opts: Optional[Dict[str, Any]] = None):
        opts = opts or {}
        self.name = opts.get('name')
        self.server = bool(opts.get('server', False))
        self.verbose = opts.get('verbose', 0)
        self.client_id = opts.get('clientID', str(uuid.uuid4()))

        self._context = zmq.Context()
        socket_type = zmq.REP if self.server else zmq.REQ
        self._socket = self._context.socket(socket_type)

        host = opts.get('host', '127.0.0.1')
        port = opts.get('port', 24020)
        if self.server:
            self._socket.bind(f'tcp://*:{port}')
        else:
            self._socket.connect(f'tcp://{host}:{port}')

        self.callables: Dict[str, Callable] = {}

    def cleanup(self) -> None:
        """Close the socket and terminate the ZMQ context."""
        if self._socket:
            self._socket.close()
            self._context.term()
            self._socket = None

    def __del__(self) -> None:
        self.cleanup()

    def log(self, level: int, *args: Any) -> None:
        if level <= self.verbose:
            tag = 'ZMQRemoteAPI'
            if self.name:
                tag += f'[{self.name}]'
            print(tag, *args)

    def call_local(self, func_name: str, args: Tuple[Any, ...]) -> Tuple[Any, ...]:
        func = self.callables.get(func_name)
        if func is None:
            raise NameError(f'No such function: {func_name}')
        if not callable(func):
            raise TypeError(f'Not a callable: {func_name}')
        result = func(*args)
        if not isinstance(result, tuple):
            result = (result,)
        return result

    def call(self, func_name: str, *args: Any) -> Tuple[Any, ...]:
        self.send({'msg': 'call', 'func': func_name, 'args': args})
        while True:
            rep = self.recv(block=True)
            if rep is None:
                continue  # Should not happen with blocking recv

            if rep['msg'] == 'result':
                if rep.get('error', False):
                    raise Exception(rep['result'])
                ret = tuple(rep['result'])
                if len(ret) == 1: return ret[0]
                if len(ret) > 1: return ret
            else:
                self.handle_request(rep)

    def register_callback_local(self, func_name: str) -> None:
        def callback(*args: Any) -> Tuple[Any, ...]:
            return self.call(func_name, *args)
        self.callables[func_name] = callback

    def register_callback(self, func_name: str, func: Callable) -> None:
        self.send({'msg': 'registerCallback', 'func': func_name})
        rep = self.recv(block=True)
        if rep is None:
            raise RuntimeError('No reply from server')
        if rep.get('msg') != 'result':
            raise RuntimeError('Invalid server reply')
        if rep.get('error', False):
            raise RuntimeError(f'registerCallback failed: {rep["result"]}')
        self.callables[func_name] = func

    def handle_request(self, req: Dict[str, Any]) -> None:
        """Process a single incoming request (call or registerCallback)."""
        msg = req.get('msg')
        if not isinstance(msg, str):
            self.log(1, 'malformed request: missing msg')
            return

        if msg == 'call':
            func_name: str = req['func']
            args = req.get('args', ())
            try:
                result = self.call_local(func_name, args)
                error = False
            except Exception as e:
                result = str(e)
                error = True
            self.send({'msg': 'result', 'error': error, 'result': result})

        elif msg == 'registerCallback':
            func_name: str = req['func']
            try:
                self.register_callback_local(func_name)
                error = False
                result = None
            except Exception as e:
                error = True
                result = str(e)
            self.send({'msg': 'result', 'error': error, 'result': result})

        else:
            self.log(1, 'unsupported message:', msg)

    def handle_requests(self) -> None:
        if not self.server:
            raise RuntimeError('handle_requests should be called only from server')
        while True:
            req = self.recv(block=False)
            if req is None:
                break
            self.handle_request(req)

    def send(self, msg: Dict[str, Any]) -> None:
        if not self._socket:
            raise RuntimeError('Socket not available')
        self.log(2, 'sending:', msg)
        data = cbor2.dumps(msg)
        self._socket.send(data)
        self.log(2, 'sent')

    def recv(self, block: bool = True) -> Optional[Dict[str, Any]]:
        if not self._socket:
            raise RuntimeError('Socket not available')
        if block:
            self.log(2, 'receiving... (block)')
            data = self._socket.recv()
        else:
            self.log(2, 'receiving... (non‑block)')
            try:
                data = self._socket.recv(flags=zmq.NOBLOCK)
            except zmq.Again:
                return None
        try:
            req = cbor2.loads(data)
        except Exception as e:
            self.log(1, 'invalid request CBOR data:', e)
            return None
        self.log(2, 'received:', req)
        return req


if __name__ == '__main__':
    def cb(x):
        return rapi.call('test2') + '-CB-' + x

    rapi = ZMQRemoteAPI({'name': 'handshake', 'server': False})
    port = rapi.call('getPort', rapi.client_id)
    rapi = ZMQRemoteAPI({'name': 'client', 'server': False, 'port': port})
    rapi.register_callback('cb', cb)
    result = rapi.call('testWithCallback', 'cb')
    print(result)
