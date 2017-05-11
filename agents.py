import bge
import mathutils
import bgeutils
import particles
from agent_states import *
import agent_actions
import static_dicts
import random


class Agent(object):
    size = 0
    max_speed = 0.02
    speed = 0.02
    handling = 0.02
    throttle = 0.0
    throttle_target = 0.0
    turning_speed = 0.01
    damping = 0.1
    turret_speed = 0.01
    base_visual_range = 6
    visual_range = 6

    stance = "FLANK"
    agent_type = "VEHICLE"

    def __init__(self, level, load_name, location, team, agent_id=None, load_dict=None):

        self.level = level

        if not agent_id:
            self.agent_id = "{}${}".format(self.agent_type, self.level.agent_id_index)
            self.level.agent_id_index += 1
        else:
            self.agent_id = agent_id

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
        self.soldiers = []

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
        self.navigation = agent_actions.AgentNavigation(self)
        self.agent_targeter = agent_actions.AgentTargeter(self)
        self.animator = agent_actions.AgentAnimator(self)

        self.load_stats()

        self.state = None

        self.set_starting_state()
        self.level.agents[self.agent_id] = self

        if load_dict:
            self.reload(load_dict)

    def save(self):

        save_dict = {"agent_type": self.agent_type, "team": self.team, "location": self.location, "direction": self.direction,
                     "selected": self.selected, "state_name": self.state.name,
                     "state_count": self.state.count, "movement_target": self.movement.target,
                     "movement_target_direction": self.movement.target_direction,
                     "movement_timer": self.movement.timer,
                     "navigation_destination": self.navigation.destination,
                     "navigation_history": self.navigation.history, "destinations": self.destinations,
                     "reverse": self.reverse, "throttle": self.throttle, "occupied": self.occupied, "aim": self.aim,
                     "targeter_id": self.agent_targeter.enemy_target_id,
                     "targeter_infantry_index": self.agent_targeter.infantry_index,
                     "targeter_angle": self.agent_targeter.turret_angle,
                     "targeter_elevation": self.agent_targeter.gun_elevation}

        return save_dict

    def reload(self, agent_dict):

        self.direction = agent_dict["direction"]

        self.movement.load_movement(agent_dict["movement_target"], agent_dict["movement_target_direction"],
                                    agent_dict["movement_timer"])

        self.navigation.destination = agent_dict["navigation_destination"]
        self.navigation.history = agent_dict["navigation_history"]

        self.selected = agent_dict["selected"]
        self.destinations = agent_dict["destinations"]
        self.aim = agent_dict["aim"]
        self.reverse = agent_dict["reverse"]
        self.throttle = agent_dict["throttle"]
        self.set_occupied(None, agent_dict["occupied"])

        self.agent_targeter.enemy_target_id = agent_dict["targeter_id"]
        self.agent_targeter.infantry_index = agent_dict["targeter_infantry_index"]
        self.agent_targeter.turret_angle = agent_dict["targeter_angle"]
        self.agent_targeter.gun_elevation = agent_dict["targeter_elevation"]

        state_class = globals()[agent_dict["state_name"]]

        self.state = state_class(self)
        self.state.count = agent_dict["state_count"]

    def set_occupied(self, target_tile, occupied_list=None):
        display = False

        if not occupied_list:
            x, y = target_tile
            occupied_list = [bgeutils.get_key([x + ox, y + oy]) for ox in range(-self.size, self.size + 1) for oy in
                             range(-self.size, self.size + 1)]

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
        self.max_speed = 0.04
        self.handling = 0.01
        self.speed = 0.02
        self.turning_speed = 0.01
        self.turret_speed = 0.01
        self.base_visual_range = 6
        self.visual_range = 6

    def update_stats(self):
        if self.movement.target:
            if self.movement.target == self.navigation.destination:
                self.throttle_target = 0.3
            else:
                self.throttle_target = 1.0

        elif self.movement.target_direction:
            self.throttle_target = 0.3
        else:
            self.throttle_target = 0.0

        self.throttle = bgeutils.interpolate_float(self.throttle, self.throttle_target, self.handling)
        self.speed = self.max_speed * self.throttle
        self.turning_speed = self.handling * self.throttle

    def set_position(self):
        self.movement.initial_position()

    def get_facing(self, target_vector):

        if not target_vector:
            target_vector = self.movement_hook.getAxisVect([0.0, 1.0, 0.0])

        search_array = [[1, 0], [1, 1], [0, 1], [1, -1], [-1, 0], [-1, 1], [0, -1], [-1, -1]]

        best_facing = None
        best_angle = 4.0

        for facing in search_array:
            facing_vector = mathutils.Vector(facing)
            angle = target_vector.to_2d().angle(facing_vector)
            if angle < best_angle:
                best_facing = facing
                best_angle = angle

        return best_facing

    def get_enemy_direction(self):
        if self.agent_targeter.enemy_target_id:
            enemy_agent = self.level.agents.get(self.agent_targeter.enemy_target_id)
            if enemy_agent:
                target_vector = (enemy_agent.box.worldPosition.copy() - self.box.worldPosition.copy()).to_2d()

                return self.get_facing(target_vector)

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
                        points = [cam.getScreenPosition(self.box)]
                        for soldier in self.soldiers:
                            points.append(cam.getScreenPosition(soldier.box))
                        padding = 0.03

                        for screen_location in points:

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
                self.destinations = []
                self.aim = best_facing
                self.agent_targeter.enemy_target_id = None

            if command["LABEL"] == "TARGET_ENEMY":
                target_id = command["TARGET_ID"]
                infantry_index = command["INFANTRY_INDEX"]

                self.agent_targeter.enemy_target_id = target_id
                self.agent_targeter.infantry_index = infantry_index
                self.navigation.stop = True
                self.destinations = []

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
        self.debug_text = "{} - {}\n{} -  {}".format(self.agent_id, self.state.name, self.direction, self.agent_targeter.hull_on_target)

        infantry_types = ["INFANTRY", "ARTILLERY"]

        self.process_commands()
        if not self.ended:
            if not self.level.paused:
                self.state_machine()

                if self.agent_type in infantry_types:
                    self.infantry_update()

    def infantry_update(self):
        pass


