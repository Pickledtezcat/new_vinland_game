import bge
import camera_control
import game_input
import levels
import bgeutils


class DebugPrinter(object):
    def __init__(self, manager):
        self.manager = manager
        self.debug_text = bgeutils.get_ob("debug_text", self.manager.main_camera.children)
        self.debug_text.resolution = 12
        self.debug_list = []

    def update(self):

        debug_text = ""

        for item in self.debug_list:
            debug_text = "{}\n{}".format(item, debug_text)

        self.debug_text["Text"] = debug_text

        self.debug_list = []

    def printer(self, data, label=""):
        info = "{}:{}".format(label, data)

        self.debug_list.append(info)


class GameLoop(object):

    def __init__(self, cont):
        self.cont = cont
        self.own = cont.owner
        self.scene = self.own.scene
        self.main_camera = self.scene.active_camera
        self.debugger = DebugPrinter(self)

        self.camera = camera_control.CameraControl(self)
        self.game_input = game_input.GameInput()
        self.level = levels.Level(self)

    def update(self):
        self.game_input.update()
        self.camera.update()
        self.level.update()
        self.debugger.update()





