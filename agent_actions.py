import bge
import bgeutils
import mathutils


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

        if self.target_direction:
            self.target_orientation = mathutils.Vector(self.target_direction).to_3d().to_track_quat("Y", "Z").to_matrix().to_3x3()

        elif self.target:
            self.agent.set_occupied(self.target)
            target_tile = self.agent.level.map[bgeutils.get_key(self.target)]
            self.target_vector = mathutils.Vector(target_tile["position"]).to_3d()
            self.target_vector.z = target_tile["height"]
            self.target_normal = mathutils.Vector(target_tile["normal"])

        self.done = False

    def update(self):
        if self.target_direction:
            self.timer = min(1.0, self.timer + self.agent.turning_speed)
            if self.timer >= 1.0:
                self.agent.direction = self.target_direction
                self.target_direction = None

        elif self.target:
            self.timer = min(1.0, self.timer + self.agent.speed)
            if self.timer >= 1.0:
                self.agent.location = self.target
                self.target = None
        else:
            self.timer = 0.0
            self.done = True

        if not self.done:
            self.set_position()
        else:
            self.agent.clear_occupied()
            self.agent.set_occupied(self.agent.location)

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

        normal = self.start_normal.lerp(self.target_normal, timer)

        local_y = self.agent.tilt_hook.getAxisVect([0.0, 1.0, 0.0])
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
        self.timer = timer

        self.set_vectors()
        self.set_position()


class Navigation(object):

    def __init__(self, agent):
        self.agent = agent
        self.destination = None
        self.history = []
        self.stop = False

    def get_next_destination(self):
        self.history = [self.agent.location]
        if self.agent.destinations:
            self.destination = self.agent.destinations.pop()

    def get_next_tile(self):
        search_array = [(1, 0), (1, 1), (0, 1), (1, -1), (-1, 0), (-1, 1), (0, -1), (-1, -1)]
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



