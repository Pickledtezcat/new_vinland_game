import bge
import camera_control
import game_input
import levels
import bgeutils

class GameLoop(object):

    def __init__(self, cont):
        self.cont = cont
        self.own = cont.owner
        self.scene = self.own.scene
        self.main_camera = self.scene.active_camera
        self.debug_text = bgeutils.get_ob("debug_text", self.main_camera.children)
        self.debug_text.resolution = 12

        self.camera = camera_control.CameraControl(self)
        self.game_input = game_input.GameInput()
        self.level = levels.Level(self)

    def update(self):
        self.game_input.update()
        self.camera.update()
        self.level.update()

        pass

    def debug_print(self, message):

        self.debug_text["Text"] = str(message)



