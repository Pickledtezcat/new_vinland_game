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
    accuracy = 6

    stance = "AGGRESSIVE"
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
        self.faction = self.level.factions[self.team]

        self.dead = False
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
        self.enter_building = None
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

        save_dict = {"agent_type": self.agent_type, "team": self.team, "location": self.location,
                     "direction": self.direction, "enter_building": self.enter_building,
                     "selected": self.selected, "state_name": self.state.name, "load_name": self.load_name,
                     "state_count": self.state.count, "movement_target": self.movement.target,
                     "movement_target_direction": self.movement.target_direction,
                     "movement_timer": self.movement.timer,
                     "navigation_destination": self.navigation.destination,
                     "navigation_history": self.navigation.history, "destinations": self.destinations,
                     "reverse": self.reverse, "throttle": self.throttle, "occupied": self.occupied, "aim": self.aim,
                     "targeter_id": self.agent_targeter.enemy_target_id,
                     "targeter_angle": self.agent_targeter.turret_angle,
                     "targeter_elevation": self.agent_targeter.gun_elevation, "stance": self.stance,
                     "soldiers": [solider.save() for solider in self.soldiers]}

        self.clear_occupied()
        return save_dict

    def reload(self, agent_dict):

        self.direction = agent_dict["direction"]
        self.enter_building = agent_dict["enter_building"]
        self.load_name = agent_dict["load_name"]

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
        self.stance = agent_dict["stance"]

        self.agent_targeter.enemy_target_id = agent_dict["targeter_id"]
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

            self.level.map[tile_key]["occupied"] = self.agent_id
            self.occupied.append(tile_key)

    def check_occupied(self, target_tile):

        occupied = []

        current_tile = self.level.get_tile(self.location)
        inside = current_tile["occupied"] or current_tile["building"]
        if inside:
            return occupied

        x, y = target_tile
        occupied_list = [[x + ox, y + oy] for ox in range(-self.size, self.size + 1) for oy in
                         range(-self.size, self.size + 1)]

        for tile_key in occupied_list:
            tile = self.level.get_tile(tile_key)
            if tile:
                occupier_id = tile["occupied"]

                if occupier_id:
                    occupier = self.level.agents.get(occupier_id)

                    if occupier and occupier != self:
                        occupied.append(occupier)

                if not self.enter_building:
                    building_id = tile["building"]

                    if building_id:
                        occupier = self.level.buildings.get(building_id)

                        if occupier:
                            occupied.append(occupier)

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

        for soldier in self.soldiers:
            soldier.terminate()

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

        self.set_speed()

    def set_speed(self):
        self.throttle = bgeutils.interpolate_float(self.throttle, self.throttle_target, self.handling)
        self.speed = self.max_speed * self.throttle
        self.turning_speed = self.handling * self.throttle

    def set_position(self):
        self.movement.initial_position()

    def get_facing(self, target_vector):

        if not target_vector or target_vector.length < 0.001:
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
            if command['label'] == "SELECT":
                if self.team == 0:

                    x_limit = command["x_limit"]
                    y_limit = command["y_limit"]
                    additive = command["additive"]
                    mouse_over = command["mouse_over"]

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

            if command["label"] == "MOVEMENT_TARGET":
                self.enter_building = None
                position = command["position"]
                reverse = command["reverse"]
                additive = command["additive"]

                if additive:
                    self.destinations.append(position)
                else:
                    self.navigation.stop = True
                    self.destinations = [position]

                if reverse:
                    self.reverse = True
                else:
                    self.reverse = False

            if command["label"] == "ROTATION_TARGET":
                self.enter_building = None
                position = command["position"]
                reverse = command["reverse"]

                if reverse:
                    target_vector = self.box.worldPosition.copy() - mathutils.Vector(position).to_3d()
                    self.reverse = True
                else:
                    target_vector = mathutils.Vector(position).to_3d() - self.box.worldPosition.copy()
                    self.reverse = False

                best_facing = self.get_facing(target_vector)

                self.navigation.stop = True
                self.destinations = []
                self.aim = best_facing
                self.agent_targeter.enemy_target_id = None

            if command["label"] == "TARGET_ENEMY":
                self.enter_building = None
                target_id = command["target_id"]

                self.agent_targeter.enemy_target_id = target_id
                self.navigation.stop = True
                self.destinations = []

            if command["label"] == "STANCE_CHANGE":
                stance = command["stance"]
                self.stance = stance
                self.set_formation()

            if command["label"] == "ENTER_BUILDING":
                if self.agent_type == "INFANTRY":
                    building_id = command["target_id"]
                    additive = command["additive"]
                    building = self.level.buildings.get(building_id)
                    if building:
                        self.enter_building = building_id

                        if additive:
                            self.destinations.append(building.location)
                        else:
                            self.destinations = [building.location]

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
        # self.debug_text = "{} - {}\n{} -  {}".format(self.agent_id, self.state.name, self.direction, self.agent_targeter.hull_on_target)

        # TODO integrate pause, dead and other behavior in to states

        debug_icon = {"AGGRESSIVE": "[A]",
                      "SENTRY": "[S]",
                      "DEFEND": "[D]",
                      "FLANK": "[F]"}

        self.debug_text = ""

        if not self.dead:
            if self.team == 0:
                self.debug_text = debug_icon[self.stance]
            self.process_commands()
        else:
            self.selected = False

        # set debug text over ride
        self.debug_text = str(self.enter_building)

        infantry_types = ["INFANTRY", "ARTILLERY"]

        if not self.ended:
            if not self.level.paused:
                self.state_machine()

                if self.agent_type in infantry_types:
                    self.infantry_update()

    def infantry_update(self):
        pass

    def set_formation(self):
        pass