class Vehicle(Agent):
    def __init__(self, level, load_name, location, team, agent_id=None, load_dict=None):
        self.agent_type = "VEHICLE"
        super().__init__(level, load_name, location, team, agent_id, load_dict)


class Infantry(Agent):
    def __init__(self, level, load_name, location, team, agent_id=None, load_dict=None):
        self.agent_type = "INFANTRY"
        self.avoid_radius = 3
        self.spacing = 1.5
        self.prone = False
        self.size = 1

        super().__init__(level, load_name, location, team, agent_id, load_dict)

        squad = static_dicts.squads[load_name]
        self.squad = [rank for rank in squad if rank != [""]]
        self.wide = len(self.squad[0])
        self.deep = len(self.squad)
        self.formation = []
        self.add_squad()

    def add_squad(self):

        self.set_formation()
        index = 0

        for rank in self.squad:
            for soldier in rank:
                self.soldiers.append(InfantryMan(self, soldier, index))
                index += 1

    def set_occupied(self, target_tile, occupied_list=None):
        pass

    def update_stats(self):
        self.speed = self.max_speed

    def set_formation(self):

        self.formation = []

        order = [self.deep, self.wide]
        spacing = self.spacing * 2.0
        scatter = 0.0
        y_offset = 0.0
        x_offset = 0

        if self.stance == "AGGRESSIVE":
            self.prone = False
            self.avoid_radius = 3
            self.max_speed = 0.025
            order = [self.deep, self.wide]
            spacing = self.spacing * 1.5
            scatter = spacing * 0.2

        if self.stance == "SENTRY":
            self.prone = False
            self.avoid_radius = 6
            self.max_speed = 0.02
            order = [self.deep, self.wide]
            spacing = self.spacing * 3.0
            scatter = spacing * 0.5

        if self.stance == "DEFEND":
            self.prone = True
            self.avoid_radius = 12
            self.max_speed = 0.015
            order = [self.deep, self.wide]
            spacing = self.spacing * 2.0
            scatter = spacing * 0.1

        if self.stance == "FLANK":
            self.prone = False
            self.avoid_radius = 12
            self.max_speed = 0.03
            order = [self.wide, self.deep]
            spacing = self.spacing
            scatter = 0.02

        half = spacing * 0.5

        def s_value(scatter_value):
            return scatter_value - (scatter_value * random.uniform(0.0, 2.0))

        for y in range(order[0]):
            for x in range(order[1]):

                if order[0] > 1:
                    y_offset = ((order[0] - 2) * spacing)

                if order[1] % 2 != 0:
                    x_offset = spacing * 0.5

                x_loc = (-order[1] * half) + (x * spacing) + half + s_value(scatter) + x_offset
                y_loc = (-order[0] * half) + (y * spacing) + half + s_value(scatter) - y_offset

                self.formation.append(mathutils.Vector([x_loc, y_loc]))

    def add_box(self):
        box = self.level.own.scene.addObject("agent_infantry", self.level.own, 0)
        return box

    def infantry_update(self):
        for soldier in self.soldiers:
            soldier.update()


class InfantryMan(object):

    def __init__(self, agent, infantry_type, index):
        self.agent = agent
        self.infantry_type = infantry_type

        self.index = index
        self.box = self.agent.box.scene.addObject("infantry_dummy", self.agent.box, 0)
        self.location = self.agent.location
        self.direction = [0, 1]
        self.occupied = None
        self.avoiding = False

        self.speed = 0.02

        self.movement = agent_actions.InfantryAction(self)
        self.navigation = agent_actions.InfantryNavigation(self)

    def update(self):
        if self.movement.done:
            self.navigation.update()

        self.movement.update()

    def set_occupied(self, target_tile):
        self.agent.level.map[bgeutils.get_key(target_tile)]["occupied"] = self.agent
        self.occupied = self.location

    def clear_occupied(self):
        if self.occupied:
            self.agent.level.map[bgeutils.get_key(self.occupied)]["occupied"] = None
            self.occupied = None

    def check_occupied(self, target_tile):
        tile = self.agent.level.map.get(bgeutils.get_key(target_tile))
        if tile:
            if tile["occupied"]:
                return tile["occupied"]
        else:
            return self

    def check_too_close(self, target_tile):

        closest = []

        radius = self.agent.avoid_radius

        ox, oy = target_tile

        for x in range(-radius, radius):
            for y in range(-radius, radius):
                check_key = (ox + x, oy + y)
                check_tile = self.agent.level.map.get(check_key)

                if check_tile:
                    vehicles = ["VEHICLE", "ARTILLERY"]
                    if check_tile["occupied"]:
                        if check_tile["occupied"] != self.agent and check_tile["occupied"].agent_type in vehicles:
                            closest.append(check_tile["occupied"])

        if closest:
            return closest[0]

    def get_destination(self):
        self.set_speed()

        location = self.agent.box.worldPosition.copy()
        location.z = 0.0

        offset = mathutils.Vector(self.agent.formation[self.index]).to_3d()
        offset.rotate(self.agent.movement_hook.worldOrientation.copy())

        destination = (location + offset).to_2d()

        return [round(axis) for axis in destination]

    def set_speed(self):
        self.speed = self.agent.speed
