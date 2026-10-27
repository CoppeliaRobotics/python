import sim

def sysCall_init():
    sim.app.logInfo("Python sandbox initialized")

    global app, scene, self
    app, scene, self = sim.app, sim.scene, sim.self
