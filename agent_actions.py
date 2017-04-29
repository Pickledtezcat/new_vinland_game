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
        self.start_vector = mathutils.Vector(self.agent.location).to_3d()
        self.start_vector.z = start_tile["height"]
        self.start_normal = mathutils.Vector(start_tile["normal"])

        self.target_vector = self.start_vector
        self.target_normal = self.start_normal

        self.current_orientation = mathutils.Vector(self.agent.direction).to_3d().to_track_quat("Y", "Z").to_matrix().to_3x3()
        self.target_orientation = mathutils.Vector(self.agent.direction).to_3d().to_track_quat("Y", "Z").to_matrix().to_3x3()

        if self.target_direction:
            self.target_orientation = mathutils.Vector(self.target_direction).to_3d().to_track_quat("Y", "Z").to_matrix().to_4x4()

        elif self.target:
            target_tile = self.agent.level.map[bgeutils.get_key(self.target)]
            self.target_vector = mathutils.Vector(self.agent.location).to_3d()
            self.target_vector.z = target_tile["height"]
            self.target_normal = mathutils.Vector(target_tile["normal"])

    def update(self):
        if self.target_direction:
            self.done = False
            self.timer = min(1.0, self.timer + self.agent.turning_speed)
            if self.timer == 1.0:
                self.target_direction = None
                self.timer = 0.0

        elif self.target:
            self.done = False
            self.timer = min(1.0, self.timer + self.agent.speed)
            if self.timer == 1.0:
                self.target = None
                self.timer = 0.0

        else:
            self.done = True

        if not self.done:
            self.set_position()

    def set_position(self, instant=False):

        if instant:
            timer = 1.0
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
        self.set_position(instant=True)


class Navigation(object):

    def __init__(self, agent):
        self.agent = agent
        self.destination = None
        self.history = []

    def get_next_destination(self):
        if self.agent.destinations:
            self.destination = self.agent.destinations.pop()

    def get_next_tile(self):
        pass

