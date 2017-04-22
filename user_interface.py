import bge


class UserInterface(object):
    def __init__(self, manager):

        self.manager = manager
        self.cursor = self.manager.own.scene.addObject("cursor", self.manager.own, 0)
        self.cursor.setParent(self.manager.main_camera)

    def terminate(self):
        self.cursor.endObject()

    def update(self):

        x, y = self.manager.game_input.virtual_mouse

        camera = self.manager.main_camera
        screen_vect = camera.getScreenVect(x, y)
        target_position = camera.worldPosition - screen_vect
        mouse_hit = camera.rayCast(target_position, camera, 7.0, "cursor_plane", 0, 1, 0)

        if mouse_hit[0]:

            location = mouse_hit[1]
            normal = mouse_hit[2]

            self.cursor.worldPosition = location
            self.cursor.worldOrientation = normal.to_track_quat("Z", "Y")







