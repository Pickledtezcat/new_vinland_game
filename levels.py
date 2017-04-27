import bge
import user_interface
import bgeutils
import agents


class SelectionBox(object):

    def __init__(self, level):
        self.level = level
        self.start = None
        self.end = None
        self.additive = False

    def update(self):

        select = "left_drag" in self.level.manager.game_input.buttons
        additive = "shift" in self.level.manager.game_input.keys
        #

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
        self.own = manager.own
        self.user_interface = user_interface.UserInterface(manager)
        self.selection_box = SelectionBox(self)

        self.map = self.get_map()
        self.agents = []

        self.add_agents()

    def get_map(self):

        map = {}
        for x in range(50):
            for y in range(50):
                target_position = [x, y, -10.0]
                origin = [x, y, 10.0]

                ray = self.own.rayCast(target_position, origin, 0.0, "ground", 1, 1, 0)
                if ray[0]:
                    tile = {"occupied": False, "height": ray[1][2], "normal": list(ray[2])}

                    map[bgeutils.get_key((x, y))] = tile

        return map

    def terminate(self):
        self.user_interface.terminate()

    def add_agents(self):
        agents.Agent(self, None, [45, 45], 0)

    def mouse_update(self):
        self.selection_box.update()

    def update(self):
        self.mouse_update()
        self.user_interface.update()
