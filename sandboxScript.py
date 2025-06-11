#python

#luaExec require('sandboxScript')

#Python runs just so that we have _evalExec and similar

def sysCall_init():
    sim = require('sim-2')
    sim.addLog(sim.verbosity_warnings, 'sim-2 has been loaded from Python')
