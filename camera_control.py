import bge
import bgeutils
import mathutils
import math

class CameraControl(object):

    def __init__(self, manager):
        self.manager = manager
        self.main_camera = self.manager.main_camera
        self.camera_hook = self.manager.main_camera.parent
        self.camera_vector = mathutils.Vector([0.0, 0.0, 0.0])

        self.offset = mathutils.Euler((0.0, 0.0, math.radians(45.0)), 'XYZ')

    def update(self):

        mouse_position = self.manager.game_input.virtual_mouse
        x, y = mouse_position

        cam_scroll = x < 0.01 or x > 0.99 or y < 0.01 or y > 0.99

        if cam_scroll:
            mouse_vector = (mathutils.Vector((x, 1.0 - y)) - mathutils.Vector((0.5, 0.5))).to_3d()
            mouse_vector.length = 0.02

            mouse_vector.rotate(self.offset)

            self.camera_vector += mouse_vector
            self.camera_vector.length = min(0.3, self.camera_vector.length)
        else:
            self.camera_vector.length = bgeutils.interpolate_float(self.camera_vector.length, 0.0, 0.1)

        self.camera_hook.worldPosition += self.camera_vector
        self.manager.debugger.printer(self.camera_vector.to_tuple(3), "cam_vec")




