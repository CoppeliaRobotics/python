#python

#luaExec require('sandboxCommon')

def sysCall_init():
    sim = require('sim')
    sim.addLog(sim.verbosity_msgs, "Simulator launched, welcome!")
    self.m = False
    self.restart = False

def sysCall_cleanup():
    sim.addLog(sim.verbosity_msgs, "Leaving...")

def sysCall_beforeSimulation():
    sim.addLog(sim.verbosity_msgs, "Simulation started.")

def sysCall_afterSimulation():
    sim.addLog(sim.verbosity_msgs, "Simulation stopped.")
    self.m = False

def sysCall_sensing():
    s = sim.getSimulationState()
    if s == sim.simulation_advancing_abouttostop and not self.m:
        sim.addLog(sim.verbosity_msgs, "simulation stopping...")
        self.m = True

def sysCall_suspend():
    sim.addLog(sim.verbosity_msgs, "Simulation suspended.")

def sysCall_resume():
    sim.addLog(sim.verbosity_msgs, "Simulation resumed.")

def restart():
    self.restart = True

def sysCall_nonSimulation():
    if self.restart:
        return {'cmd': 'restart'}

def sysCall_actuation():
    if self.restart:
        return {'cmd': 'restart'}

def sysCall_suspended():
    if self.restart:
        return {'cmd': 'restart'}
