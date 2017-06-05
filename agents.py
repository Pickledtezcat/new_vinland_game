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
    accuracy = 6
    vision_distance = 0
    initial_health = 0

    stance = "AGGRESSIVE"
    agent_type = "VEHICLE"

    def __init__(self, level, load_name, location, team, agent_id=None, load_dict=None):

        self.level = level

        if not agent_id:
            self.agent_id = "{}${}".format(self.agent_type, self.level.get_new_id())
        else:
            self.agent_id = agent_id

        self.load_name = load_name
        self.team = team
        self.faction = self.level.factions[self.team]

        self.dead = False
        self.ended = False
        self.visible = True
        self.seen = False
        self.suspect = False

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

    def set_visible(self, setting):
        self.visible = setting

    def set_seen(self, setting):
        self.seen = setting

    def set_suspect(self, setting):
        self.suspect = setting

    def save(self):

        save_dict = {"agent_type": self.agent_type, "team": self.team, "location": self.location,
                     "direction": self.direction, "enter_building": self.enter_building,
                     "selected": self.selected, "state_name": self.state.name, "load_name": self.load_name,
                     "state_count": self.state.count, "movement_target": self.movement.target,
                     "movement_target_direction": self.movement.target_direction,
                     "movement_timer": self.movement.timer, "initial_health": self.initial_health,
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

        self.initial_health = agent_dict["initial_health"]

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
                    both_infantry = self.agent_type == "INFANTRY" and occupier.agent_type == "INFANTRY"

                    if not both_infantry:
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
                    if cam.pointInsideFrustum(self.box.worldPosition):
                        points = [cam.getScreenPosition(self.box)]
                        for soldier in self.soldiers:
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
                self.dismount_building()

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
                self.agent_targeter.set_target_id = None

            if command["label"] == "TARGET_ENEMY":
                # self.dismount_building()
                target_id = command["target_id"]

                self.agent_targeter.set_target_id = target_id
                self.navigation.stop = True
                self.destinations = []

            if command["label"] == "STANCE_CHANGE":
                stance = command["stance"]
                self.stance = stance
                self.set_formation()

            if command["label"] == "ENTER_BUILDING":
                if self.agent_type == "INFANTRY":
                    self.mount_building(command["target_id"])

        self.commands = []

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

    def set_starting_state(self):
        self.state = AgentStartUp(self)

    def state_machine(self):
        self.state.update()

        next_state = self.state.transition
        if next_state:
            self.state.end()
            self.state = next_state(self)

    def check_dead(self):
        pass

    def update(self):
        # TODO integrate pause, dead and other behavior in to states

        # self.debug_text = "{}\n{}".format(str(self.agent_id), str(self.agent_targeter.enemy_target_id))
        self.debug_text = ""

        if not self.dead:
            self.check_dead()
            self.process_commands()
        else:
            self.selected = False

        if not self.ended:
            if not self.level.paused:
                self.state_machine()

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

            health = 0
            for soldier in self.soldiers:
                health += soldier.toughness

            self.initial_health = health

    def set_occupied(self, target_tile, occupied_list=None):
        pass

    def update_stats(self):

        self.set_soldiers_visible()
        self.set_speed()

    def set_soldiers_visible(self):
        # TODO set other visibility cases

        for soldier in self.soldiers:
            if soldier.in_building:
                soldier.visible = False
            else:
                soldier.visible = self.visible

    def check_dead(self):
        dead = True
        for soldier in self.soldiers:
            if not soldier.dead:
                dead = False

        if dead:
            self.dead = True

    def set_speed(self):
        infantry_speed = [soldier.speed for soldier in self.soldiers if not soldier.dead]
        if infantry_speed:
            self.speed = min(infantry_speed)
        else:
            self.speed = 0.0

    def get_closest_soldier(self, target):
        closest = 2000
        closest_soldier = None

        for soldier in self.soldiers:
            if not soldier.dead:
                target_vector = soldier.box.worldPosition.copy() - target
                distance = target_vector.length

                if distance < closest:
                    closest = distance
                    closest_soldier = soldier

        return closest_soldier, closest

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
            if self.weapon:
                self.weapon.update()
            if self.grenade:
                self.grenade.update()

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
            building_id = tile["building"]

            if occupier_id:
                occupier = self.agent.level.agents.get(occupier_id)
                if occupier:
                    if occupier == self.agent and building_id == self.in_building:
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
                     "behavior_timer": self.behavior.action_timer, "visible": self.visible,
                     "grenade_ammo": self.grenade.ammo, "grenade_timer": self.grenade.timer,
                     "toughness": self.toughness, "behavior_prone": self.behavior.prone, "index": self.index,
                     "prone": self.agent.prone, "direction": self.direction, "location": self.location,
                     "infantry_type": self.infantry_type, "occupied": self.occupied, "weapon_timer": self.weapon.timer,
                     "weapon_ammo": self.weapon.ammo, "dead": self.dead}

        self.clear_occupied()
        return save_dict

    def reload(self, load_dict):

        self.index = load_dict["index"]
        self.agent.prone = load_dict["prone"]
        self.direction = load_dict["direction"]
        self.location = load_dict["location"]
        self.in_building = load_dict["in_building"]
        self.visible = load_dict["visible"]

        self.mesh_name = static_dicts.soldiers()[self.infantry_type]["mesh_name"]

        self.movement.set_vectors()
        self.movement.set_position()

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


