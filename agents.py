import bge
import mathutils
import bgeutils
import particles
from agent_states import *
import agent_actions


class Agent(object):
    size = 0
    max_speed = 0.02
    speed = 0.02
    handling = 0.02
    throttle = 0.0
    throttle_target = 0.0
    turning_speed = 0.01
    damping = 0.1

    stance = "FLANK"
    agent_type = "VEHICLE"

    def __init__(self, level, load_name, location, team, load_dict=None):

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
        self.direction = [1, 0]
        self.destinations = []
        self.aim = None
        self.occupied = []

        self.target = None
        self.reverse = False
        self.selected = False
        self.waiting = False

        self.movement = agent_actions.AgentMovement(self)
        self.navigation = agent_actions.Navigation(self)

        self.load_stats()

        self.state = None

        self.set_starting_state()
        self.level.agents.append(self)

        if load_dict:
            self.reload(load_dict)

    def save(self):

        save_dict = {"team": self.team, "location": self.location, "direction": self.direction,
                     "selected": self.selected, "state_name": self.state.name,
                     "state_count": self.state.count, "movement_target": self.movement.target,
                     "movement_target_direction": self.movement.target_direction,
                     "movement_timer": self.movement.timer,
                     "navigation_destination": self.navigation.destination,
                     "navigation_history": self.navigation.history, "destinations": self.destinations,
                     "reverse": self.reverse, "occupied": self.occupied, "aim": self.aim}

        return save_dict

    def reload(self, agent_dict):

        self.direction = agent_dict["direction"]
        state_class = globals()[agent_dict["state_name"]]

        self.state = state_class(self)
        self.state.count = agent_dict["state_count"]

        self.movement.load_movement(agent_dict["movement_target"], agent_dict["movement_target_direction"],
                                    agent_dict["movement_timer"])

        self.navigation.destination = agent_dict["navigation_destination"]
        self.navigation.history = agent_dict["navigation_history"]

        self.selected = agent_dict["selected"]
        self.destinations = agent_dict["destinations"]
        self.aim = agent_dict["aim"]
        self.reverse = agent_dict["reverse"]
        self.set_occupied(None, agent_dict["occupied"])

    def set_occupied(self, target_tile, occupied_list=None):
        display = True

        if not occupied_list:
            x, y = target_tile
            occupied_list = [bgeutils.get_key([x + ox, y + oy]) for ox in range(-self.size, self.size + 1) for oy in range(-self.size, self.size + 1)]

        for tile_key in occupied_list:
            if display:
                marker = self.box.scene.addObject("debug_marker", self.box, 120)
                marker.worldPosition = mathutils.Vector(self.level.map[tile_key]["position"]).to_3d()
                marker.worldPosition.z = self.level.map[tile_key]["height"]

            self.level.map[tile_key]["occupied"] = self
            self.occupied.append(tile_key)

    def check_occupied(self, target_tile):

        x, y = target_tile
        occupied = []
        occupied_list = [bgeutils.get_key([x + ox, y + oy]) for ox in range(-self.size, self.size + 1) for oy in
                         range(-self.size, self.size + 1)]

        for tile_key in occupied_list:
            tile = self.level.map.get(tile_key)
            if tile:
                if tile["occupied"]:
                    if tile["occupied"] != self:
                        occupied.append(tile["occupied"])

        return occupied

    def clear_occupied(self):

        for tile_key in self.occupied:
            self.level.map[tile_key]["occupied"] = None
        self.occupied = []

    def add_box(self):
        box = self.level.own.scene.addObject("agent", self.level.own, 0)
        return box

    def terminate(self):
        self.box.endObject()
        self.debug_label.ended = True

    def load_stats(self):
        self.size = 1
        self.max_speed = 0.02
        self.handling = 0.02
        self.speed = 0.06
        self.turning_speed = 0.03

    def set_speed(self):
        self.speed = 0.02
        self.turning_speed = 0.01

    def set_position(self):
        self.movement.initial_position()

    def get_facing(self, target_vector):

        if not target_vector:
            target_vector = self.movement_hook.getAxisVect([0.0, 1.0, 0.0])

        search_array = [(1, 0), (1, 1), (0, 1), (1, -1), (-1, 0), (-1, 1), (0, -1), (-1, -1)]

        best_facing = None
        best_angle = 4.0

        for facing in search_array:
            facing_vector = mathutils.Vector(facing).to_3d()
            angle = target_vector.angle(facing_vector)
            if angle < best_angle:
                best_facing = facing
                best_angle = angle

        return best_facing

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
                    self.navigation.stop = True
                    self.destinations = [position]

                if reverse:
                    self.reverse = True
                else:
                    self.reverse = False

            if command["LABEL"] == "ROTATION_TARGET":
                position = command["POSITION"]
                reverse = command["REVERSE"]

                if reverse:
                    self.reverse = True
                else:
                    self.reverse = False

                target_vector = mathutils.Vector(position).to_3d() - self.box.worldPosition.copy()
                best_facing = self.get_facing(target_vector)

                self.navigation.stop = True
                self.aim = best_facing

        self.commands = []

    def set_starting_state(self):
        self.state = AgentStartUp(self)

    def state_machine(self):
        self.state.update()

        next_state = self.state.transition
        if next_state:
            self.state.end()
            self.state = next_state(self)

    def update(self):
        self.debug_text = "{}\n{}".format(self.state.name, self.destinations)

        self.process_commands()
        if not self.ended:
            if not self.level.paused:
                self.state_machine()
