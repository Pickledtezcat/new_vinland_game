import bge
import mathutils


class UserInterface(object):
    def __init__(self, level):

        self.level = level
        self.manager = self.level.manager
        self.cursor = self.manager.own.scene.addObject("movement_cursor", self.manager.own, 0)
        self.cursor.setParent(self.manager.main_camera)
        self.bounding_box = self.manager.own.scene.addObject("bounding_box", self.manager.own, 0)
        self.cursor.setParent(self.manager.main_camera)

    def terminate(self):
        self.cursor.endObject()
        self.bounding_box.endObject()

    def set_bounding_box(self, hide, start, end):

        if hide:
            self.bounding_box.visible = False
        else:
            self.bounding_box.visible = True

            x_limit = sorted([start[0], end[0]])
            y_limit = sorted([start[1], end[1]])

            start_hit = self.mouse_ray((x_limit[0], y_limit[0]))
            end_hit = self.mouse_ray((x_limit[1], y_limit[1]))
            corner_hit = self.mouse_ray((x_limit[1], y_limit[0]))

            start_vector = start_hit[1]
            end_vector = end_hit[1]
            corner_vector = corner_hit[1]

            x_length = (corner_vector - start_vector).length
            y_length = (end_vector - corner_vector).length

            self.bounding_box.worldPosition = start_vector
            self.bounding_box.worldOrientation = self.manager.main_camera.worldOrientation
            self.bounding_box.localScale.x = x_length
            self.bounding_box.localScale.y = y_length

    def mouse_ray(self, position):
        x, y = position

        camera = self.manager.main_camera
        screen_vect = camera.getScreenVect(x, y)
        target_position = camera.worldPosition - screen_vect
        mouse_hit = camera.rayCast(target_position, camera, 7.0, "cursor_plane", 0, 1, 0)

        return mouse_hit

    def update(self):

        mouse_hit = self.mouse_ray(self.manager.game_input.virtual_mouse)

        if mouse_hit[0]:

            location = mouse_hit[1]
            normal = mouse_hit[2]

            if self.level.mouse_control.context == "TARGET":
                self.cursor.replaceMesh("target_cursor")
            else:
                self.cursor.replaceMesh("movement_cursor")

            self.cursor.worldPosition = location
            self.cursor.worldOrientation = normal.to_track_quat("Z", "Y")







