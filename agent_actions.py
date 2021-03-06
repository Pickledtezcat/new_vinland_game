import bge
import bgeutils
import mathutils
import random
import math


class AgentMovement(object):
    def __init__(self, agent):
        self.agent = agent
        self.target = None
        self.start_vector = None
        self.target_vector = None
        self.start_normal = None
        self.target_normal = None
        self.remaining = 0.0
        self.recoil = mathutils.Vector([0.0, 0.0, 0.0])
        self.tilt = 0.0
        self.damping = 0.03

        self.target_direction = None
        self.current_orientation = None
        self.target_orientation = None
        self.scale = 1.0

        self.timer = 0.0
        self.done = True
        self.set_vectors()

    def set_vectors(self):

        start_tile = self.agent.level.map[bgeutils.get_key(self.agent.location)]

        if start_tile["terrain"] > 128:
            self.agent.off_road = bgeutils.interpolate_float(self.agent.off_road, 1.0, 0.1)
        else:
            self.agent.off_road = bgeutils.interpolate_float(self.agent.off_road, 0.0, 0.1)

        self.start_vector = mathutils.Vector(start_tile["position"]).to_3d()
        self.start_vector.z = start_tile["height"]
        self.start_normal = mathutils.Vector(start_tile["normal"])

        self.target_vector = self.start_vector
        self.target_normal = self.start_normal

        self.current_orientation = mathutils.Vector(self.agent.direction).to_3d().to_track_quat("Y",
                                                                                                "Z").to_matrix().to_3x3()
        self.target_orientation = mathutils.Vector(self.agent.direction).to_3d().to_track_quat("Y",
                                                                                               "Z").to_matrix().to_3x3()

        start_direction = mathutils.Vector(self.agent.direction)
        end_direction = start_direction

        if self.target_direction:
            self.target_orientation = mathutils.Vector(self.target_direction).to_3d().to_track_quat("Y",
                                                                                                    "Z").to_matrix().to_3x3()
            end_direction = mathutils.Vector(self.target_direction)

        elif self.target:
            self.agent.set_occupied(self.target)
            target_tile = self.agent.level.map[bgeutils.get_key(self.target)]
            self.target_vector = mathutils.Vector(target_tile["position"]).to_3d()
            self.target_vector.z = target_tile["height"]
            self.target_normal = mathutils.Vector(target_tile["normal"])

        angle = start_direction.angle(end_direction)
        self.scale = angle / 3.142
        self.done = False
        self.timer = 0.0

    def update(self):

        if self.agent.fully_loaded():
            self.riding_vehicle()
        else:
            if self.scale > 0.0:
                turning_speed = self.agent.turning_speed / self.scale
            else:
                turning_speed = self.agent.turning_speed

            if self.target_direction:
                self.timer = min(1.0, self.timer + turning_speed)
                if self.timer >= 1.0:
                    self.agent.direction = self.target_direction
                    self.target_direction = None

            elif self.target:
                speed = self.agent.speed + self.remaining
                self.remaining = 0.0

                self.timer += speed
                if self.timer >= 1.0:
                    self.remaining = self.timer - 1.0
                    self.timer = 1.0
                    self.agent.location = self.target
                    self.target = None

            else:
                if not self.done:
                    self.done = True
                    self.agent.get_center()
                    self.agent.clear_occupied()
                    self.agent.set_occupied(self.agent.location)

            self.set_position()

    def riding_vehicle(self):

        riding = self.agent.level.agents.get(self.agent.enter_vehicle)

        if not riding.dead:
            self.load_movement(riding.location, None, 1.0)
        else:
            self.agent.dismount_vehicle()

    def set_aim(self):
        self.target_direction = self.agent.aim
        self.target = None
        self.set_vectors()

    def target_enemy(self):
        target_direction = self.agent.get_enemy_direction()

        if target_direction:
            if target_direction != self.agent.direction:
                self.target_direction = target_direction
                self.set_vectors()

    def set_position(self, set_timer=0.0):

        if set_timer:
            timer = set_timer
            damping = 1.0
        else:
            timer = self.timer
            damping = self.agent.damping

        if self.agent.agent_type == "VEHICLE":
            throttle = self.agent.throttle
            throttle_target = self.agent.throttle_target
            throttle_difference = (throttle - throttle_target)
            if self.agent.reverse:
                throttle_difference *= -1.0

            self.tilt = bgeutils.interpolate_float(self.tilt, throttle_difference, damping)

        self.recoil = self.recoil.lerp(mathutils.Vector([0.0, 0.0, 0.0]), damping)

        self.agent.box.worldPosition = self.start_vector.lerp(self.target_vector, timer)
        rotation = self.current_orientation.lerp(self.target_orientation, bgeutils.smoothstep(timer))
        self.agent.movement_hook.worldOrientation = rotation

        if self.agent.agent_type != "INFANTRY":
            normal = self.start_normal.lerp(self.target_normal, timer)
            local_y = self.agent.movement_hook.getAxisVect([0.0, 1.0, 0.0])

            tilt = self.tilt * 0.01

            z = self.recoil.copy() + mathutils.Vector([0.0, tilt, 1.0]).normalized()
            local_z = self.agent.tilt_hook.getAxisVect(z)

            target_vector = local_z.lerp(normal, damping)

            self.agent.tilt_hook.alignAxisToVect(local_y, 1, 1.0)
            self.agent.tilt_hook.alignAxisToVect(target_vector, 2, 1.0)

    def initial_position(self):
        self.set_position(set_timer=1.0)
        self.agent.set_occupied(self.agent.location)

    def load_movement(self, target, target_direction, timer):
        self.target = target
        self.target_direction = target_direction
        self.set_vectors()
        self.timer = timer
        self.set_position()
        self.agent.get_center()


