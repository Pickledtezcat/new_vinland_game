import bge
import mathutils
import bgeutils
import particles
from agent_states import *
import agent_actions
import static_dicts
import random
import vehicle_stats
import model_display
import math


class VehicleTrails(object):
    def __init__(self, agent):

        self.agent = agent
        self.level = agent.level
        self.size = self.agent.stats.chassis_size
        self.timer = 0.0

        self.adders = bgeutils.get_ob_list("trail", self.agent.box.childrenRecursive)
        self.tracks = []

    def end_tracks(self):

        for track in self.tracks:
            track.dropped = True
        self.tracks = []

    def add_tracks(self):

        self.end_tracks()
        self.tracks = [particles.Track(self.level, adder, self.size * 2.0, self.agent.off_road) for adder in self.adders]

    def update(self):

        if self.agent.on_screen:
            if self.adders:
                if self.timer >= 1.0:
                    self.timer = 0.0
                    for adder in self.adders:
                        particles.DirtClods(self.level,  (self.size - 0.5) * self.agent.off_road, adder.worldPosition.copy())
                    self.add_tracks()
                else:
                    self.timer += abs(self.agent.display_speed * 0.15)

        else:
            self.end_tracks()


class Agent(object):
    size = 0
    off_road = 0.0
    max_speed = 0.02
    speed = 0.0
    display_speed = 0.0
    handling = 0.02
    throttle = 0.0
    throttle_target = 0.0
    turning_speed = 0.01
    # TODO set damping to match vehicle weight

    damping = 0.05
    turret_speed = 0.01
    rank = 2
    accuracy = 6
    vision_distance = 0
    initial_health = 0
    shock = 0.0
    ammo = 0.0
    resistance = 0.0
    best_penetration = 0
    on_screen = False
    has_ammo = 1
    is_damaged = -1
    is_carrying = False
    is_sentry = False
    is_shocked = -1
    best_weapon = None

    stance = "FLANK"

    def __init__(self, level, load_name, location, team, agent_id=None, load_dict=None):
        self.agent_type = self.get_agent_type()
        self.level = level

        if not agent_id:
            self.agent_id = "{}${}".format(self.agent_type, self.level.get_new_id())
        else:
            self.agent_id = agent_id

        self.load_name = load_name
        self.team = team
        self.faction = self.level.factions[self.team]

        self.dead = False
        self.knocked_out = False
        self.on_fire = False
        self.ended = False
        self.visible = True
        self.seen = False
        self.suspect = False
        self.selection_group = None
        self.weapons = []

        self.stats = None
        self.health = 0
        self.mechanical_damage = 0
        self.crippled = False
        self.load_stats()

        self.model = None
        self.movement_hook = None
        self.tilt_hook = None
        self.box = None
        self.add_box()

        self.debug_label = particles.DebugLabel(self.level, self)
        self.debug_text = ""

        self.commands = []
        self.hits = []
        self.soldiers = []

        self.location = location
        self.direction = [0, -1]
        self.destinations = []
        self.enter_building = None
        self.enter_vehicle = None
        self.occupier = None
        self.aim = None
        self.occupied = []
        self.target = None
        self.reverse = False
        self.selected = False
        self.waiting = False
        self.deployed = 0.0
        self.stowed = 0.0
        self.angled = 0.0
        self.shooting_bonus = 0.0
        self.trails = None

        self.movement = agent_actions.AgentMovement(self)
        self.navigation = agent_actions.AgentNavigation(self)
        self.agent_targeter = agent_actions.AgentTargeter(self)

        self.state = None
        self.center = None
        self.get_center()

        self.set_starting_state()
        self.level.agents[self.agent_id] = self

        if load_dict:
            self.reload(load_dict)

    def get_agent_type(self):
        return "VEHICLE"

    def get_center(self):
        self.center = self.box.worldPosition.copy()

    def update_trails(self):
        if self.trails:
            self.trails.update()

    def end_trails(self):
        if self.trails:
            self.trails.end_tracks()

    def get_visual_range(self):

        visual_range = 3

        # TODO handle vehicle viewing range

        for soldier in self.soldiers:
            if not soldier.dead:

                if soldier.special == "OFFICER":
                    visual_range = max(visual_range, 4)
                if soldier.special == "COMMANDER":
                    visual_range = max(visual_range, 5)
                if soldier.special == "OBSERVER":
                    visual_range = max(visual_range, 6)

        if self.stance == "SENTRY":
            visual_range = min(7, visual_range + 1)

        self.vision_distance = visual_range * 6

        return visual_range

    def add_visibility_marker(self):
        if self.team == 0:
            command = {"label": "VISIBILITY_MARKER",
                       "location": bgeutils.position_to_location(self.center.copy()), "duration": 18.0}
            self.level.commands.append(command)

    def set_visible(self, setting):
        self.visible = setting

    def set_seen(self, setting):
        self.seen = setting

    def set_suspect(self, setting):
        self.suspect = setting

    def update_model(self):
        if self.model:
            self.model.game_update()

    def process_hits(self):
        pass

    def handle_weapons(self):
        pass

    def save(self):

        weapons = [weapon.timer for weapon in self.weapons]

        save_dict = {"agent_type": self.agent_type, "team": self.team, "location": self.location, "dead": self.dead,
                     "knocked_out": self.knocked_out, "rank": self.rank, "shock": self.shock, "health": self.health,
                     "direction": self.direction, "enter_building": self.enter_building, "angled": self.angled,
                     "mechanical_damage": self.mechanical_damage, "enter_vehicle": self.enter_vehicle,
                     "on_fire": self.on_fire, "selected": self.selected, "state_name": self.state.name,
                     "load_name": self.load_name, "ammo": self.ammo, "stance": self.stance, "occupier": self.occupier,
                     "state_count": self.state.count, "movement_target": self.movement.target, "stowed": self.stowed,
                     "movement_target_direction": self.movement.target_direction, "weapons": weapons,
                     "movement_timer": self.movement.timer, "initial_health": self.initial_health,
                     "navigation_destination": self.navigation.destination, "deployed": self.deployed,
                     "navigation_history": self.navigation.history, "destinations": self.destinations,
                     "reverse": self.reverse, "throttle": self.throttle, "occupied": self.occupied, "aim": self.aim,
                     "selection_group": self.selection_group, "turret_angle": self.agent_targeter.turret_angle,
                     "off_road": self.off_road,
                     "soldiers": [solider.save() for solider in self.soldiers]}

        self.clear_occupied()
        return save_dict

    def reload(self, agent_dict):

        self.direction = agent_dict["direction"]
        self.enter_building = agent_dict["enter_building"]
        self.enter_vehicle = agent_dict["enter_vehicle"]
        self.occupier = agent_dict["occupier"]
        self.load_name = agent_dict["load_name"]
        self.dead = agent_dict["dead"]
        self.knocked_out = agent_dict["knocked_out"]
        self.on_fire = agent_dict["on_fire"]
        self.rank = agent_dict["rank"]
        self.shock = agent_dict["shock"]
        self.health = agent_dict["health"]
        self.mechanical_damage = agent_dict["mechanical_damage"]
        self.ammo = agent_dict["ammo"]
        self.deployed = agent_dict["deployed"]
        self.angled = agent_dict["angled"]
        self.stowed = agent_dict["stowed"]
        self.off_road = agent_dict["off_road"]

        self.movement.load_movement(agent_dict["movement_target"], agent_dict["movement_target_direction"],
                                    agent_dict["movement_timer"])

        self.navigation.destination = agent_dict["navigation_destination"]
        self.navigation.history = agent_dict["navigation_history"]

        self.selected = agent_dict["selected"]
        self.selection_group = agent_dict["selection_group"]

        self.destinations = agent_dict["destinations"]
        self.aim = agent_dict["aim"]
        self.reverse = agent_dict["reverse"]
        self.throttle = agent_dict["throttle"]
        self.set_occupied(None, agent_dict["occupied"])
        self.stance = agent_dict["stance"]

        self.agent_targeter.turret_angle = agent_dict["turret_angle"]

        state_class = globals()[agent_dict["state_name"]]

        self.state = state_class(self)
        self.state.count = agent_dict["state_count"]

        self.initial_health = agent_dict["initial_health"]

        weapons = agent_dict["weapons"]

        for i in range(len(weapons)):
            self.weapons[i].timer = weapons[i]

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

        current_location = self.level.get_tile(self.location)
        inside = current_location["occupied"] or current_location["building"]
        if inside:
            if current_location["occupied"] != self.agent_id:
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
                    if occupier:
                        if occupier != self:
                            occupied.append(occupier)

                building_id = tile["building"]
                if building_id:
                    building = self.level.buildings.get(building_id)

                    if building:
                        occupied.append(building)
            else:
                occupied.append(self)

        return occupied

    def clear_occupied(self):

        for tile_key in self.occupied:
            self.level.map[tile_key]["occupied"] = None
        self.occupied = []

    def add_box(self):
        box = self.level.own.scene.addObject("agent", self.level.own, 0)

        self.box = box
        self.movement_hook = bgeutils.get_ob("hook", self.box.childrenRecursive)
        self.tilt_hook = bgeutils.get_ob("tilt", self.box.childrenRecursive)

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

    def get_best_penetration(self):
        self.best_penetration = 0

    def update_stats(self):

        self.accuracy = float(self.rank)
        self.resistance = float(self.rank)

        resistance = self.resistance * 0.05

        self.shock = max(0.0, self.shock - resistance)

        if self.movement.target:
            if self.movement.target == self.navigation.destination:
                self.throttle_target = 0.3
            else:
                self.throttle_target = 1.0

        elif self.movement.target_direction:
            self.throttle_target = 0.3
        else:
            self.throttle_target = 0.0

        self.get_best_penetration()
        self.set_speed()

    def set_speed(self):
        self.throttle = bgeutils.interpolate_float(self.throttle, self.throttle_target, self.handling)
        self.speed = self.max_speed * self.throttle
        self.turning_speed = self.handling * self.throttle

    def get_attack_facing(self, other_agent_position):
        return False

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
        if self.agent_targeter.enemy_target:
            return self.get_facing(self.agent_targeter.target_vector)

    def process_commands(self):

        for command in self.commands:
            if command:
                fully_loaded = self.fully_loaded()

                if fully_loaded:
                    self.selected = False
                    if command["label"] == "DISMOUNT_VEHICLE":
                        self.dismount_vehicle()
                else:
                    if command["label"] == "SINGLE_SELECT":
                        if self.team == 0:
                            additive = command["additive"]
                            target = command["target"]
                            if additive:
                                if self.agent_id == target:
                                    self.selected = not self.selected

                            else:
                                if self.agent_id == target:
                                    self.selected = True
                                else:
                                    self.selected = False

                    if command['label'] == "GROUP_SELECT":

                        additive = command["additive"]
                        setting = command["setting"]
                        number = command["number"]

                        if setting:
                            if self.selected:
                                self.selection_group = number
                        else:

                            if self.selection_group == number:
                                self.selected = True
                            else:
                                if not additive:
                                    self.selected = False

                    if command['label'] == "SELECT":
                        x_limit = command["x_limit"]
                        y_limit = command["y_limit"]
                        additive = command["additive"]
                        friends = command["friends"]

                        cam = self.level.manager.main_camera

                        select = False

                        if friends:
                            if self.agent_id in friends:
                                if additive:
                                    self.selected = not self.selected
                                else:
                                    self.selected = True

                            else:
                                if not additive:
                                    self.selected = False

                        else:
                            if cam.pointInsideFrustum(self.box.worldPosition.copy()):
                                points = [cam.getScreenPosition(self.box)]
                                for soldier in self.soldiers:
                                    if not soldier.dead:
                                        points.append(cam.getScreenPosition(soldier.box))

                                for screen_location in points:

                                    if x_limit[0] < screen_location[0] < x_limit[1]:
                                        if y_limit[0] < screen_location[1] < y_limit[1]:
                                            select = True

                            if select:
                                self.selected = True

                            elif not additive:
                                if not select:
                                    self.selected = False

                    if command["label"] == "MOVEMENT_TARGET":
                        self.dismount_building()
                        self.dismount_vehicle()

                        position = command["position"]
                        reverse = command["reverse"]
                        additive = command["additive"]

                        if additive:
                            self.destinations.append(position)
                        else:
                            self.navigation.stop = True
                            self.destinations = [position]

                        if reverse:
                            self.throttle = 0.0
                            self.reverse = True
                        else:
                            if self.reverse:
                                self.throttle = 0.0
                                self.reverse = False

                    if command["label"] == "ROTATION_TARGET":
                        self.dismount_building()
                        self.dismount_vehicle()

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
                        if best_facing != self.direction:
                            self.aim = best_facing
                        self.agent_targeter.set_target_id = None

                    if command["label"] == "TARGET_ENEMY":
                        self.dismount_vehicle()
                        target_id = command["target_id"]

                        self.agent_targeter.set_target_id = target_id
                        self.navigation.stop = True
                        self.destinations = []

                    if command["label"] == "STANCE_CHANGE":
                        stance = command["stance"]
                        self.stance = stance
                        self.set_formation()

                    if command["label"] == "ENTER_BUILDING":
                        self.dismount_vehicle()
                        self.mount_building(command["target_id"])

                    if command["label"] == "ENTER_VEHICLE":
                        self.dismount_building()
                        self.mount_vehicle(command["target_id"])

        self.commands = []

    def mount_building(self, building_id):
        pass

    def dismount_building(self):
        pass

    def mount_vehicle(self, vehicle_id):
        pass

    def dismount_vehicle(self):
        pass

    def fully_loaded(self):

        if not self.enter_vehicle:
            return False

        else:
            for soldier in self.soldiers:
                if not soldier.dead:
                    if not soldier.in_vehicle:
                        return False

        return True

    def set_starting_state(self):
        self.state = AgentStartUp(self)

    def state_machine(self):
        self.state.update()

        next_state = self.state.transition
        if next_state:
            self.state.end()
            self.state = next_state(self)

    def check_status(self):
        # TODO use to check status for user interface

        if not self.dead:
            if not self.knocked_out:
                self.process_commands()
                return

            self.stance = "DEFEND"
            self.set_formation()
            self.selected = False
            return

        self.dismount_building()
        self.selected = False
        return

    def check_on_screen(self):
        if self.level.camera_controller.main_camera.pointInsideFrustum(self.center.copy()):
            self.on_screen = True
        else:
            self.on_screen = False

        self.set_visible(self.on_screen)

    def update(self):
        # TODO integrate pause, dead and other behavior in to states

        self.debug_text = ""

        self.check_status()
        self.check_on_screen()

        if not self.ended:
            if not self.level.paused:
                self.state_machine()

    def infantry_update(self):
        pass

    def set_formation(self):
        pass

    def deploy(self, deploying):

        adjust = -0.002
        if deploying:
            adjust = 0.002

        self.deployed = min(1.0, max(0.0, self.deployed + adjust))

    def get_target(self, origin):
        target_vector = self.center.copy() - origin.center.copy()
        return None, target_vector

    def death_effect(self):
        pass

    def model_death_effect(self):
        pass


