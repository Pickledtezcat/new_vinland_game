import bge
import mathutils
import bgeutils
import particles
import agent_states
import agent_actions


class Agent(object):

    size = 0
    max_speed = 0.0
    speed = 0.0
    handling = 0.0
    throttle = 0.0
    throttle_target = 0.0
    turning_speed = 0.01
    damping = 0.1

    stance = "FLANK"

    def __init__(self, level, load_name, location, team, direction=None):

        self.level = level
        self.load_name = load_name
        self.team = team
        self.ended = False

        self.box = self.add_box()
        self.movement_hook = bgeutils.get_ob("hook", self.box.childrenRecursive)
        self.tilt_hook = bgeutils.get_ob("tilt", self.box.childrenRecursive)
        self.recoil_hook = bgeutils.get_ob("recoil", self.box.childrenRecursive)
        self.mesh = bgeutils.get_ob("mesh", self.box.childrenRecursive)
        self.debug_label = particles.DebugLabel(self.level, self)
        self.debug_text = "AGENT"

        self.commands = []

        self.location = location
        self.direction = direction
        if not direction:
            self.direction = [1, 0]
        self.destinations = []
        self.occupied = []

        self.target = None
        self.reverse = False
        self.selected = False

        self.movement = agent_actions.AgentMovement(self)
        self.navigation = agent_actions.Navigation(self)

        self.load_stats()

        self.state = None

        self.set_starting_state()
        self.level.agents.append(self)

    def set_occupied(self):

        x, y = self.location

        for ox in range(self.size):
            for oy in range(self.size):
                tile_key = bgeutils.get_key([x + ox, y + oy])
                self.level.map[tile_key]["occupied"] = self
                self.occupied.append(tile_key)

    def check_occupied(self, target_tile):

        x, y = target_tile
        occupied = []

        for ox in range(self.size):
            for oy in range(self.size):

                tile_key = bgeutils.get_key([x + ox, y + oy])
                tile = self.level.map.get(tile_key)
                if tile:
                    if tile["occupied"]:
                        occupied.append(tile["occupied"])

        return occupied

    def clear_occupied(self):

        for tile_key in self.occupied:
            self.level.map[tile_key]["occupied"] = None
        self.occupied = None

    def add_box(self):
        box = self.level.own.scene.addObject("agent", self.level.own, 0)
        return box

    def terminate(self):
        self.box.endObject()
        self.debug_label.ended = True

    def load_stats(self):

        self.size = 3
        self.max_speed = 0.02
        self.handling = 0.02

    def set_speed(self):
        self.speed = 0.02

    def set_position(self):
        self.movement.initial_position()

    def process_commands(self):

        for command in self.commands:
            if command['LABEL'] == "SELECT":
                if self.team == 0:

                    x_limit = command["X_LIMIT"]
                    y_limit = command["Y_LIMIT"]
                    additive = command["ADDITIVE"]
                    mouse_over = command["MOUSE_OVER"]

                    cam = self.level.manager.main_camera

                    select = False

                    if cam.pointInsideFrustum(self.box.worldPosition):
                        screen_location = cam.getScreenPosition(self.box)
                        padding = 0.03

                        if x_limit[0] - padding < screen_location[0] < x_limit[1] + padding:
                            if y_limit[0] - padding < screen_location[1] < y_limit[1] + padding:
                                select = True

                    if mouse_over == self and additive:
                        self.selected = False

                    elif select:
                        self.selected = True

                    elif not additive:
                        if not select:
                            self.selected = False

            if command["LABEL"] == "MOVEMENT_TARGET":
                position = command["POSITION"]
                reverse = command["REVERSE"]
                additive = command["ADDITIVE"]

                if additive:
                    self.destinations.append(position)
                else:
                    self.destinations = [position]

                if reverse:
                    self.reverse = True
                else:
                    self.reverse = False

        self.commands = []

    def set_starting_state(self):
        self.state = agent_states.VehicleStartUp(self)

    def state_machine(self):
        self.state.update()
        next_state = self.state.transition
        if next_state:
            self.state.end()
            self.state = next_state(self)

    def update(self):
        self.debug_text = self.selected

        self.process_commands()
        if not self.ended:
            if not self.level.paused:
                self.state_machine()



