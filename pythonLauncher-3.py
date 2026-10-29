def __main():
    global __main
    del __main

    import json, sys
    __args = json.loads(sys.stdin.read())
    sys.path.insert(0, __args["pythonPath"])

    _globals = globals()
    import sim
    from sim.zmqremoteapi import PythonWrapper
    __pythonWrapper = PythonWrapper(_globals, **__args)
    _globals["print"] = __pythonWrapper.rapi.print
    __pythonWrapper.registerCmdInterface()
    exec(compile(__args["userCode"], "coppeliaSim script", "exec"), _globals)
    __pythonWrapper.registerSysCalls()
    import inspect
    if inspect.iscoroutinefunction(f := _globals.get('sysCall_thread')):
        t = __pythonWrapper.registerThread(f)
        sim.step = t.step
        sim.sleep = t.sim_sleep
    __pythonWrapper.spin()


if __name__ == '__main__':
    __main()