class InfantryAction(object):
    def __init__(self, infantryman):
        self.infantryman = infantryman
        self.target = None
        self.direction = None
        self.timer = 0.0
        self.done = False

        self.start_vector = None
        self.target_vector = None

    def set_vectors(self):

        start_tile = self.infantryman.agent.level.map[bgeutils.get_key(self.infantryman.location)]
        self.start_vector = mathutils.Vector(start_tile["position"]).to_3d()
        self.start_vector.z = start_tile["height"]

        self.target_vector = self.start_vector

        if self.target:
            self.infantryman.set_occupied(self.target)
            target_tile = self.infantryman.agent.level.map[bgeutils.get_key(self.target)]
            self.target_vector = mathutils.Vector(target_tile["position"]).to_3d()
            self.target_vector.z = target_tile["height"]

        self.done = False
        self.timer = 0.0

    def set_initial_position(self):
        if self.target:
            target = self.target
        else:
            target = self.infantryman.location

        self.infantryman.set_occupied(target)

    def update(self):

        if self.infantryman.in_vehicle:
            self.riding_vehicle()
        else:
            if self.target:
                self.timer = min(1.0, self.timer + self.infantryman.speed)
                if self.timer >= 1.0:
                    self.infantryman.location = self.target
                    self.target = None

            else:
                if not self.done:
                    self.done = True

            if not self.done:
                self.set_position()

    def riding_vehicle(self):
        self.infantryman.clear_occupied()

        riding = self.infantryman.agent.level.agents.get(self.infantryman.agent.enter_vehicle)
        if riding:
            if not riding.dead:
                position = riding.tow_hook.worldPosition
                self.infantryman.box.worldPosition = position.copy()
                self.infantryman.location = bgeutils.position_to_location(position.copy())
                self.target = None
                self.done = True

    def set_position(self, set_timer=0.0):

        if set_timer:
            timer = set_timer
        else:
            timer = self.timer

        self.infantryman.box.worldPosition = self.start_vector.lerp(self.target_vector, timer)