class Vehicle(Agent):
    def __init__(self, level, load_name, location, team, agent_id=None, load_dict=None):
        self.agent_type = "VEHICLE"
        self.stance_speed = 1.0
        self.wait_for_infantry = True
        self.aligning = False
        self.gun_timer = 0.0

        super().__init__(level, load_name, location, team, agent_id, load_dict)

        self.tow_hook = bgeutils.get_ob("tow_hook", self.box.childrenRecursive)
        self.trails = VehicleTrails(self)
        self.set_formation()

    def get_weapons(self):
        for weapon in self.stats.weapons:
            weapon.link_agent(self)
            self.weapons.append(weapon)

    def stowing_gun(self):
        if self.stats.artillery:
            self.deploy(False)

    def aligning_gun(self):

        # TODO handle rotating gun on anti-tank artillery

        angle_target = self.agent_targeter.hull_angle
        angle_target = min(0.4, max(-0.4, angle_target))

        if self.angled > angle_target + 0.01:
            self.angled -= 0.01
        elif self.angled < angle_target - 0.01:
            self.angled += 0.01

        moving = not self.movement.done

        if self.stats.artillery:
            if moving:
                self.stowing_gun()
                return True

            if self.ammo <= 0.0:
                self.stowing_gun()
                return True

            target = self.agent_targeter.enemy_target
            target_distance = self.agent_targeter.target_distance

            if not target:
                self.stowing_gun()
                return True
            else:
                deploy_angle = min(1.0, target_distance / 36.0)
                if self.deployed < (deploy_angle - 0.1):
                    self.deploy(True)
                    return True

                if self.deployed > (deploy_angle + 0.1):
                    self.deploy(False)
                    return True

        return False

    def load_stats(self):
        tiles = bge.logic.globalDict["profiles"][bge.logic.globalDict["active_profile"]]["vehicles"][self.load_name]
        self.stats = vehicle_stats.VehicleStats(tiles)
        self.stats.faction_number = self.team

        if self.stats.chassis_size > 3:
            self.size = 2
        else:
            self.size = 1

        self.initial_health = self.health = self.stats.durability
        self.ammo = self.stats.ammo
        self.get_weapons()
        self.best_weapon = self.stats.best_weapon
        self.set_stats()

    def update_stats(self):
        self.set_stats()
        self.set_speed()

    def attack_facing(self, other_agent_position):

        local_y = self.movement_hook.getAxisVect([0.0, 1.0, 0.0])
        target_vector = self.box.worldPosition.copy() - other_agent_position
        if target_vector.length == 0.0:
            target_vector = mathutils.Vector([0.0, 1.0, 0.0])

        angle = local_y.angle(target_vector)
        return angle

    def get_attack_facing(self, other_agent_position):

        has_turret = False
        if self.stats.turret_size > 0:
            has_turret = True

        angle = self.attack_facing(other_agent_position)
        facing = "FLANKS"
        if math.degrees(angle) > 90:
            facing = "FRONT"

        return [has_turret, facing, self.stats.armor]

    def set_stats(self):
        self.accuracy = float(self.rank) + self.stats.stability
        self.resistance = float(self.rank)
        resistance = self.resistance * 0.05

        self.shock = max(0.0, self.shock - resistance)

        # if self.shock > 100:
        #     self.knocked_out = True
        # else:
        #     self.knocked_out = False

        off_road_speed = bgeutils.interpolate_float(self.stats.speed[0], self.stats.speed[1], self.off_road)
        off_road_handling = bgeutils.interpolate_float(self.stats.handling[0], self.stats.handling[1], self.off_road)

        self.max_speed = off_road_speed * 0.00075
        self.handling = off_road_handling * 0.001
        self.turret_speed = self.stats.turret_speed * 0.001

        if self.shock > 40:
            self.max_speed *= 0.5
            self.handling *= 0.5

        elif self.shock > 20:
            self.max_speed *= 0.75
            self.handling *= 0.75

        # TODO find a way to show crippling damage without vehicle getting stuck

        damage_mod = 1.0
        damage_degree = self.mechanical_damage / self.stats.reliability

        if damage_degree > 1.0:
            damage_mod = 0.5

        if damage_degree > 2.0:
            self.crippled = True
        else:
            self.crippled = False

        self.max_speed *= damage_mod
        self.handling *= damage_mod

        self.get_best_penetration()

    def handle_weapons(self):
        # TODO make weapons dependent on agent states

        self.aligning = self.aligning_gun()

        for weapon in self.weapons:
            weapon.update()

        self.gun_timer += 1

        if self.gun_timer > 12:
            self.gun_timer = 0
            self.shoot_weapons()

    def shoot_weapons(self):
        for weapon in self.weapons:
            shooting = weapon.shoot()
            if shooting:
                return

    def check_status(self):
        # TODO set some stats to update on move
        # TODO handle most of this in agent states

        if not self.dead:
            self.is_damaged = -1
            self.has_ammo = 1
            self.is_shocked = -1
            self.is_sentry = False
            self.is_carrying = False
            # is_carrying = False

            if not self.knocked_out:
                if self.on_screen:
                    if self.ammo <= 0.0:
                        self.has_ammo = -1
                    elif self.ammo < 0.25:
                        self.has_ammo = 0

                    if self.shock > 40:
                        self.is_shocked = 1
                    elif self.shock > 20:
                        self.is_shocked = 0

                    if self.stats.has_commander:
                        if self.stance == "SENTRY":
                            self.is_sentry = True

                    if self.occupier:
                        self.is_carrying = True

                    self.is_damaged = -1
                    if self.mechanical_damage > 0:
                        if self.crippled:
                            self.is_damaged = 1
                        else:
                            self.is_damaged = 0

                self.process_commands()
                return

            self.stance = "DEFEND"
            self.set_formation()
            self.selected = False
            return

        self.selected = False
        return

    def handle_on_fire(self):
        if self.on_fire:
            print("{} is on fire!".format(self.agent_id))

    def vehicle_explode(self):
        if not self.dead:

            command = {"label": "EXPLOSION", "effect": "DUMMY_EXPLOSION", "damage": 100,
                       "position": self.center, "agent": self}

            self.level.commands.append(command)

            self.dead = True

    def update(self):

        # TODO integrate pause, dead and other behavior in to states

        self.debug_text = ""

        self.check_on_screen()
        self.check_status()

        if not self.ended:
            if not self.level.paused:
                self.state_machine()

    def get_best_penetration(self):
        best_penetration = 0

        for weapon in self.weapons:
            if weapon.penetration > best_penetration:
                best_penetration = weapon.penetration

        self.best_penetration = best_penetration

    def set_formation(self):

        hatch_open = False

        if self.stance == "AGGRESSIVE":
            self.stance_speed = 0.75
            self.shooting_bonus = 0.75

        if self.stance == "SENTRY":
            self.stance_speed = 0.5
            self.shooting_bonus = 0.75
            hatch_open = True

        if self.stance == "DEFEND":
            self.stance_speed = 0.5
            self.shooting_bonus = 1.0

        if self.stance == "FLANK":
            self.stance_speed = 1.0
            self.shooting_bonus = 0.5

        self.model.set_open_hatch(hatch_open)

    def set_speed(self):

        if self.movement.target:
            stowing_target = 0.0
            if self.movement.target_direction:
                self.throttle_target = self.stance_speed * 0.3
            elif self.movement.target == self.navigation.destination:
                self.throttle_target = self.stance_speed * 0.3
            else:
                self.throttle_target = self.stance_speed

        elif self.movement.target_direction:
            stowing_target = 0.0
            self.throttle_target = self.stance_speed * 0.75
        else:
            stowing_target = 1.0
            self.throttle_target = 0.0

        self.stowed = bgeutils.interpolate_float(self.stowed, stowing_target, 0.02)

        self.throttle = bgeutils.interpolate_float(self.throttle, self.throttle_target, self.handling)
        speed_mod = self.throttle * self.stance_speed
        display_mod = self.throttle_target * self.stance_speed

        self.speed = self.max_speed * speed_mod
        self.turning_speed = self.handling * speed_mod

        self.display_speed = (self.max_speed * display_mod) * 5.0
        if self.reverse:
            self.speed *= 0.8
            self.display_speed *= -0.8

    def add_box(self):
        super().add_box()
        self.model = model_display.VehicleModel(self.tilt_hook, self, scale=0.5)

    def process_hits(self):

        hits = self.hits

        # command = {"label": "HIT", "sector": sector, "weapon": weapon, "agent": agent}

        # command = {"label": "SPLASH_DAMAGE", "sector": None, "damage": effective_damage,
        #            "agent": agent}
        # command = {"label": "HIT", "sector": sector, "weapon": weapon, "agent": agent}

        sectors = ["BOTTOM", "TOP", "FRONT", "FLANKS", "TURRET"]

        for hit in hits:

            fire_chance = False
            explosion_chance = False
            damage_chance = False
            knockout_chance = False

            label = hit["label"]
            # TODO give XP to killing agent

            enemy_agent = hit["agent"]
            sector = hit["sector"]
            origin = hit["origin"]

            splash_damage = label == "SPLASH_DAMAGE"

            if splash_damage:
                damage_chance = True
                damage = hit["damage"]
                penetration = damage * 0.1
            else:
                weapon = hit["weapon"]
                damage = weapon.power
                penetration = weapon.penetration

            attack_vector = self.center.copy() - origin
            attack_distance = attack_vector.length

            penetration -= (attack_distance * 0.25)
            penetration *= random.uniform(0.5, 1.0)

            hit_angle = self.attack_facing(origin)
            facing = "FLANKS"
            if math.degrees(hit_angle) > 90:
                facing = "FRONT"

            hit_locations = []
            for t in range(self.stats.turret_size):
                hit_locations.append("TURRET")
            for c in range(self.stats.chassis_size):
                hit_locations.append(facing)

            hit_location = random.choice(hit_locations)
            critical_location = random.choice(self.stats.crits[hit_location])
            armor_value = self.stats.armor[hit_location]
            max_chance = 6

            if not splash_damage:
                if "WEAK_SPOT" in self.stats.flags:
                    if random.randint(0, 10) == 0:
                        armor_value = 0.0

                if critical_location == "DRIVE":
                    armor_value *= 0.5
                    damage_chance = True

                if critical_location == "ENGINE":
                    damage_chance = True
                    fire_chance = True
                    explosion_chance = True

                if critical_location == "WEAPON":
                    if "MANTLET" not in self.stats.flags:
                        armor_value *= 0.5

                    fire_chance = True
                    explosion_chance = True

                if critical_location == "CREW":
                    knockout_chance = True

                if critical_location == "UTILITY":
                    explosion_chance = True
                    if "EXTRA_FUEL" in self.stats.flags:
                        fire_chance = True

                if critical_location == "ARMOR":
                    armor_value *= 2.0

                if critical_location == "EMPTY":
                    armor_value *= 2.0

            if sector == "TOP":
                if "OPEN_TOP" in self.stats.flags:
                    knockout_chance = True
                    armor_value = 0.0
                elif "ANTI_AIRCRAFT" in self.stats.flags:
                    knockout_chance = True
                    armor_value = 0.0
                else:
                    if self.stance == "SENTRY":
                        if "COMMANDER" in self.stats.flags:
                            if random.randint(0, max_chance) == 0:
                                knockout_chance = True
                                armor_value = 0.0

                    if "EXTRA_PLATES" in self.stats.flags:
                        armor_value *= 0.5
                    else:
                        armor_value *= 0.25

            if sector == "BOTTOM":
                damage_chance = True
                if "EXTRA_PLATES" in self.stats.flags:
                    armor_value *= 0.5
                else:
                    armor_value *= 0.25

            penetrated = penetration > armor_value
            damage *= random.uniform(0.5, 1.0)

            if penetrated:
                self.health -= damage
                self.shock += damage

                if "EXTRA_SAFETY" in self.stats.flags:
                    max_chance = 12

                if "DANGEROUS_DESIGN" in self.stats.flags:
                    max_chance = 3

                if fire_chance:
                    if random.randint(0, max_chance * 2) == 0:
                        self.knocked_out = True
                        self.on_fire = True

                if explosion_chance:
                    if random.randint(0, max_chance * 4) == 0:
                        self.vehicle_explode()

                if knockout_chance and not self.knocked_out:
                    if random.randint(0, max_chance) == 0:
                        crew_damage = int(damage * 0.1)
                        if crew_damage > 0:
                            if random.randint(0, crew_damage) > self.stats.crew:
                                self.knocked_out = True

                if damage_chance:
                    if random.randint(0, max_chance) == 0:
                        self.mechanical_damage += 1

            else:
                if damage_chance:
                    if random.randint(0, max_chance * 2) == 0:
                        self.shock += damage
                        self.mechanical_damage += 1

            if not splash_damage:
                self.add_hit_effect(damage, penetrated)

            recoil_vector = origin.copy() - self.center.copy()
            recoil_vector.z = 0.0

            recoil_length = min(0.018, ((damage * 0.5) / self.stats.weight) * 0.005)
            recoil_vector.length = recoil_length
            self.movement.recoil += recoil_vector

        if self.health < 0 and not self.dead:
            self.dead = True

            if random.uniform(0.0, 6.0) < self.ammo:
                self.vehicle_explode()

        self.hits = []

    def add_hit_effect(self, damage_value, penetrated):

        damage_value *= random.uniform(0.5, 1.0)

        tile = self.level.get_tile(self.location)
        if penetrated:
            particles.NormalHit(self.level, tile, damage_value)

    def model_death_effect(self):
        if self.model:
            self.model.display_death()

    def death_effect(self):
        tile = self.level.get_tile(self.location)
        particles.DeathExplosion(self.level, tile, 100.0)


