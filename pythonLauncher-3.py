import os


# Third-party packages required by the `sim` module (pip name, import name).
REQUIRED_PACKAGES = (
    ('pyzmq', 'zmq'),
    ('cbor2', 'cbor2'),
    ('numpy', 'numpy'),
)

# Prefix of the one-line message the Lua wrapper recognises (so it can report it
# as a clean error instead of "The Python interpreter terminated with exit code
# ..."). Keep in sync with pythonWrapper-3.lua.
_MISSING_PACKAGES_MARKER = '[missing-python-packages]'


def _processAlive(pid: int) -> bool:
    """
    Best-effort check whether a process with that pid still exists.
    """
    if pid <= 0:
        return True
    if os.name == 'nt':
        import ctypes
        SYNCHRONIZE = 0x00100000
        h = ctypes.windll.kernel32.OpenProcess(SYNCHRONIZE, False, pid)
        if not h:
            return False
        try:
            # WAIT_OBJECT_0 (0) means the process has exited
            return ctypes.windll.kernel32.WaitForSingleObject(h, 0) != 0
        finally:
            ctypes.windll.kernel32.CloseHandle(h)
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def _simPidFromArgv(argv) -> int | None:
    """
    The wrapper passes the simulator's pid as a decoration argument
    ('coppeliaSim.pid=<pid>'); the actual configuration comes via stdin.
    """
    for a in argv:
        if a.startswith('coppeliaSim.pid='):
            try:
                return int(a.split('=', 1)[1])
            except ValueError:
                pass
    return None


def _watchSimulatorProcess(pid: int, checkInterval: float = 1.0) -> None:
    """
    Quits this process when the simulator that spawned it disappears.

    This is the watchdog for the case where the application dies without running
    the script cleanup (crash, force quit): the Lua side then cannot kill this
    subprocess any more. A silence-based watchdog cannot be used instead, because
    the simulator may legitimately stay silent for a long time (popup menu, modal
    dialog, edit mode).
    """
    import time
    while True:
        time.sleep(checkInterval)
        if not _processAlive(pid):
            os._exit(0)


def _formatPackageList(names) -> str:
    if len(names) == 1:
        return names[0]
    return ', '.join(names[:-1]) + ' and ' + names[-1]


def _reportPackageProblem(msg: str) -> None:
    import sys
    print(_MISSING_PACKAGES_MARKER + ' ' + msg, file=sys.stderr, flush=True)
    sys.exit(42)


def _missingPackages() -> list:
    """
    Returns the pip names of the required packages that are not importable,
    without importing them (cheap check based on the module specs).
    """
    import importlib.util
    missing = []
    for pipName, importName in REQUIRED_PACKAGES:
        try:
            found = importlib.util.find_spec(importName) is not None
        except (ImportError, ValueError, AttributeError):
            found = False
        if not found:
            missing.append(pipName)
    return missing


def _checkRequiredPackages() -> None:
    """
    Reports missing required packages with a clear message instead of letting a
    cryptic ImportError traceback (plus "terminated with exit code 1") surface.
    """
    import sys
    missing = _missingPackages()
    if missing:
        exe = sys.executable
        _reportPackageProblem(
            f'detected some missing Python packages: {_formatPackageList(missing)} '
            f'are required, make sure to install them for {exe!r} '
            f'(e.g. "{exe}" -m pip install {" ".join(missing)})')


def __main():
    global __main
    del __main

    import json, sys
    __args = json.loads(sys.stdin.read())

    # Watch the simulator process (passed by the wrapper as a decoration argument)
    # so that this process does not linger when the application dies abruptly.
    __simPid = _simPidFromArgv(sys.argv[1:])
    if __simPid:
        import threading
        threading.Thread(target=_watchSimulatorProcess, args=(__simPid,), daemon=True).start()

    sys.path.insert(0, __args["pythonPath"])
    # 'include <file>' in an embedded script: import from the included file's folder
    for __p in (__args.get("additionalPaths") or []):
        if __p and __p not in sys.path:
            sys.path.append(__p)

    _globals = globals()
    _checkRequiredPackages()
    try:
        import sim
        from sim.zmqremoteapi import PythonWrapper
    except ImportError as e:
        _reportPackageProblem(
            f'failed to import the sim module or one of its dependencies for '
            f'{sys.executable!r}: {e}')
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