class InfantryAnimation(object):
    def __init__(self, infantryman):
        self.infantryman = infantryman
        self.last_frame = -1
        self.frame = 0.0
        self.north = random.choice(["NE", "NW"])
        self.faction = self.infantryman.agent.faction
        self.set_frame("default", 0)
        self.last_action = None
        self.infantryman.sprite.visible = True

    def get_target_direction(self, action):

        shooting_actions = ["FACE_TARGET"]

        if action in shooting_actions:
            target = self.infantryman.agent.agent_targeter.enemy_target
            if target:
                target_vector = self.infantryman.agent.agent_targeter.target_vector
                return bgeutils.get_closest_vector(target_vector)

        if action == "FACE_GUN":
            target_vector = self.infantryman.agent.box.worldPosition.copy() - self.infantryman.box.worldPosition.copy()
            return bgeutils.get_closest_vector(target_vector)

        return self.infantryman.direction

    def update(self):

        behavior = self.infantryman.behavior
        prone = self.infantryman.behavior.prone
        timed_actions = ["DYING", "GO_PRONE", "GET_UP", "SHOOTING", "WAIT", "FINISHED", "FACE_TARGET"]
        dead_actions = ["DYING", "DEAD"]

        if not self.infantryman.visible:
            self.infantryman.sprite.visible = False
        else:
            self.infantryman.sprite.visible = True

            if behavior.action in timed_actions:
                self.frame = behavior.action_timer * 4.0

                if behavior.action == "SHOOTING" and self.infantryman.special == "RAPID_FIRE":
                    action_time = behavior.action_timer * 12
                    remainder = action_time % 3
                    self.frame = remainder * 4.0

            elif behavior.action == "DEAD":
                self.frame = 4.0
            else:
                animation_mod = 6.0
                if prone:
                    animation_mod = 8.0

                next_frame = self.frame + (self.infantryman.speed * animation_mod)
                if next_frame < 4.0:
                    self.frame = next_frame
                else:
                    self.frame = 0.0

            frame_number = min(3, int(self.frame))

            if behavior.action == "GET_TILE":
                if prone:
                    action = "prone_crawl"
                else:
                    action = "walk"

            elif behavior.action == "GO_PRONE":
                action = "go_prone"

            elif behavior.action == "GET_UP":
                action = "get_up"

            elif behavior.action == "SHOOTING":
                if prone:
                    action = "prone_shoot"
                else:
                    action = "shoot"

            elif behavior.action in dead_actions:
                if prone:
                    action = "prone_death"
                else:
                    action = "death"

                if behavior.action == "DEAD":
                    frame_number = 4

            elif behavior.action == "FIDGET":
                action = "default"
            else:
                if self.infantryman.behavior.prone:
                    action = "go_prone"
                    frame_number = 3
                else:
                    action = "default"
                    frame_number = 0

            if frame_number != self.last_frame or action != self.last_action:
                self.set_frame(action, frame_number)

    def set_frame(self, action, frame_number):
        self.last_frame = frame_number
        self.last_action = action

        north = self.north
        directions_dict = {(-1, -1): "W",
                           (-1, 0): "NW",
                           (-1, 1): north,
                           (0, 1): "NE",
                           (1, 1): "E",
                           (1, 0): "SE",
                           (1, -1): "S",
                           (0, -1): "SW"}

        direction = self.get_target_direction(self.infantryman.behavior.action)
        sprite_direction = directions_dict[tuple(direction)]
        mesh_name = self.infantryman.mesh_name
        frame_name = "{}_{}_{}${}_{}".format(self.faction, mesh_name, action, sprite_direction, frame_number)
        self.infantryman.sprite.replaceMesh(frame_name)