class Artillery(Vehicle):
    def __init__(self, level, load_name, location, team, agent_id=None, load_dict=None):

        self.avoid_radius = 4
        self.spacing = 1.5
        self.prone = False
        self.size = 0
        self.stance_speed = 1.0
        self.wait_for_infantry = True
        self.aligning = False
        self.gun_timer = 0.0
        self.walk_mod = 1.0

        super().__init__(level, load_name, location, team, agent_id, load_dict)
        self.formation = []
        self.add_squad(load_dict)

        self.set_formation()

    def get_agent_type(self):
        return "ARTILLERY"

    def infantry_update(self):
        for soldier in self.soldiers:
            soldier.update()
            soldier.visible = True

    def add_box(self):
        box = self.level.own.scene.addObject("agent", self.level.own, 0)

        self.box = box
        self.movement_hook = bgeutils.get_ob("hook", self.box.childrenRecursive)
        self.tilt_hook = bgeutils.get_ob("tilt", self.box.childrenRecursive)
        self.model = model_display.ArtilleryModel(self.tilt_hook, self, scale=0.5)

    def set_starting_formation(self):

        points = self.model.crew_adders

        for point in points:
            position = point.worldPosition.copy() - self.movement_hook.worldPosition.copy()
            position.rotate(self.movement_hook.worldOrientation.copy())

            self.formation.append(position)

    def add_squad(self, load_dict):
        self.set_starting_formation()
        self.set_formation()

        points = self.model.crew_adders[:self.stats.crew]
        soldier = "GUN CREW"

        if load_dict:
            for soldier_details in load_dict["soldiers"]:
                solider = soldier_details["infantry_type"]
                self.soldiers.append(ArtilleryMan(self, solider, 0, load_dict=soldier_details))
        else:
            for i in range(len(points)):
                self.soldiers.append(ArtilleryMan(self, soldier, i))

    def set_formation(self):

        if self.stance == "AGGRESSIVE":
            self.prone = False
            self.stance_speed = 0.75
            self.shooting_bonus = 0.75

        if self.stance == "SENTRY":
            self.prone = False
            self.stance_speed = 0.5
            self.shooting_bonus = 0.75

        if self.stance == "DEFEND":
            self.prone = True
            self.stance_speed = 0.5
            self.shooting_bonus = 1.0

        if self.stance == "FLANK":
            self.prone = False
            self.stance_speed = 1.0
            self.shooting_bonus = 0.5

    def process_hits(self):

        hits = self.hits

        # command = {"label": "HIT", "sector": sector, "weapon": weapon, "agent": agent}

        # command = {"label": "SPLASH_DAMAGE", "sector": None, "damage": effective_damage,
        #            "agent": agent}
        # command = {"label": "HIT", "sector": sector, "weapon": weapon, "agent": agent}

        for hit in hits:

            explosion_chance = False
            knockout_chance = False

            label = hit["label"]
            # TODO give XP to killing agent

            enemy_agent = hit["agent"]
            sector = hit["sector"]
            origin = hit["origin"]

            splash_damage = label == "SPLASH_DAMAGE"

            if splash_damage:
                knockout_chance = True
                damage = hit["damage"]
                penetration = damage * 0.5
            else:
                weapon = hit["weapon"]
                damage = weapon.power
                penetration = weapon.penetration

            attack_vector = self.center.copy() - origin
            attack_distance = attack_vector.length

            penetration -= (attack_distance * 0.25)
            penetration *= random.uniform(0.5, 1.0)

            hit_angle = self.attack_facing(origin)
            facing = "FLANKS"
            if math.degrees(hit_angle) > 90:
                facing = "FRONT"

            hit_locations = []
            for t in range(self.stats.turret_size):
                hit_locations.append("TURRET")
            for c in range(self.stats.chassis_size):
                hit_locations.append(facing)

            hit_location = random.choice(hit_locations)
            critical_location = random.choice(self.stats.crits[hit_location])
            armor_value = self.stats.armor[hit_location]
            max_chance = 6

            if not splash_damage:
                if "WEAK_SPOT" in self.stats.flags:
                    if random.randint(0, 10) > 9:
                        armor_value *= 0.5

                if critical_location == "WEAPON":
                    if "MANTLET" not in self.stats.flags:
                        armor_value *= 0.5
                    explosion_chance = True

                if critical_location == "CREW":
                    knockout_chance = True

                if critical_location == "ARMOR":
                    armor_value *= 2.0

                if critical_location == "EMPTY":
                    armor_value *= 2.0

                if sector == "TOP":
                    knockout_chance = True
                    armor_value = 0.0

                if sector == "BOTTOM":
                    armor_value = 0.0

            penetrated = penetration > armor_value
            damage *= random.uniform(0.5, 1.0)

            if penetrated:
                self.health -= damage
                self.shock += damage

                if "EXTRA_SAFETY" in self.stats.flags:
                    max_chance = 12

                if "DANGEROUS_DESIGN" in self.stats.flags:
                    max_chance = 3

                if explosion_chance:
                    if random.randint(0, max_chance * 4) == 0:
                        self.vehicle_explode()

                if knockout_chance and not self.knocked_out:
                    if random.randint(0, max_chance) == 0:
                        crew_damage = int(damage * 0.1)
                        if crew_damage > 0:
                            if random.randint(0, crew_damage) > self.stats.crew:
                                self.knocked_out = True
                                self.crew_killed()

            else:
                if knockout_chance and not self.knocked_out:
                    if random.randint(0, max_chance) == 0:
                        crew_damage = int(damage * 0.1)
                        if crew_damage > 0:
                            if random.randint(0, crew_damage) > self.stats.crew:
                                self.knocked_out = True
                                self.crew_killed()

            self.add_hit_effect(damage, penetrated)

            recoil_vector = origin.copy() - self.center.copy()
            recoil_vector.z = 0.0

            recoil_length = min(0.018, ((damage * 0.5) / self.stats.weight) * 0.005)
            recoil_vector.length = recoil_length
            self.movement.recoil += recoil_vector

        if self.health < 0 and not self.dead:
            self.dead = True

            if random.uniform(0.0, 6.0) < self.ammo:
                self.vehicle_explode()

        self.hits = []

    def death_effect(self):
        tile = self.level.get_tile(self.location)
        particles.DeathExplosion(self.level, tile, 10.0)

        self.crew_killed()

    def crew_killed(self):
        for soldier in self.soldiers:
            soldier.toughness = 0

    def model_death_effect(self):
        if self.model:
            self.model.display_death()