class Vehicle(Agent):
    def __init__(self, level, load_name, location, team, agent_id=None, load_dict=None):
        self.agent_type = "VEHICLE"
        super().__init__(level, load_name, location, team, agent_id, load_dict)


class Infantry(Agent):
    def __init__(self, level, load_name, location, team, agent_id=None, load_dict=None):
        self.agent_type = "INFANTRY"
        self.avoid_radius = 4
        self.spacing = 1.5
        self.prone = False
        self.size = 1
        self.walk_mod = 1.0

        super().__init__(level, load_name, location, team, agent_id, load_dict)

        squad = static_dicts.squads[self.load_name]
        self.squad = [rank for rank in squad if rank != [""]]
        self.squad.reverse()
        self.wide = len(self.squad[0])
        self.deep = len(self.squad)
        self.formation = []
        self.add_squad(load_dict)

        infantry_speed = [soldier.speed for soldier in self.soldiers]
        self.speed = min(infantry_speed)

    def add_squad(self, load_dict):

        self.set_formation()
        index = 0

        if load_dict:
            for soldier_details in load_dict["soldiers"]:
                solider = soldier_details["infantry_type"]
                self.soldiers.append(InfantryMan(self, solider, index, load_dict=soldier_details))
        else:
            for rank in self.squad:
                for soldier in rank:
                    self.soldiers.append(InfantryMan(self, soldier, index))
                    index += 1

    def set_occupied(self, target_tile, occupied_list=None):
        pass

    def update_stats(self):
        dead = True
        for soldier in self.soldiers:
            if not soldier.dead:
                dead = False

        if dead:
            self.dead = True

        self.set_speed()

    def set_speed(self):
        infantry_speed = [soldier.speed for soldier in self.soldiers]
        self.speed = min(infantry_speed)

    def set_formation(self):

        self.formation = []

        order = [self.deep, self.wide]
        spacing = self.spacing * 2.0
        scatter = 0.0
        y_offset = 0.0
        x_offset = 0

        if self.stance == "AGGRESSIVE":
            self.prone = False
            self.avoid_radius = 2
            self.walk_mod = 0.85
            order = [self.deep, self.wide]
            spacing = self.spacing * 1.5
            scatter = spacing * 0.2

        if self.stance == "SENTRY":
            self.prone = False
            self.avoid_radius = 2
            self.walk_mod = 0.75
            order = [self.deep, self.wide]
            spacing = self.spacing * 3.0
            scatter = spacing * 0.5

        if self.stance == "DEFEND":
            self.prone = True
            self.avoid_radius = 4
            self.walk_mod = 0.5
            order = [self.deep, self.wide]
            spacing = self.spacing * 2.5
            scatter = spacing * 0.3

        if self.stance == "FLANK":
            self.prone = False
            self.avoid_radius = 4
            self.walk_mod = 1.0
            order = [self.wide, self.deep]
            spacing = self.spacing
            scatter = 0.02

        half = spacing * 0.5

        def s_value(scatter_value):
            return scatter_value - (scatter_value * random.uniform(0.0, 2.0))

        if order[0] > 1:
            y_offset = spacing

        if order[1] % 2 != 0:
            x_offset = spacing * 0.5

        for y in range(order[0]):
            for x in range(order[1]):
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
    def __init__(self, agent, infantry_type, index, load_dict=None):
        self.agent = agent
        self.agent_type = "INFANTRYMAN"
        self.infantry_type = infantry_type

        stats = static_dicts.soldiers()[self.infantry_type]

        self.mesh_name = stats["mesh_name"]
        self.toughness = stats["toughness"]
        self.base_speed = stats["speed"]
        self.power = stats["power"]
        self.rof = stats["ROF"]
        self.special = stats["special"]
        self.sound = stats["sound"]

        self.weapon = SoldierWeapon(self)

        # TODO add other infantry stats here

        self.index = index
        self.box = self.agent.box.scene.addObject("infantry_dummy", self.agent.box, 0)
        self.sprite = self.box.children[0]
        self.location = self.agent.location
        self.direction = [0, 1]
        self.occupied = None
        self.in_building = None
        self.dead = False

        self.speed = 0.02

        self.movement = agent_actions.InfantryAction(self)
        self.behavior = agent_actions.InfantryBehavior(self)
        self.animation = agent_actions.InfantryAnimation(self)

        if load_dict:
            self.reload(load_dict)

    def terminate(self):
        self.box.endObject()

    def close_up_formation(self):

        if self.index < len(self.agent.formation) - 1:
            next_index = self.index + 1
            changed = False

            next_soldier = [soldier for soldier in self.agent.soldiers if soldier.index == next_index]

            if next_soldier:
                if next_soldier[0].dead:
                    # TODO sort formation towards the front
                    changed = True
                    self.index = next_index

            if changed:
                self.agent.navigation.get_next_destination()

    def update(self):
        self.behavior.update()
        self.animation.update()
        self.movement.update()

        if not self.dead:
            self.weapon.update()

    def set_occupied(self, target_tile):
        self.agent.level.map[bgeutils.get_key(target_tile)]["occupied"] = self.agent.agent_id
        self.occupied = self.location

    def clear_occupied(self):
        if self.occupied:
            self.agent.level.map[bgeutils.get_key(self.occupied)]["occupied"] = None
            self.occupied = None

    def check_occupied(self, target_tile):
        tile = self.agent.level.get_tile(target_tile)
        if tile:
            occupier_id = tile["occupied"]
            if occupier_id:
                occupier = self.agent.level.agents.get(occupier_id)
                if occupier:
                    return occupier

            building_id = tile["building"]
            if building_id:
                occupier = self.agent.level.buildings.get(building_id)
                if occupier:
                    return occupier

        else:
            return self

    def check_too_close(self, target_tile):

        closest = []

        radius = self.agent.avoid_radius

        ox, oy = target_tile

        for x in range(-radius, radius):
            for y in range(-radius, radius):
                check_key = [ox + x, oy + y]
                check_tile = self.agent.level.get_tile(check_key)

                if check_tile:
                    vehicles = ["VEHICLE", "ARTILLERY"]
                    occupier_id = check_tile["occupied"]
                    if occupier_id:
                        occupant = self.agent.level.agents.get(occupier_id)
                        if occupant:
                            if occupant != self.agent and occupant.agent_type in vehicles:
                                if occupant.navigation.destination:
                                    closest.append(occupant)

        if closest:
            return closest[0]

    def get_destination(self):
        self.set_speed()
        destination = None

        if self.agent.enter_building:
            building = self.agent.level.buildings.get(self.agent.enter_building)
            if building:
                destination = building.get_closest_door(list(self.box.worldPosition.copy()))[:2]

        if not destination:
            location = self.agent.box.worldPosition.copy()
            location.z = 0.0

            offset = mathutils.Vector(self.agent.formation[self.index]).to_3d()
            offset.rotate(self.agent.movement_hook.worldOrientation.copy())

            destination = (location + offset).to_2d()

        return [round(axis) for axis in destination]

    def set_speed(self):
        self.speed = (self.base_speed * self.agent.walk_mod) * 0.005

    def save(self):

        save_dict = {"movement_target": self.movement.target, "movement_timer": self.movement.timer,
                     "destination": self.behavior.destination, "history": self.behavior.history, "in_building": self.in_building,
                     "toughness": self.toughness, "behavior_prone": self.behavior.prone, "index": self.index,
                     "prone": self.agent.prone, "direction": self.direction, "location": self.location,
                     "infantry_type": self.infantry_type, "occupied": self.occupied, "weapon_timer": self.weapon.timer,
                     "weapon_ready": self.weapon.ready, "weapon_ammo": self.weapon.ammo, "dead": self.dead}

        self.clear_occupied()
        return save_dict

    def reload(self, load_dict):

        self.index = load_dict["index"]
        self.agent.prone = load_dict["prone"]
        self.direction = load_dict["direction"]
        self.location = load_dict["location"]
        self.in_building = load_dict["in_building"]

        self.mesh_name = static_dicts.soldiers()[self.infantry_type]["mesh_name"]

        self.movement.set_vectors()
        self.movement.set_position()

        self.behavior.destination = load_dict["destination"]
        self.behavior.history = load_dict["history"]
        self.behavior.prone = load_dict["behavior_prone"]
        self.toughness = load_dict["toughness"]

        self.weapon.timer = load_dict["weapon_timer"]
        self.weapon.ready = load_dict["weapon_ready"]
        self.weapon.ammo = load_dict["weapon_ammo"]
        self.dead = load_dict["dead"]

        self.behavior.update()
        self.animation.update()