class InfantryBehavior(object):
    def __init__(self, infantryman):
        self.infantryman = infantryman
        self.destination = None
        self.history = []
        self.stop = False
        self.avoiding = None
        self.prone = False
        self.action_timer = 1.0
        self.action = "GET_TILE"
        self.fidget_count = random.randint(1, 12)

    def get_action(self):

        if not self.infantryman.agent.enter_building:
            self.infantryman.in_building = False

        if not self.infantryman.agent.enter_vehicle:
            self.infantryman.in_vehicle = False

        if self.action == "DYING":
            self.infantryman.dead = True
            self.infantryman.clear_occupied()
            return "DEAD"

        dying = self.infantryman.toughness <= 0

        if dying:
            return "DYING"

        avoiding = self.avoiding
        self.avoiding = self.infantryman.check_too_close(self.infantryman.location)

        if avoiding and not self.avoiding:
            return "WAIT"

        if self.avoiding:
            return "GET_TILE"

        if self.infantryman.agent.prone:
            if not self.prone:
                return "GO_PRONE"
        else:
            if self.prone:
                return "GET_UP"

        grenade = self.infantryman.shoot_grenade()
        if grenade:
            return grenade

        shooting = self.infantryman.shoot_weapon()
        if shooting:
            return "SHOOTING"

        destination = self.infantryman.get_destination()
        if destination != self.destination:
            self.destination = destination

        if self.infantryman.in_vehicle:
            return "IN_VEHICLE"

        if self.infantryman.location != self.destination:
            return "GET_TILE"
        else:
            if self.infantryman.agent.enter_building:
                self.infantryman.clear_occupied()
                self.history = [self.infantryman.location]
                self.infantryman.in_building = self.infantryman.agent.enter_building
                return "IN_BUILDING"

            if self.infantryman.agent.enter_vehicle:
                self.infantryman.clear_occupied()
                check_destination = self.infantryman.get_destination()
                if check_destination != self.destination:
                    return "GET_TILE"

                self.history = []
                self.infantryman.in_vehicle = self.infantryman.agent.enter_vehicle

                return "IN_VEHICLE"

            if self.infantryman.agent.agent_type == "ARTILLERY":
                self.history = [self.infantryman.location]
                # TODO make infantry face gun
                return "FACE_GUN"

            if self.infantryman.agent.agent_targeter.enemy_target:
                self.history = [self.infantryman.location]
                return "FACE_TARGET"

            self.history = [self.infantryman.location]

            if not self.prone:
                if self.fidget_count < 0:
                    self.fidget_count = random.randint(3, 12)
                    return "FIDGET"
                else:
                    self.fidget_count -= 1

            return "FINISHED"

    def update(self):
        if self.action != "DEAD":
            if self.infantryman.movement.done:
                if self.action_timer < 1.0:
                    self.action_timer = min(1.0, self.action_timer + 0.02)
                else:
                    if self.action == "GO_PRONE":
                        self.prone = True
                    if self.action == "GET_UP":
                        self.prone = False

                    self.action = self.get_action()

                    if self.action == "GET_TILE":
                        self.get_next_tile()
                        self.infantryman.close_up_formation()
                    else:
                        self.action_timer = 0.0
                        self.infantryman.close_up_formation()

    def get_next_tile(self):

        avoiding = self.avoiding

        search_array = [[1, 0], [1, 1], [0, 1], [1, -1], [-1, 0], [-1, 1], [0, -1], [-1, -1]]
        current_tile = self.infantryman.location

        if avoiding:
            local_y = avoiding.box.getAxisVect([0.0, 1.0, 0.0])
            local_y.length = avoiding.size

            reference = (avoiding.box.worldPosition.copy() + local_y).to_2d()
        else:
            reference = mathutils.Vector(self.destination).to_2d()

        target = current_tile
        choice = self.infantryman.direction

        closest = 10000.0
        furthest = 0.0
        free = 0

        for s in search_array:
            neighbor = [current_tile[0] + s[0], current_tile[1] + s[1]]
            neighbor_check = self.infantryman.check_occupied(neighbor)

            if not neighbor_check:
                free += 1
                if neighbor not in self.history:

                    distance = (reference - mathutils.Vector(neighbor)).length
                    if bgeutils.diagonal(s):
                        distance += 0.4

                    if avoiding:
                        if distance > furthest:
                            furthest = distance
                            choice = s
                            target = neighbor
                    else:
                        if distance < closest:
                            closest = distance
                            choice = s
                            target = neighbor

        if free > 0:
            self.infantryman.direction = choice
            self.infantryman.movement.target = target
            self.infantryman.movement.set_vectors()

            if len(self.history) > 8:
                self.history = [self.infantryman.location, target]
            else:
                self.history.append(target)
        else:
            self.action = "WAIT"


