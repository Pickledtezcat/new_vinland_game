import bge
import user_interface
import bgeutils
import agents
import mathutils
import particles


class MovementMarker(object):
    def __init__(self, level, owner, position, offset):
        self.level = level
        self.owner = owner
        self.position = position
        self.offset = offset

        self.icon = particles.MovementPointIcon(self.level, position)

    def update(self, movement_point, angle):

        rotation = mathutils.Euler((0.0, 0.0, angle))
        new_position = self.offset.to_3d()
        new_position.rotate(rotation)
        target_point = movement_point - new_position.to_2d()

        self.position = target_point
        self.icon.set_position(self.position)

    def terminate(self):
        if not self.icon.released:
            self.icon.ended = True

    def release(self):
        if not self.icon.invalid_location:
            if "alt" in self.level.manager.game_input.keys:
                reverse = True
            else:
                reverse = False

            if "shift" in self.level.manager.game_input.keys:
                additive = True
            else:
                additive = False

            destination = [int(axis) for axis in self.position]

            if "control" in self.level.manager.game_input.keys:
                command = {"LABEL": "ROTATION_TARGET", "POSITION": destination, "REVERSE": reverse,
                           "ADDITIVE": additive}
            else:
                command = {"LABEL": "MOVEMENT_TARGET", "POSITION": destination, "REVERSE": reverse,
                           "ADDITIVE": additive}

            self.owner.commands.append(command)

        self.icon.released = True


class MouseControl(object):

    def __init__(self, level):
        self.level = level
        self.start = None
        self.end = None
        self.additive = False
        self.tile_over = [35, 35]
        self.tile_key = bgeutils.get_key(self.tile_over)
        self.bypass = False

        self.movement_point = None
        self.movement_markers = []
        self.center_point = None
        self.rotation_countdown = 8

        self.pulse = 0
        self.pulsing = False

    def get_tile_over(self):

        x, y = self.level.manager.game_input.virtual_mouse.copy()
        camera = self.level.manager.main_camera
        screen_vect = camera.getScreenVect(x, y)
        target_position = camera.worldPosition - screen_vect
        mouse_hit = camera.rayCast(target_position, camera, 200.0, "ground", 0, 1, 0)

        if mouse_hit[0]:
            tile_over = [round(mouse_hit[1][0]), round(mouse_hit[1][1]) - 1]
            tile_key = bgeutils.get_key(tile_over)
            if self.level.map.get(tile_key):
                self.tile_over = tile_over
                self.tile_key = tile_key

    def reset_movement(self):
        self.movement_point = None
        for movement_marker in self.movement_markers:
            movement_marker.terminate()

        self.movement_markers = []
        self.center_point = None
        self.rotation_countdown = 8

    def set_movement_points(self):
        self.movement_point = mathutils.Vector(self.tile_over)
        selected_agents = [agent for agent in self.level.agents if agent.selected]

        center_point = mathutils.Vector().to_2d()

        if len(selected_agents) > 0:
            for selected_agent in selected_agents:
                center_point += selected_agent.box.worldPosition.copy().to_2d()

            center_point /= len(selected_agents)

        self.center_point = center_point

        self.level.manager.debugger.printer(self.center_point, "center", decay=300)

        for selected_agent in selected_agents:
            offset = self.center_point.copy() - selected_agent.box.worldPosition.copy().to_2d()
            target_point = self.movement_point.copy() - offset

            self.movement_markers.append(MovementMarker(self.level, selected_agent, target_point, offset))

    def update_movement_points(self):
        vector_start = self.movement_point.copy()
        ground_hit = self.level.map[bgeutils.get_key(self.tile_over)]

        vector_end = mathutils.Vector(ground_hit["position"])

        movement_vector = vector_end - vector_start
        local_vector = self.movement_point.copy() - self.center_point.copy()

        angle = movement_vector.angle_signed(local_vector, 0.0)

        for marker in self.movement_markers:
            marker.update(self.movement_point.copy(), angle)

    def set_selection_box(self):

        additive = "shift" in self.level.manager.game_input.keys
        mouse_over = self.level.map[bgeutils.get_key(self.tile_over)]
        if mouse_over:
            target_agent = mouse_over["occupied"]
        else:
            target_agent = None

        x_limit = sorted([self.start[0], self.end[0]])
        y_limit = sorted([self.start[1], self.end[1]])

        message = {"LABEL": "SELECT", "X_LIMIT": x_limit, "Y_LIMIT": y_limit, "ADDITIVE": additive,
                   "MOUSE_OVER": target_agent}

        for agent in self.level.agents:
            agent.commands.append(message)

        self.start = None
        self.end = None

    def update(self):

        if self.pulse < 0:
            self.pulsing = True
            self.pulse = 3
        else:
            self.pulsing = False
            self.pulse -= 1

        if self.pulsing:
            self.get_tile_over()

        if not self.bypass:
            select = "left_drag" in self.level.manager.game_input.buttons
            movement = "right_drag" in self.level.manager.game_input.buttons

            if not self.start:
                if movement and self.tile_over:
                    if not self.movement_markers:
                        self.set_movement_points()

                    if self.rotation_countdown > 0:
                        self.rotation_countdown -= 1
                    else:
                        if self.pulsing:
                            self.update_movement_points()
                else:
                    if self.movement_markers:
                        for marker in self.movement_markers:
                            marker.release()
                        self.reset_movement()

            if not self.movement_markers:
                if select:
                    focus = self.level.manager.game_input.virtual_mouse.copy()
                    if not self.start:
                        self.start = focus

                    self.end = focus
                    self.level.user_interface.set_bounding_box(False, self.start, self.end)

                else:
                    if self.start and self.end:
                        self.set_selection_box()

                    self.level.user_interface.set_bounding_box(True, None, None)


