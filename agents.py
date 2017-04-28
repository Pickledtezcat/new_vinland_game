import bge
import mathutils
import bgeutils
import particles

class AgentMovement(object):

    def __init__(self, agent):
        self.agent = agent
        self.target = None
        self.start_vector = None
        self.target_vector = None
        self.start_normal = None
        self.target_normal = None

        self.direction = None
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

        if self.direction:
            self.target_orientation = mathutils.Vector(self.direction).to_3d().to_track_quat("Y", "Z").to_matrix().to_4x4()

        elif self.target:
            target_tile = self.agent.level.map[bgeutils.get_key(self.target)]
            self.target_vector = mathutils.Vector(self.agent.location).to_3d()
            self.target_vector.z = target_tile["height"]
            self.target_normal = mathutils.Vector(target_tile["normal"])

    def update(self):
        if self.direction:
            self.done = False
            self.timer = min(1.0, self.timer + self.agent.turning_speed)
            if self.timer == 1.0:
                self.direction = None
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


class Agent(object):

    size = 0
    max_speed = 0.0
    speed = 0.0
    handling = 0.0
    throttle = 0.0
    throttle_target = 0.0
    turning_speed = 0.01
    damping = 0.1

    starting_state = "VehicleStart"

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

        self.target = None
        self.reverse = False
        self.selected = False

        self.movement = AgentMovement(self)
        self.navigation = Navigation(self)

        self.load_stats()

        self.state = None
        self.state_name = None

        self.set_position()
        self.level.agents.append(self)

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

                    cam = self.level.manager.main_camera

                    select = False

                    if cam.pointInsideFrustum(self.box.worldPosition):
                        screen_location = cam.getScreenPosition(self.box)
                        padding = 0.03

                        if x_limit[0] - padding < screen_location[0] < x_limit[1] + padding:
                            if y_limit[0] - padding < screen_location[1] < y_limit[1] + padding:
                                select = True

                    if select:
                        self.selected = True

                    elif not command["ADDITIVE"]:
                        if not select:
                            self.selected = False

        self.commands = []

    def update(self):

        self.debug_text = self.selected
        self.process_commands()
        pass

