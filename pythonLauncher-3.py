def __main():
    global __main
    del __main

    import json, sys
    __args = json.loads(sys.stdin.read())
    sys.path.insert(0, __args["pythonPath"])
    # 'include <file>' in an embedded script: import from the included file's folder
    for __p in (__args.get("additionalPaths") or []):
        if __p and __p not in sys.path:
            sys.path.append(__p)

    _globals = globals()
    import sim
    from sim.zmqremoteapi import PythonWrapper
    __pythonWrapper = PythonWrapper(_globals, **__args)
    _globals["print"] = __pythonWrapper.rapi.print
    # Expose the RPC object: it lets the script call Lua functions as plain
    # callables (rapi.call(None, 'func', ...)), which - unlike
    # sim.self.callFunction() - runs them in the thread coroutine where
    # sim.self:step()/yield() can actually suspend and resume.
    _globals["rapi"] = __pythonWrapper.rapi
    __pythonWrapper.registerCmdInterface()
    exec(compile(__args["userCode"], "coppeliaSim script", "exec"), _globals)
    __pythonWrapper.registerSysCalls()
    # Thread suspension is handled on the Lua side (Lua's thread coroutine is
    # suspended/resumed, Python just waits for the reply): sysCall_thread is a
    # plain function and step()/sleep() are regular blocking calls.
    sim.step = __pythonWrapper.step
    sim.sleep = __pythonWrapper.sleep
    __pythonWrapper.spin()


if __name__ == '__main__':
    __main()
