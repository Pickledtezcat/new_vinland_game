import bge
import bgeutils
import mathutils
import math


class CameraControl(object):

    def __init__(self, manager):
        self.manager = manager
        self.main_camera = self.manager.main_camera
        self.camera_hook = self.manager.main_camera.parent
        self.in_zoom = bgeutils.get_ob("in_zoom", self.camera_hook.children).localTransform
        self.out_zoom = bgeutils.get_ob("out_zoom", self.camera_hook.children).localTransform
        self.sun_lamp = bgeutils.get_ob("sun_lamp", self.camera_hook.children)

        self.camera_vector = mathutils.Vector([0.0, 0.0, 0.0])
        self.offset = mathutils.Euler((0.0, 0.0, math.radians(45.0)), 'XYZ')

        self.zoom_in = True
        self.zoom_timer = 1.0

    def zoom(self):

        spot_in = 40.0
        spot_out = 66.0

        if self.zoom_in:
            self.zoom_timer = min(1.0, self.zoom_timer + 0.01)
            step = bgeutils.smoothstep(self.zoom_timer)
            if "wheel_down" in self.manager.game_input.buttons:
                self.zoom_in = False

        else:
            self.zoom_timer = max(0.0, self.zoom_timer - 0.01)
            step = bgeutils.smoothstep(self.zoom_timer)
            if "wheel_up" in self.manager.game_input.buttons:
                self.zoom_in = True

        self.main_camera.localTransform = self.out_zoom.lerp(self.in_zoom, step)
        self.sun_lamp.spotsize = bgeutils.interpolate_float(spot_out, spot_in, step)

    def update(self):
        self.zoom()

        mouse_position = self.manager.game_input.virtual_mouse
        x, y = mouse_position

        cam_scroll = x < 0.01 or x > 0.99 or y < 0.01 or y > 0.99

        if cam_scroll:
            mouse_vector = (mathutils.Vector((x, 1.0 - y)) - mathutils.Vector((0.5, 0.5))).to_3d()
            mouse_vector.length = 0.01

            mouse_vector.rotate(self.offset)

            self.camera_vector += mouse_vector
            self.camera_vector.length = min(0.3, self.camera_vector.length)
        else:
            self.camera_vector.length = bgeutils.interpolate_float(self.camera_vector.length, 0.0, 0.1)

        self.camera_hook.worldPosition += self.camera_vector