class Level(object):

    def __init__(self, manager, load_dict=None):
        self.manager = manager
        self.own = manager.own
        self.user_interface = user_interface.UserInterface(manager)
        self.commands = []
        self.mouse_control = MouseControl(self)
        self.paused = False

        self.map = {}
        self.agents = []
        self.particles = []

        if load_dict:
            self.load_level(load_dict)
        else:
            self.get_map()
            self.add_agents()

    def get_map(self):

        map = {}
        for x in range(100):
            for y in range(100):
                x_pos = x + 0.5
                y_pos = y + 0.5

                target_position = [x_pos, y_pos, -10.0]
                origin = [x_pos, y_pos, 10.0]

                ray = self.own.rayCast(target_position, origin, 0.0, "ground", 1, 1, 0)
                if ray[0]:
                    tile = {"position": [x_pos, y_pos], "occupied": None, "height": ray[1][2], "normal": list(ray[2])}

                    map[bgeutils.get_key((x, y))] = tile

        self.map = map

    def terminate(self):
        self.user_interface.terminate()

        for particle in self.particles:
            particle.terminate()

        for agent in self.agents:
            agent.terminate()

    def add_agents(self):
        agents.Agent(self, None, [45, 45], 0)
        agents.Agent(self, None, [20, 45], 0)
        agents.Agent(self, None, [30, 45], 0)

    def load_level(self, load_dict):
        self.map = load_dict["map"]
        loading_agents = load_dict["agents"]

        for agent_key in loading_agents:
            loading_agent = loading_agents[agent_key]
            location = loading_agent["location"]
            team = loading_agent["team"]

            loaded_agent = agents.Agent(self, None, location, team, load_dict=loading_agent)

    def save_agents(self):
        agent_id = 1

        saving_agents = {}
        for agent in self.agents:
            saving_agents[str(agent_id)] = agent.save()
            agent_id += 1

        return saving_agents

    def mouse_update(self):
        self.mouse_control.update()

    def particle_update(self):
        next_generation = []

        for particle in self.particles:
            if not particle.ended:
                particle.update()
                next_generation.append(particle)
            else:
                particle.terminate()

        self.particles = next_generation

    def agent_update(self):

        next_generation = []

        for agent in self.agents:
            if not agent.ended:
                agent.update()
                next_generation.append(agent)
            else:
                agent.terminate()

        self.agents = next_generation

    def user_interface_update(self):
        # temporary
        if "pause" in self.manager.game_input.keys:
            self.paused = not self.paused

        self.manager.debugger.printer(self.paused, "paused")
        self.user_interface.update()

    def update(self):
        self.mouse_update()
        self.user_interface_update()
        self.agent_update()
        self.particle_update()
