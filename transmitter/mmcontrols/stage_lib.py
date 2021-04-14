from pycromanager import Bridge

class StageLib:
    def __init__(self, stageDevice):
        bridge = Bridge()
        self.mmc = bridge.get_core()
        self.mmc.set_xy_stage_device(stageDevice)

    def waitForDevice(self, deviceLabel):
        busy = True
        while busy:
            if not self.mmc.device_busy(deviceLabel):
                busy = False

    def getCurrentPosition(self):
        if self.mmc.get_xy_stage_device():
            return self.mmc.get_xy_stage_position()
        return None

    # dxdy = Relative displacement [x,y]
    def moveStageRelative(self, dxdy):
        dx = dxdy[0]
        dy = dxdy[1]
        if self.mmc.get_xy_stage_device():
            self.mmc.set_relative_xy_position(dx, dy)
            self.waitForDevice(self.mmc.get_xy_stage_device())
            return "" #TODO - SHOULD RETURN SOMETHING COOL AND EPIC

    def moveStageAbsolute(self, xy):
        x = xy[0]
        y = xy[1]
        if self.mmc.get_xy_stage_device():
            self.mmc.set_xy_position(x, y)
            self.waitForDevice(self.mmc.get_xy_stage_device())
            return "" #TODO - SHOULD RETURN SOMETHING COOL AND EPIC