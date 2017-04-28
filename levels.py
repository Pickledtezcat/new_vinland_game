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

        if select:
            if not self.start:
                self.start = self.level.manager.game_input.virtual_mouse.copy()

            self.end = self.level.manager.game_input.virtual_mouse.copy()
            self.level.user_interface.set_bounding_box(False, self.start, self.end)

        else:
            if self.start:
                additive = "shift" in self.level.manager.game_input.keys
                x_limit = sorted([self.start[0], self.end[0]])
                y_limit = sorted([self.start[1], self.end[1]])

                message = {"LABEL": "SELECT", "X_LIMIT": x_limit, "Y_LIMIT": y_limit, "ADDITIVE": additive}
                for agent in self.level.agents:
                    agent.commands.append(message)

                self.start = None
                self.end = None

            self.level.user_interface.set_bounding_box(True, None, None)


class Level(object):

    def __init__(self, manager):
        self.manager = manager
        self.own = manager.own
        self.user_interface = user_interface.UserInterface(manager)
        self.selection_box = SelectionBox(self)

        self.map = self.get_map()
        self.agents = []
        self.particles = []

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

    def particle_update(self):
        next_generation = []

        for particle in self.particles:
            if not particle.ended:
                particle.update()
                next_generation.append(particle)
            else:
                particle.terminate()

        self.particles = next_generation

    def agent_update(self):

        next_generation = []

        for agent in self.agents:
            if not agent.ended:
                agent.update()
                next_generation.append(agent)
            else:
                agent.terminate()

        self.agents = next_generation

    def update(self):
        self.mouse_update()
        self.user_interface.update()
        self.agent_update()
        self.particle_update()
