import bge
import bgeutils
import mathutils
import random


class AgentMovement(object):

    def __init__(self, agent):
        self.agent = agent
        self.target = None
        self.start_vector = None
        self.target_vector = None
        self.start_normal = None
        self.target_normal = None

        self.target_direction = None
        self.current_orientation = None
        self.target_orientation = None
        self.scale = 1.0

        self.timer = 0.0
        self.done = True

        self.set_vectors()

    def set_vectors(self):

        start_tile = self.agent.level.map[bgeutils.get_key(self.agent.location)]
        self.start_vector = mathutils.Vector(start_tile["position"]).to_3d()
        self.start_vector.z = start_tile["height"]
        self.start_normal = mathutils.Vector(start_tile["normal"])

        self.target_vector = self.start_vector
        self.target_normal = self.start_normal

        self.current_orientation = mathutils.Vector(self.agent.direction).to_3d().to_track_quat("Y", "Z").to_matrix().to_3x3()
        self.target_orientation = mathutils.Vector(self.agent.direction).to_3d().to_track_quat("Y", "Z").to_matrix().to_3x3()

        start_direction = mathutils.Vector(self.agent.direction)
        end_direction = start_direction

        if self.target_direction:
            self.target_orientation = mathutils.Vector(self.target_direction).to_3d().to_track_quat("Y", "Z").to_matrix().to_3x3()
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
            self.timer = min(1.0, self.timer + self.agent.speed)
            if self.timer >= 1.0:
                self.agent.location = self.target
                self.target = None

        else:
            if not self.done:
                self.done = True
                self.agent.clear_occupied()
                self.agent.set_occupied(self.agent.location)

        if not self.done:
            self.set_position()

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

        self.agent.box.worldPosition = self.start_vector.lerp(self.target_vector, timer)
        rotation = self.current_orientation.lerp(self.target_orientation, bgeutils.smoothstep(timer))
        self.agent.movement_hook.worldOrientation = rotation

        if self.agent.agent_type != "INFANTRY":
            normal = self.start_normal.lerp(self.target_normal, timer)

            local_y = self.agent.movement_hook.getAxisVect([0.0, 1.0, 0.0])
            local_z = self.agent.tilt_hook.getAxisVect([0.0, 0.0, 1.0])

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

    def update(self):

        if self.target:
            self.timer = min(1.0, self.timer + self.infantryman.speed)
            if self.timer >= 1.0:
                self.infantryman.location = self.target
                self.target = None

        else:
            if not self.done:
                self.done = True
                self.infantryman.clear_occupied()
                self.infantryman.set_occupied(self.infantryman.location)

        if not self.done:
            self.set_position()

    def set_position(self, set_timer=0.0):

        if set_timer:
            timer = set_timer
        else:
            timer = self.timer

        self.infantryman.box.worldPosition = self.start_vector.lerp(self.target_vector, timer)