class SoldierGrenade(object):
    # TODO save and load grenade states and artillery bullets

    def __init__(self, infantryman, ammo):
        self.weapon_type = "ARTILLERY"
        self.infantryman = infantryman
        self.sound = None
        self.ammo = ammo
        self.bullet = "GRENADE"
        self.accuracy = self.infantryman.agent.accuracy
        self.max_range = 8
        self.recharge = 0.01
        self.timer = 0.0
        self.ready = False
        self.in_range = False
        self.action = "FIDGET"

    def update(self):

        if self.ammo > 0:
            if not self.infantryman.agent.prone:
                if not self.infantryman.in_building:

                    self.timer = min(1.0, self.timer + self.recharge)
                    if self.timer >= 1.0:
                        self.ready = True

    def get_target(self):
        target_id = self.infantryman.agent.agent_targeter.enemy_target_id
        target = self.infantryman.agent.level.agents.get(target_id)
        return target_id, target

    def check_in_range(self):
        target_id, target = self.get_target()
        if target:
            distance = (target.box.worldPosition.copy() - self.infantryman.box.worldPosition.copy()).length
            if distance <= self.max_range:
                return True

    def shoot(self):
        target_id, target = self.get_target()
        action = None
        origin = self.infantryman.box.worldPosition.copy()
        accuracy = self.accuracy

        if target and self.ready and self.check_in_range():
            command = {"label": "ARTILLERY", "owner": self.infantryman.agent, "target_id": target_id,
                       "accuracy": accuracy, "origin": origin, "bullet": self.bullet, "effect": None}

            self.infantryman.agent.level.commands.append(command)
            self.ready = False
            self.timer = 0.0
            self.ammo -= 1

            if self.sound:
                bgeutils.sound_message("SOUND_EFFECT", ("I_{}".format(self.sound), self.infantryman.box, 0.5, 1.0))

            action = self.action

        return action


class SoldierSatchelCharge(SoldierGrenade):
    def __init__(self, infantryman, ammo):
        super().__init__(infantryman, ammo)
        self.bullet = "SATCHEL_CHARGE"


class SoldierRifleGrenade(SoldierGrenade):
    def __init__(self, infantryman, ammo):
        super().__init__(infantryman, ammo)
        self.bullet = "RIFLE_GRENADE"
        self.max_range = 18
        self.sound = "ANTI_TANK"
        self.action = "SHOOTING"


class SoldierWeapon(object):
    def __init__(self, infantryman):
        self.weapon_type = "INFANTRY_WEAPON"
        self.infantryman = infantryman
        self.power = self.infantryman.power
        self.sound = self.infantryman.sound
        self.recharge = (self.infantryman.rof * 0.0025) * random.uniform(0.8, 1.0)
        self.special = self.infantryman.special
        self.accuracy = self.infantryman.agent.accuracy
        self.timer = 0.0
        self.ammo = 1.0
        self.effect_timer = random.randint(0, 3)
        self.ready = False

    def update(self):

        if self.ammo > 0.0:
            prone = self.infantryman.agent.prone

            if prone:
                self.accuracy = self.infantryman.agent.accuracy * 2.0
                recharge = self.recharge * 0.5
            else:
                self.accuracy = self.infantryman.agent.accuracy
                recharge = self.recharge

            if self.infantryman.in_building:
                self.accuracy = self.infantryman.agent.accuracy * 2.0
                recharge = self.recharge * 0.5

            self.timer = min(1.0, self.timer + recharge)
            if self.timer >= 1.0:
                self.ready = True

        else:
            self.ready = False

        if self.infantryman.agent.enter_building and not self.infantryman.in_building:
            self.ready = False

    def check_in_range(self):
        target_id, target = self.get_target()
        if target:
            distance = (target.box.worldPosition.copy() - self.infantryman.box.worldPosition.copy()).length
            if distance <= 18:
                return True

    def get_target(self):
        target_id = self.infantryman.agent.agent_targeter.enemy_target_id
        target = self.infantryman.agent.level.agents.get(target_id)
        return target_id, target

    def get_window(self):
        target_id, target = self.get_target()
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
        target_id, target = self.get_target()

        if target and self.ready and self.check_in_range():

            effect = None

            if self.infantryman.in_building:
                window_position = self.get_window()
                if window_position:
                    origin = window_position
                else:
                    return False
            else:
                origin = self.infantryman.location

            if self.effect_timer > 2 or self.infantryman.in_building:
                self.effect_timer = 1
                if self.special == "RAPID_FIRE":
                    effect = "RAPID_YELLOW_STREAK"
                else:
                    effect = "YELLOW_STREAK"
            else:
                self.effect_timer += 1

            if self.special == "ANTI_TANK":
                effect = "RED_STREAK"

            effective_range = self.accuracy + self.power
            effective_power = self.power * random.uniform(0.0, 1.0)

            command = {"label": "SMALL_ARMS_SHOOT", "weapon": self, "owner": self.infantryman, "target_id": target_id,
                       "effect": effect, "origin": origin, "effective_range": effective_range,
                       "effective_power": effective_power}

            bgeutils.sound_message("SOUND_EFFECT", ("I_{}".format(self.sound), self.infantryman.box, 0.3, 1.0))
            self.infantryman.agent.level.commands.append(command)
            self.ready = False
            self.timer = 0.0
            self.ammo -= 0.01

            return True

        return False