class SoldierWeapon(object):
    def __init__(self, infantryman):
        self.weapon_type = "INFANTRY_WEAPON"
        self.infantryman = infantryman
        self.power = self.infantryman.power
        self.range = self.power * 2.0
        self.sound = self.infantryman.sound
        self.recharge = (self.infantryman.rof * 0.0025) * random.uniform(0.8, 1.0)
        self.special = self.infantryman.special
        self.accuracy = self.infantryman.agent.accuracy
        self.timer = 0.0
        self.ammo = 1.0
        self.effect_timer = random.randint(0, 3)
        self.ready = False
        self.in_range = False
        self.check_timer = 0

    def update(self):

        prone = self.infantryman.agent.prone

        if prone:
            self.accuracy = self.infantryman.agent.accuracy * 2.0
        else:
            self.accuracy = self.infantryman.agent.accuracy

        if self.ammo > 0.0:
            if not self.ready:
                if prone:
                    recharge = self.recharge * 0.5
                else:
                    recharge = self.recharge

                self.timer = min(1.0, self.timer + recharge)
                if self.timer >= 1.0:
                    self.timer = 0.0
                    self.ready = True

            if self.check_timer <= 0:
                self.check_timer = 8
                self.in_range = self.check_in_range()

            else:
                self.check_timer -= 1

        else:
            self.ready = False

    def check_in_range(self):
        target_id, target = self.get_target()
        if target:
            distance = (target.box.worldPosition.copy() - self.infantryman.box.worldPosition.copy()).length
            if distance < self.range:
                return True

    def get_target(self):
        target_id = self.infantryman.agent.agent_targeter.enemy_target_id
        target = self.infantryman.agent.level.agents.get(target_id)
        return target_id, target

    def shoot_weapon(self):
        target_id, target = self.get_target()

        if target and self.ready and self.in_range:

            effect = None

            if self.effect_timer > 2:
                self.effect_timer = 1
                effect = "YELLOW_STREAK"
            else:
                self.effect_timer += 1

            if self.special == "ANTI_TANK":
                effect = "RED_STREAK"

            command = {"label": "SMALL_ARMS_SHOOT", "weapon": self, "owner": self.infantryman, "target_id": target_id,
                       "effect": effect}

            bgeutils.sound_message("SOUND_EFFECT", ("I_{}".format(self.sound), None, 3.0, 1.0))
            self.infantryman.agent.level.commands.append(command)
            self.ready = False
            self.timer = 0.0
            self.ammo -= 0.01

            return True

        return False