class Infantry(Agent):
    def __init__(self, level, load_name, location, team, agent_id=None, load_dict=None):
        self.avoid_radius = 4
        self.spacing = 1.5
        self.prone = False
        self.size = 0
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

    def get_agent_type(self):
        return "INFANTRY"

    def get_center(self):

        center = self.get_infantry_center()

        if center:
            self.center = center
        else:
            self.center = self.box.worldPosition.copy()

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

            health = 0
            for soldier in self.soldiers:
                health += soldier.toughness

            self.initial_health = health

    def set_occupied(self, target_tile, occupied_list=None):
        pass

    def update_stats(self):

        self.accuracy = float(self.rank)
        self.resistance = float(self.rank)

        resistance = self.resistance * 0.05
        self.shock = max(0.0, self.shock - resistance)

        combat_stances = ["DEFEND", "AGGRESSIVE"]

        if self.shock > 50 and self.stance not in combat_stances:
            self.stance = "DEFEND"
            self.set_formation()

        # TODO handle shocked units becoming knocked out

        # if self.shock > 100:
        #     self.knocked_out = True
        # else:
        #     self.knocked_out = False

        self.get_best_penetration()
        self.set_speed()

    def get_best_penetration(self):

        best_penetration = 0

        for soldier in self.soldiers:
            if soldier.grenade:
                if soldier.grenade.ammo > 0:
                    best_penetration = 60

            if soldier.weapon.ammo > 0.0:
                if soldier.weapon.power > best_penetration:
                    best_penetration = soldier.weapon.power

        self.best_penetration = best_penetration

    def check_status(self):

        if not self.dead:
            if self.on_screen:
                self.has_ammo = 1
                self.is_sentry = False
                commanders = ["COMMANDER", "OBSERVER", "OFFICER"]

                out_of_grenades = 0
                out_of_ammo = 0

                if self.shock > 40:
                    self.is_shocked = 1
                elif self.shock > 20:
                    self.is_shocked = 0
                else:
                    self.is_shocked = -1

                for soldier in self.soldiers:
                    if self.stance == "SENTRY":
                        if soldier.special in commanders:
                            self.is_sentry = True
                    if soldier.weapon.ammo <= 0.0:
                        out_of_ammo += 1
                    if soldier.grenade:
                        if soldier.grenade.ammo <= 0:
                            out_of_grenades += 1
                    else:
                        out_of_grenades -= 1

                if out_of_grenades >= len(self.soldiers):
                    self.has_ammo -= 1
                if out_of_ammo >= len(self.soldiers):
                    self.has_ammo -= 2
                elif out_of_ammo >= int(len(self.soldiers) * 0.5):
                    self.has_ammo -= 1

            dead = True
            for soldier in self.soldiers:
                if not soldier.dead:
                    dead = False

            if dead:
                self.dead = True
            else:
                if not self.knocked_out:
                    self.process_commands()
                    return

                self.stance = "DEFEND"
                self.set_formation()
                self.selected = False
                return

        self.dismount_building()
        self.selected = False
        return

    def check_on_screen(self):
        on_screen = False

        for soldier in self.soldiers:
            if self.level.camera_controller.main_camera.pointInsideFrustum(soldier.box.worldPosition.copy()):
                on_screen = True

        self.on_screen = on_screen
        self.set_visible(self.on_screen)

    def set_speed(self):
        infantry_speed = [soldier.speed for soldier in self.soldiers if not soldier.dead]
        if infantry_speed:
            self.speed = min(infantry_speed)
        else:
            self.speed = 0.0

    def get_target(self, origin):
        closest_soldier, best_vector = self.get_closest_soldier(origin)
        if closest_soldier:
            return closest_soldier, best_vector

        else:
            target_vector = self.center.copy() - origin.center.copy()
            return None, target_vector

    def get_closest_soldier(self, origin):

        closest = 2000
        closest_soldier = None
        best_vector = None

        for soldier in self.soldiers:
            if not soldier.dead:
                target_vector = soldier.box.worldPosition.copy() - origin.box.worldPosition.copy()
                distance = target_vector.length

                if distance < closest:
                    closest = distance
                    best_vector = target_vector
                    closest_soldier = soldier

        return closest_soldier, best_vector

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
            self.walk_mod = 0.85
            order = [self.deep, self.wide]
            spacing = self.spacing * 1.5
            scatter = spacing * 0.2

        if self.stance == "SENTRY":
            self.prone = False
            self.avoid_radius = 3
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
        self.box = box
        self.movement_hook = bgeutils.get_ob("hook", self.box.childrenRecursive)
        self.tilt_hook = bgeutils.get_ob("tilt", self.box.childrenRecursive)

    def infantry_update(self):
        for soldier in self.soldiers:
            soldier.update()
            if soldier.in_building or soldier.in_vehicle:
                soldier.visible = False
            else:
                soldier.visible = self.visible

    def get_infantry_center(self):
        center = mathutils.Vector()
        number = 0

        for soldier in self.soldiers:
            if not soldier.dead:
                center += soldier.box.worldPosition.copy()
                number += 1

        if number > 0:
            return center / number

    def mount_building(self, building_id):
        building = self.level.buildings.get(building_id)
        if building:
            if not building.occupier:
                self.navigation.stop = True
                self.enter_building = building_id
                self.destinations = [building.location]
                building.occupier = self.agent_id

    def dismount_building(self):
        building = self.level.buildings.get(self.enter_building)
        if building:
            building.occupier = None
            self.enter_building = None

    def mount_vehicle(self, vehicle_id):
        vehicle = self.level.agents.get(vehicle_id)
        if vehicle:
            if not vehicle.occupier:
                self.selected = False
                self.navigation.stop = True
                self.enter_vehicle = vehicle_id
                self.destinations = [vehicle.location]
                vehicle.occupier = self.agent_id

    def dismount_vehicle(self):
        vehicle = self.level.agents.get(self.enter_vehicle)
        if vehicle:
            self.navigation.stop = True
            vehicle.occupier = None
            self.enter_vehicle = None


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
        self.effect = stats["effect"]
        self.visible = True

        self.grenade = None
        if self.special == "SATCHEL_CHARGE":
            self.grenade = SoldierSatchelCharge(self, stats["grenades"])
        if self.special == "RIFLE_GRENADE":
            self.grenade = SoldierRifleGrenade(self, stats["grenades"])
        else:
            self.grenade = SoldierGrenade(self, stats["grenades"])

        self.weapon = SoldierWeapon(self)

        # TODO add other infantry stats here

        self.index = index
        self.box = self.agent.box.scene.addObject("infantry_dummy", self.agent.box, 0)
        self.sprite = self.box.children[0]
        self.location = self.agent.location
        self.direction = [0, 1]
        self.occupied = []
        self.in_building = None
        self.in_vehicle = None
        self.dead = False
        self.markers = []

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
            if self.weapon:
                self.weapon.update()
            if self.grenade:
                self.grenade.update()

    def set_occupied(self, target_tile):

        # setting_tile = self.agent.level.get_tile(target_tile)
        # if setting_tile:
        #     if not setting_tile["occupied"]:

        if self.occupied:
            self.clear_occupied()

        if not self.dead:
            display = False

            check_tile = self.agent.level.get_tile(target_tile)
            if check_tile:
                occupied = check_tile["occupied"]
                if not occupied:
                    self.agent.level.set_tile(target_tile, "occupied", self.agent.agent_id)
                    marker = None
                    if display:
                        marker = self.box.scene.addObject("debug_marker", self.box, 0)
                        tile = self.agent.level.map[bgeutils.get_key(target_tile)]
                        marker.worldPosition = mathutils.Vector(tile["position"]).to_3d()
                        marker.worldPosition.z = tile["height"]
                        self.markers.append(marker)
                    self.occupied.append([target_tile, marker])

    def clear_occupied(self):
        if self.occupied:
            for key_set in self.occupied:
                tile_key = key_set[0]
                self.agent.level.set_tile(tile_key, "occupied", None)
                marker = key_set[1]
                if marker:
                    marker.endObject()

            self.occupied = []

    def check_occupied(self, target_tile):

        current_location = self.agent.level.get_tile(self.location)
        inside = current_location["occupied"] or current_location["building"]
        if inside:
            if current_location["occupied"] != self.agent.agent_id:
                return False

        tile = self.agent.level.get_tile(target_tile)
        if tile:
            occupier_id = tile["occupied"]
            building_id = tile["building"]

            if occupier_id:
                if occupier_id == self.agent.enter_vehicle:
                    return False

                occupier = self.agent.level.agents.get(occupier_id)
                if occupier:
                    if occupier == self.agent and building_id == self.in_building:
                        return False

                    if occupier == self.agent and self.agent.enter_vehicle:
                        return False

                    return occupier

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
                        if occupier_id != self.agent.enter_vehicle:
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
                closest_door = building.get_closest_door(list(self.box.worldPosition.copy()))
                if closest_door:
                    destination = closest_door[:2]
            else:
                self.agent.dismount_building()

        if self.agent.enter_vehicle:
            vehicle = self.agent.level.agents.get(self.agent.enter_vehicle)
            if vehicle:
                if vehicle.dead:
                    self.agent.dismount_vehicle()
                else:
                    entry_point = vehicle.tow_hook
                    if entry_point:
                        destination = bgeutils.position_to_location(entry_point.worldPosition.copy())

        if not destination:
            location = self.agent.box.worldPosition.copy()
            location.z = 0.0

            offset = mathutils.Vector(self.agent.formation[self.index]).to_3d()
            offset.rotate(self.agent.movement_hook.worldOrientation.copy())

            destination = (location + offset).to_2d()

        return [round(axis) for axis in destination]

    def set_speed(self):

        if self.agent.shock > 40:
            walk_mod = self.agent.walk_mod * 0.5
        elif self.agent.shock > 20:
            walk_mod = self.agent.walk_mod * 0.85
        else:
            walk_mod = self.agent.walk_mod

        self.speed = (self.base_speed * walk_mod) * 0.005

    def shoot_weapon(self):
        if self.weapon:
            return self.weapon.shoot_weapon()

    def shoot_grenade(self):
        if self.grenade:
            return self.grenade.shoot()

    def save(self):

        save_dict = {"movement_target": self.movement.target, "movement_timer": self.movement.timer,
                     "destination": self.behavior.destination, "history": self.behavior.history,
                     "in_building": self.in_building, "behavior_action": self.behavior.action,
                     "in_vehicle": self.in_vehicle,
                     "behavior_timer": self.behavior.action_timer, "visible": self.visible,
                     "grenade_ammo": self.grenade.ammo, "grenade_timer": self.grenade.timer,
                     "toughness": self.toughness, "behavior_prone": self.behavior.prone, "index": self.index,
                     "prone": self.agent.prone, "direction": self.direction, "location": self.location,
                     "infantry_type": self.infantry_type, "weapon_timer": self.weapon.timer,
                     "weapon_ammo": self.weapon.ammo, "dead": self.dead}

        self.clear_occupied()
        return save_dict

    def reload(self, load_dict):

        self.index = load_dict["index"]
        self.agent.prone = load_dict["prone"]
        self.direction = load_dict["direction"]
        self.location = load_dict["location"]
        self.in_building = load_dict["in_building"]
        self.in_vehicle = load_dict["in_vehicle"]
        self.visible = load_dict["visible"]

        self.mesh_name = static_dicts.soldiers()[self.infantry_type]["mesh_name"]

        self.movement.set_vectors()
        self.movement.set_position()
        self.movement.set_initial_position()

        self.behavior.destination = load_dict["destination"]
        self.behavior.history = load_dict["history"]
        self.behavior.prone = load_dict["behavior_prone"]
        self.behavior.action = load_dict["behavior_action"]
        self.behavior.action_timer = load_dict["behavior_timer"]
        self.toughness = load_dict["toughness"]

        self.weapon.timer = load_dict["weapon_timer"]
        self.weapon.ammo = load_dict["weapon_ammo"]
        self.grenade.ammo = load_dict["grenade_ammo"]
        self.grenade.timer = load_dict["grenade_timer"]

        self.dead = load_dict["dead"]

        self.behavior.update()
        self.animation.update()