class AgentNavigation(object):
    def __init__(self, agent):
        self.agent = agent
        self.destination = None
        self.history = []
        self.stop = False

    def get_next_destination(self):
        self.history = [self.agent.location]
        if self.agent.destinations:
            self.destination = self.agent.destinations.pop(0)

    def get_next_tile(self):
        search_array = [[1, 0], [1, 1], [0, 1], [1, -1], [-1, 0], [-1, 1], [0, -1], [-1, -1]]
        current_tile = self.agent.location
        touching_infantry = False
        next_facing = None
        next_target = None
        closest = 10000.0

        for s in search_array:
            neighbor = [current_tile[0] + s[0], current_tile[1] + s[1]]
            neighbor_check = self.agent.check_occupied(neighbor)

            if not neighbor_check:
                if neighbor not in self.history:

                    distance = (mathutils.Vector(self.destination) - mathutils.Vector(neighbor)).length
                    if bgeutils.diagonal(s):
                        distance += 0.4

                    if self.agent.reverse:
                        s = [s[0] * -1, s[1] * -1]

                    if s != self.agent.direction:
                        distance += 0.2

                    if distance < closest:
                        closest = distance
                        next_facing = s
                        next_target = neighbor

            elif self.agent.agent_type != "INFANTRY":
                for agent in neighbor_check:
                    if agent.agent_type == "INFANTRY":
                        if agent.team == self.agent.team:
                            if agent.agent_id != self.agent.occupier:
                                touching_infantry = True

        return next_facing, next_target, touching_infantry

    def update(self):

        if self.agent.fully_loaded():
            self.destination = None
            self.history = []
            self.stop = True

        elif self.agent.movement.done:
            if self.stop:
                self.stop = False
                self.destination = None

            if not self.destination:
                self.get_next_destination()

            if self.destination:
                next_facing, next_target, touching_infantry = self.get_next_tile()

                if self.agent.location == self.destination:
                    self.destination = None

                elif not next_facing:
                    self.destination = None

                elif next_target:

                    if touching_infantry:
                        self.agent.waiting = True

                    else:
                        if len(self.history) > 25:
                            self.history = []

                        if next_facing != self.agent.direction:
                            self.agent.movement.target_direction = next_facing
                            self.agent.movement.set_vectors()

                        else:
                            self.history.append(next_target)
                            self.agent.movement.target = next_target
                            self.agent.movement.set_vectors()

                else:
                    self.destination = None


