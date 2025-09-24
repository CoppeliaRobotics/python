import sys
import psutil
import zmq
import sys


try:
    import cbor2 as cbor
except ModuleNotFoundError:
    import cbor

context = zmq.Context()
socket = context.socket(zmq.REP)
socket.bind(sys.argv[1])
socket.setsockopt(zmq.RCVTIMEO, 1000)
PID = int(sys.argv[2])
module = {}

def isCoppeliaSimAlive():
    try:
        proc = psutil.Process(PID)
        if proc.is_running() and proc.status() != psutil.STATUS_ZOMBIE and proc.name() == 'coppeliaSim':
            return True
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        pass
    return False    

while True:
    try:
        # in: cmd + (code or func+args), out: ret or err
        raw = socket.recv()
        req = cbor.loads(raw)
        rep = {}
        if req['cmd'] == 'loadCode':
            try:
                code = compile(req['code'], req['info'], "exec") #__EXCEPTION__
                exec(code,module) #__EXCEPTION__
                rep = {'ret': None}
            except Exception as e:
                import traceback
                rep = {'err': traceback.format_exc()}
        elif req['cmd'] == 'callFunc':
            try:
                func = module[req['func']]
                rep = {'ret': func(*req['args'])} #__EXCEPTION__
            except Exception as e:
                import traceback
                rep = {'err': traceback.format_exc()}
        else:
            rep = {'err': f'unknown command: "{req["cmd"]}"'}
        socket.send(cbor.dumps(rep))
    except zmq.Again:
        if isCoppeliaSimAlive():
            continue