class ArtilleryMan(InfantryMan):
    def __init__(self, agent, infantry_type, index, load_dict=None):
        self.agent = agent
        self.agent_type = "ARTILLERYMAN"

        super().__init__(agent, infantry_type, index, load_dict)

    def check_too_close(self, target_tile):
        return False

    def update(self):
        self.behavior.update()
        self.animation.update()
        self.movement.update()

    def set_occupied(self, target_tile):
        pass

    def clear_occupied(self):
        pass

    def check_occupied(self, target_tile):

        check_tile = self.agent.level.get_tile(target_tile)
        if not check_tile:
            return self

        return None

    def get_destination(self):
        self.set_speed()

        location = self.agent.box.worldPosition.copy()
        location.z = 0.0

        offset = self.agent.formation[self.index].copy()
        offset.rotate(self.agent.movement_hook.worldOrientation.copy())

        destination = location + offset
        target_tile = [round(axis) for axis in destination.to_2d()]

        for soldier in self.agent.soldiers:
            if soldier.location == target_tile:
                return self.location

        return target_tile


class SoldierGrenade(object):
    def __init__(self, infantryman, ammo):
        self.weapon_type = "ARTILLERY"
        self.infantryman = infantryman
        self.sound = None
        self.effect = None
        self.rating = 1
        self.ammo = ammo
        self.bullet = "GRENADE"
        self.total_accuracy = self.infantryman.agent.accuracy
        self.max_range = 8.0
        self.recharge = 0.002
        self.power = 20
        self.penetration = 10
        self.timer = 0.0
        self.action = "FIDGET"

    def update(self):

        recharge = self.recharge
        if self.infantryman.behavior.prone:
            recharge *= 0.5

        self.timer = min(1.0, self.timer + recharge)

    def get_ready(self):

        if self.ammo <= 0:
            return False

        if self.infantryman.in_building:
            return False

        if self.timer < 1.0:
            return False

        return True

    def shoot(self):

        action = None
        target = self.infantryman.agent.agent_targeter.enemy_target
        if target:

            target_vector = self.infantryman.box.worldPosition.copy() - target.center.copy()
            target_distance = target_vector.length

            in_range = self.max_range > target_distance

            self.total_accuracy = self.infantryman.agent.accuracy + 20.0
            if self.infantryman.agent.prone:
                self.total_accuracy *= 0.5

            if in_range and self.get_ready():

                command = {"label": "ARTILLERY", "agent": self.infantryman.agent, "weapon": self,
                           "hook": self.infantryman.box}

                self.infantryman.agent.level.commands.append(command)
                self.timer = 0.0
                self.ammo -= 1

                if self.sound:
                    sound_command = {"label": "SOUND_EFFECT",
                                     "content": (self.sound, self.infantryman.box, 0.5, 1.0)}
                    self.infantryman.agent.level.commands.append(sound_command)

                action = self.action

        return action