class AgentTargeter(object):
    """the agent targeter is controlled by set_target_id and can provide information on the current target,
    enemy distance, target_vector and so on"""

    def __init__(self, agent):
        self.agent = agent
        self.has_turret = False
        self.check_timer = 0
        self.set_target_id = None

        self.enemy_target_id = None
        self.enemy_target = None
        self.target_vector = None
        self.turret_angle = 0.0
        self.hull_angle = 0.0
        self.turret_on_target = 180.0
        self.hull_on_target = 180.0
        self.closest_soldier = None
        self.target_distance = 0.0

    def get_basic_distance(self, target):
        target_vector = target.center.copy() - self.agent.center.copy()

        return target_vector.length

    def get_closest_enemy(self):

        # TODO implement a target ranking system

        key_list = [key for key in self.agent.level.agents]

        valid_agents = [agent_key for agent_key in key_list if
                        not self.invalid_target(self.agent.level.agents[agent_key])]
        reasonable_targets = [valid_agent_key for valid_agent_key in valid_agents if
                              not self.impenetrable(self.agent.level.agents[valid_agent_key])]

        closest = 2000
        best_target = None

        for reasonable_agent_key in reasonable_targets:
            enemy_agent = self.agent.level.agents[reasonable_agent_key]

            valid_target = self.check_target(enemy_agent)

            if valid_target:
                target_distance = self.get_basic_distance(enemy_agent)

                if target_distance < closest:
                    closest = target_distance
                    best_target = reasonable_agent_key

        if best_target:
            self.enemy_target_id = best_target
            self.set_closest_target(best_target)
        else:
            self.reset_values()

    def invalid_target(self, target_agent):

        if not target_agent:
            return True

        if self.agent.team == target_agent.team:
            return True

        if target_agent.dead:
            return True

        if not target_agent.seen:
            return True

        if target_agent.knocked_out:
            return True

        if target_agent.fully_loaded():
            return True

        if self.agent.fully_loaded():
            return True

    def impenetrable(self, target_agent):

        if self.agent.agent_type == "INFANTRY":
            return False

        armor_facing = target_agent.get_attack_facing(self.agent.center.copy())
        if armor_facing:

            if self.agent.stats.artillery and target_agent.stats.open_top:
                return False

            has_turret, facing, armor = armor_facing

            lowest_armor = armor[facing]

            penetration = self.agent.best_penetration

            if has_turret:
                if armor["TURRET"] < lowest_armor:
                    lowest_armor = armor["TURRET"]

            target_distance = (self.agent.center.copy() - target_agent.center.copy()).length
            penetration -= (target_distance * 0.25)

            if penetration < lowest_armor:
                return True

    def check_target(self, target_agent):

        invalid_target = self.invalid_target(target_agent)
        if invalid_target:
            return False

        impenetrable = self.impenetrable(target_agent)
        if impenetrable:
            return False

        return True

    def reset_values(self):
        self.enemy_target_id = None
        self.enemy_target = None
        self.target_vector = None
        self.hull_angle = 0.0
        self.turret_on_target = 180.0
        self.hull_on_target = 180.0
        self.closest_soldier = None
        self.target_distance = 0.0

    def set_closest_target(self, target_id):
        enemy_agent = self.agent.level.agents[target_id]
        self.enemy_target = enemy_agent
        self.closest_soldier, self.target_vector = enemy_agent.get_target(self.agent)
        self.target_distance = self.target_vector.length

    def update(self):

        if self.agent.dead:
            self.set_target_id = None
            self.reset_values()
        else:
            if self.agent.team != 0:
                if self.check_timer <= 0:
                    self.check_timer = 12
                    self.get_closest_enemy()

                else:
                    self.check_timer -= 1

                if self.enemy_target_id:
                    self.set_target_id = self.enemy_target_id
                else:
                    self.set_target_id = None
                    self.reset_values()

            else:
                if self.set_target_id:

                    set_target = self.agent.level.agents[self.set_target_id]

                    set_target_check = self.check_target(set_target)
                    if set_target_check:
                        self.set_closest_target(self.set_target_id)
                    else:
                        self.set_target_id = None
                        self.reset_values()

                else:
                    # if not self.check_target(self.enemy_target):
                    #     self.reset_values()

                    if self.check_timer <= 0:
                        self.check_timer = 12
                        self.get_closest_enemy()

                    else:
                        self.check_timer -= 1

        local_y = self.agent.movement_hook.getAxisVect([0.0, 1.0, 0.0]).to_2d()
        target_angle = 0.0

        if self.enemy_target:
            target_angle = local_y.angle_signed(self.target_vector.to_2d(), 0.0) * -1.0

        self.hull_angle = target_angle
        turret_speed = self.agent.turret_speed
        turret_difference = abs(self.turret_angle - target_angle)

        self.hull_on_target = math.degrees(abs(target_angle))
        self.turret_on_target = math.degrees(turret_difference)

        if turret_difference > 0.02:
            scale = turret_difference / 3.142
            turret_speed /= scale

            self.turret_angle = bgeutils.interpolate_float(self.turret_angle, target_angle, turret_speed)
