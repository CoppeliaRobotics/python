import sys
import cbor
import zmq
import os

context = zmq.Context()
socket = context.socket(zmq.REP)
socket.bind(sys.argv[1])
module = {}
while True:
    # in: cmd + (code or func+args), out: ret or err
    req = cbor.loads(socket.recv())
    rep = {}
    if req['cmd'] == 'loadCode':
        try:
            s = req['info'] + "_" + str(os.getpid()) + ".py"
            if sys.platform.startswith('win'):
                s = "z:\\" + s
            else:
                s = "//" + s
            code = compile(req['code'], s, "exec") #__EXCEPTION__
            exec(code,module) #__EXCEPTION__
            rep = {'ret': s}
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
