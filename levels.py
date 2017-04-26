import bge
import user_interface


class SelectionBox(object):

    def __init__(self, level):
        self.level = level
        self.start = None
        self.end = None
        self.additive = False

    def update(self):

        select = "left_drag" in self.level.manager.game_input.buttons
        additive = "shift" in self.level.manager.game_input.keys

        if select:
            if not self.start:
                self.start = self.level.manager.game_input.virtual_mouse.copy()

            self.end = self.level.manager.game_input.virtual_mouse.copy()
            self.level.user_interface.set_bounding_box(False, self.start, self.end)

        else:
            if self.start:
                self.start = None

            self.level.user_interface.set_bounding_box(True, None, None)


class Level(object):

    def __init__(self, manager):
        self.manager = manager
        self.user_interface = user_interface.UserInterface(manager)
        self.selection_box = SelectionBox(self)

    def terminate(self):
        self.user_interface.terminate()

    def mouse_update(self):
        self.selection_box.update()

    def update(self):
        self.mouse_update()
        self.user_interface.update()