class SoldierSatchelCharge(SoldierGrenade):
    def __init__(self, infantryman, ammo):
        super().__init__(infantryman, ammo)
        self.bullet = "GRENADE"
        self.power = 30
        self.rating = 3
        self.penetration = 60


class SoldierRifleGrenade(SoldierGrenade):
    def __init__(self, infantryman, ammo):
        super().__init__(infantryman, ammo)
        self.bullet = "ROCKET"
        self.power = 20
        self.rating = 1
        self.max_range = 18.0
        self.sound = "I_ANTI_TANK"
        self.action = "SHOOTING"


class SoldierWeapon(object):
    def __init__(self, infantryman):
        self.weapon_type = "INFANTRY_WEAPON"
        self.infantryman = infantryman
        self.power = self.infantryman.power
        self.penetration = self.infantryman.power
        self.effect = self.infantryman.effect
        self.recharge = (self.infantryman.rof * 0.0015) * random.uniform(0.8, 1.0)
        self.flag = self.infantryman.special
        self.total_accuracy = self.infantryman.agent.accuracy
        self.effective_range = 0.0
        self.timer = 0.0
        self.ammo = 1.0

    def update(self):

        if self.ammo > 0.0:
            accuracy = self.infantryman.agent.accuracy
            recharge = self.recharge
            prone = self.infantryman.agent.prone

            if prone or self.infantryman.in_building:
                accuracy *= 2.0
                recharge *= 0.5

            if self.infantryman.agent.shock > 40:
                accuracy *= 0.5
                recharge *= 0.5

            elif self.infantryman.agent.shock > 20:
                accuracy *= 0.75
                recharge *= 0.75

            self.total_accuracy = accuracy
            self.effective_range = self.total_accuracy + self.power

            self.timer = min(1.0, self.timer + recharge)

    def get_ready(self):

        target = self.infantryman.agent.agent_targeter.enemy_target

        if not target:
            return False

        if self.infantryman.agent.enter_building and not self.infantryman.in_building:
            return False

        if self.infantryman.agent.knocked_out:
            return False

        if self.ammo > 0.0:
            if self.timer >= 1.0:
                penetration = self.power

                target_distance = self.infantryman.agent.agent_targeter.target_distance
                armor_facing = target.get_attack_facing(self.infantryman.box.worldPosition.copy())
                if armor_facing:
                    has_turret, facing, armor = armor_facing

                    lowest_armor = armor[facing] * 0.5

                    if has_turret:
                        if armor["TURRET"] < lowest_armor:
                            lowest_armor = armor["TURRET"]

                    penetration -= (target_distance * 0.25)

                    if penetration < lowest_armor:
                        return False

                return True

    def get_window(self):

        target = self.infantryman.agent.agent_targeter.enemy_target
        building = self.infantryman.agent.level.buildings.get(self.infantryman.in_building)

        valid_windows = []

        if target and building:
            angle_limit = 1.4
            windows = building.windows

            for window in windows:
                window_position = mathutils.Vector(window[0])
                window_angle = mathutils.Vector(window[1])
                target_vector = target.box.worldPosition.copy() - window_position
                target_angle = window_angle.angle(target_vector)

                if target_angle < angle_limit:
                    valid_windows.append(window_position)

            if valid_windows:
                return random.choice(valid_windows)

    def shoot_weapon(self):

        target = self.infantryman.agent.agent_targeter.enemy_target

        if target:
            if self.get_ready():
                target_distance = self.infantryman.agent.agent_targeter.target_distance

                if target_distance < 18.0:
                    # TODO check for armor penetration

                    if self.infantryman.in_building:
                        window_position = self.get_window()
                        if window_position:
                            origin = window_position
                        else:
                            return False
                    else:
                        origin = self.infantryman.box.worldPosition.copy()
                        origin.z += 0.5

                    command = {"label": "SMALL_ARMS", "weapon": self, "agent": self.infantryman.agent,
                               "origin": origin}

                    self.infantryman.agent.level.commands.append(command)
                    self.timer = 0.0
                    self.ammo -= 0.01

                    self.infantryman.direction = bgeutils.get_closest_vector(
                        self.infantryman.agent.agent_targeter.target_vector)

                    return True

        return False