class InfantryAnimation(object):

    def __init__(self, infantryman):
        self.infantryman = infantryman
        self.last_frame = 0
        self.frame = 0.0
        self.north = random.choice(["NE", "NW"])
        self.faction = self.infantryman.agent.faction
        self.set_frame("default", 0)
        self.infantryman.sprite.visible = True

    def get_vector(self, target_vector):

        search_array = [[1, 0], [1, 1], [0, 1], [1, -1], [-1, 0], [-1, 1], [0, -1], [-1, -1]]

        best_facing = None
        best_angle = 4.0

        for facing in search_array:
            facing_vector = mathutils.Vector(facing)
            angle = facing_vector.angle(target_vector.to_2d())
            if angle < best_angle:
                best_facing = facing
                best_angle = angle

        return best_facing

    def get_target_direction(self, action):

        shooting_actions = ["FACE_TARGET", "SHOOTING"]

        if action in shooting_actions:
            target = self.infantryman.agent.level.agents.get(self.infantryman.agent.agent_targeter.enemy_target_id)
            if target:
                target_vector = target.box.worldPosition.copy() - self.infantryman.box.worldPosition.copy()
                return self.get_vector(target_vector)

        return self.infantryman.direction

    def update(self):

        behavior = self.infantryman.behavior
        prone = self.infantryman.behavior.prone
        timed_actions = ["DYING", "GO_PRONE", "GET_UP", "SHOOTING", "WAIT", "FINISHED", "FACE_TARGET"]
        dead_actions = ["DYING", "DEAD"]

        if behavior.action in timed_actions:
            self.frame = behavior.action_timer * 4.0

            if behavior.action == "SHOOTING" and self.infantryman.special == "RAPID_FIRE":

                action_time = behavior.action_timer * 12
                remainder = action_time % 3
                self.frame = remainder * 3.0

            # TODO find out how to rapid fire

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

        else:
            action = "default"

        if frame_number != self.last_frame:
            self.set_frame(action, frame_number)

    def set_frame(self, action, frame_number):
        self.last_frame = frame_number

        if action == "default":
            if self.infantryman.behavior.prone:
                action = "go_prone"
                frame_number = 3
            else:
                if random.uniform(0.0, 1.0) < 0.8:
                    frame_number = 0

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

    def get_action(self):

        if self.action == "DYING":
            self.infantryman.dead = True
            self.infantryman.clear_occupied()
            return "DEAD"

        shooting = self.infantryman.weapon.shoot_weapon()
        dying = self.infantryman.toughness <= 0

        if dying:
            self.action_timer = 0.0
            return "DYING"

        if self.infantryman.agent.prone:
            if not self.prone:
                self.action_timer = 0.0
                return "GO_PRONE"
        else:
            if self.prone:
                self.action_timer = 0.0
                return "GET_UP"

        if shooting:
            self.action_timer = 0.0
            return "SHOOTING"

        avoiding = self.avoiding
        self.avoiding = self.infantryman.check_too_close(self.infantryman.location)

        if avoiding and not self.avoiding:
            self.action_timer = 0.0
            return "WAIT"

        destination = self.infantryman.get_destination()
        if destination != self.destination:
            self.destination = destination

        if self.infantryman.location != self.destination:
            return "GET_TILE"
        else:
            if self.avoiding:
                return "GET_TILE"
            if self.infantryman.agent.agent_type == "ARTILLERY":
                self.action_timer = 0.0
                self.history = [self.infantryman.location]
                return "FACE_GUN"
            if self.infantryman.agent.agent_targeter.enemy_target_id:
                self.action_timer = 0.0
                self.history = [self.infantryman.location]
                return "FACE_TARGET"
            self.action_timer = 0.0
            self.history = [self.infantryman.location]
            return "FINISHED"

    def update(self):
        if self.action != "DEAD":
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
        free = 0

        for s in search_array:
            neighbor = [current_tile[0] + s[0], current_tile[1] + s[1]]
            neighbor_check = self.agent.check_occupied(neighbor)

            if not neighbor_check:
                if neighbor not in self.history:
                    free += 1

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
                    if agent.agent_type == "INFANTRY" and agent.team == self.agent.team:
                        touching_infantry = True

        return closest, next_facing, next_target, free, touching_infantry

    def update(self):

        if self.agent.movement.done:

            if self.stop:
                self.stop = False
                self.destination = None

            if not self.destination:
                self.get_next_destination()

            if self.destination:
                closest, next_facing, next_target, free, touching_infantry = self.get_next_tile()

                if self.agent.location == self.destination:
                    self.destination = None

                elif not next_facing:
                    self.destination = None

                elif next_target:
                    if free < 6 and closest < 3:
                        if len(self.history) > 25:
                            self.history = []
                            self.agent.waiting = True

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

    def __init__(self, agent):
        self.agent = agent
        self.enemy_target_id = None
        self.turret_angle = 0.0
        self.gun_elevation = 0.0

        self.turret_on_target = False
        self.hull_on_target = False

    def update(self):
        local_y = self.agent.movement_hook.getAxisVect([0.0, 1.0, 0.0]).to_2d()
        enemy_dead = False

        if self.enemy_target_id:
            enemy_agent = self.agent.level.agents[self.enemy_target_id]
            if enemy_agent.dead:
                enemy_dead = True
            target_vector = (enemy_agent.box.worldPosition.copy() - self.agent.box.worldPosition.copy()).to_2d()
        else:
            target_vector = local_y

        if enemy_dead:
            self.enemy_target_id = None
        else:
            target_angle = local_y.angle_signed(target_vector, 0.0) * -1.0
            turret_speed = self.agent.turret_speed

            turret_difference = abs(self.turret_angle - target_angle)

            self.turret_on_target = False
            self.hull_on_target = False

            if abs(target_angle) < 0.5:
                self.hull_on_target = True

            if turret_difference < 0.5:
                self.turret_on_target = True

            if turret_difference > 0.02:
                scale = turret_difference / 3.142
                turret_speed /= scale

                self.turret_angle = bgeutils.interpolate_float(self.turret_angle, target_angle, turret_speed)


class AgentAnimator(object):
    def __init__(self, agent):

        self.agent = agent
        self.turret = bgeutils.get_ob("agent_turret", self.agent.box.childrenRecursive)

    def update(self):

        if self.turret:
            turret_angle = self.agent.agent_targeter.turret_angle
            turret_matrix = mathutils.Matrix.Rotation(turret_angle, 4, 'Z').to_3x3()
            self.turret.localOrientation = turret_matrix


