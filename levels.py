import bge
import user_interface
import bgeutils
import agents
import mathutils
import particles
import camera_control
import game_audio
import random


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
                command = {"label": "ROTATION_TARGET", "position": destination, "reverse": reverse,
                           "additive": additive}
            else:
                command = {"label": "MOVEMENT_TARGET", "position": destination, "reverse": reverse,
                           "additive": additive}

            self.owner.commands.append(command)

        self.icon.released = True


class MouseControl(object):

    def __init__(self, level):
        self.level = level
        self.start = None
        self.end = None
        self.additive = False
        self.tile_over = [35, 35]
        self.mouse_over = None
        self.over_units = []
        self.bypass = False

        self.movement_point = None
        self.movement_markers = []
        self.center_point = None
        self.rotation_countdown = 8
        self.context = None

        self.pulse = 0
        self.pulsing = False

    def get_tile_over(self):

        x, y = self.level.manager.game_input.virtual_mouse.copy()
        camera = self.level.manager.main_camera
        screen_vect = camera.getScreenVect(x, y)
        target_position = camera.worldPosition - screen_vect
        mouse_hit = camera.rayCast(target_position, camera, 200.0, "ground", 0, 1, 0)

        self.mouse_over = None

        if mouse_hit[0]:
            tile_over = [round(mouse_hit[1][0]), round(mouse_hit[1][1]) - 1]

            self.tile_over = tile_over
            tile_key = bgeutils.get_key(tile_over)
            mouse_over = self.level.map.get(tile_key)

            if mouse_over:
                self.mouse_over = mouse_over

            self.over_units = []

            for x in range(-1, 2):
                for y in range(-1, 2):

                    tx, ty = tile_over
                    neighbor = [x + tx, y + ty]
                    neighbor_key = bgeutils.get_key(neighbor)
                    neighbor_tile = self.level.map.get(neighbor_key)

                    if neighbor_tile:
                        occupant = neighbor_tile["occupied"]
                        if occupant:
                            self.over_units.append(occupant)

    def reset_movement(self):
        self.movement_point = None
        for movement_marker in self.movement_markers:
            movement_marker.terminate()

        self.movement_markers = []
        self.center_point = None
        self.rotation_countdown = 8

    def set_movement_points(self):
        self.movement_point = mathutils.Vector(self.tile_over)

        selected_agents = [self.level.agents[agent_id] for agent_id in self.level.agents if self.level.agents[agent_id].selected]

        center_point = mathutils.Vector().to_2d()

        if len(selected_agents) > 0:
            for selected_agent in selected_agents:
                center_point += selected_agent.box.worldPosition.copy().to_2d()

            center_point /= len(selected_agents)

        self.center_point = center_point

        for selected_agent in selected_agents:
            offset = self.center_point.copy() - selected_agent.box.worldPosition.copy().to_2d()
            target_point = self.movement_point.copy() - offset

            self.movement_markers.append(MovementMarker(self.level, selected_agent, target_point, offset))

    def update_movement_points(self):
        vector_start = self.movement_point.copy()

        if self.mouse_over:
            vector_end = mathutils.Vector(self.mouse_over["position"])
        else:
            vector_end = mathutils.Vector([0.0, 1.0])

        movement_vector = vector_end - vector_start

        local_vector = self.movement_point.copy() - self.center_point.copy()

        angle = movement_vector.angle_signed(local_vector, 0.0)

        for marker in self.movement_markers:
            marker.update(self.movement_point.copy(), angle)

    def set_selection_box(self):

        additive = "shift" in self.level.manager.game_input.keys
        if self.mouse_over:
            target_agent = self.mouse_over["occupied"]
        else:
            target_agent = None

        x_limit = sorted([self.start[0], self.end[0]])
        y_limit = sorted([self.start[1], self.end[1]])

        message = {"label": "SELECT", "x_limit": x_limit, "y_limit": y_limit, "additive": additive,
                   "mouse_over": target_agent}

        active_agents = [self.level.agents[agent_id] for agent_id in self.level.agents if self.level.agents[agent_id].team == 0]

        for agent in active_agents:
            agent.commands.append(message)

        self.start = None
        self.end = None

    def set_targets(self):
        enemy = None

        if self.over_units:
            for unit_id in self.over_units:
                target = self.level.agents[unit_id]
                if target.team != 0:
                    enemy = target

        if enemy:
            self.context = "TARGET"
            click = "right_button" in self.level.manager.game_input.buttons

            if click:
                selected_agents = [self.level.agents[agent_id] for agent_id in self.level.agents if
                                   self.level.agents[agent_id].selected]
                if selected_agents:
                    target_id = enemy.agent_id

                    message = {"label": "TARGET_ENEMY", "target_id": target_id}

                    for agent in selected_agents:
                        agent.commands.append(message)

    def update(self):

        if self.pulse < 0:
            self.pulsing = True
            self.pulse = 5
        else:
            self.pulsing = False
            self.pulse -= 1

        if self.pulsing:
            self.get_tile_over()

        self.context = "NONE"

        if not self.bypass:

            if not self.start and not self.movement_markers:
                self.set_targets()

            if self.context == "NONE":
                if not self.start:
                    movement = "right_drag" in self.level.manager.game_input.buttons

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
                    select = "left_drag" in self.level.manager.game_input.buttons

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

    def __init__(self, manager):
        self.manager = manager
        self.own = manager.own
        self.scene = self.own.scene
        self.camera_controller = camera_control.CameraControl(self)
        self.listener = self.camera_controller.camera_hook
        self.game_audio = game_audio.Audio(self)
        self.user_interface = user_interface.UserInterface(self)
        self.commands = []
        self.mouse_control = MouseControl(self)
        self.paused = False
        self.map_size = 100
        self.agent_id_index = 0
        self.loaded = False

        self.map = {}
        self.agents = {}
        self.particles = []
        self.messages = []
        self.bullets = []

        self.factions = {0: "HRE",
                        1: "VIN"}

        hre_infantry_path = bge.logic.expandPath("//infantry_sprites/hre_summer_sprites.blend")
        vin_infantry_path = bge.logic.expandPath("//infantry_sprites/vin_summer_sprites.blend")

        self.assets = []

        self.assets.append(bge.logic.LibLoad(hre_infantry_path, "Scene"))
        self.assets.append(bge.logic.LibLoad(vin_infantry_path, "Scene"))

        self.load_dict = None
        load_name = bge.logic.globalDict["profiles"][bge.logic.globalDict["active_profile"]]["saved_game"]
        if load_name:
            self.load_dict = bgeutils.load_level()
            self.load_level(self.load_dict)
        else:
            self.get_map()

    def check_assets_loaded(self):
        for asset in self.assets:
            if not asset:
                return False

        return True

    def get_tile(self, tile_key):
        if 0 < tile_key[0] < self.map_size and 0 < tile_key[1] < self.map_size:
            map_key = bgeutils.get_key(tile_key)

            return self.map[map_key]

    def set_tile(self, tile_key, setting, value):
        if 0 > tile_key[0] > self.map_size and 0 > tile_key[1] > self.map_size:
            map_key = bgeutils.get_key(tile_key)
            self.map[map_key][setting] = value

    def get_map(self):

        map = {}
        for x in range(self.map_size):
            for y in range(self.map_size):
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

        for agent_id in self.agents:
            agent = self.agents[agent_id]
            agent.terminate()

    def add_agents(self):

        for friend in range(4):
            agents.Vehicle(self, None, [35 + (10 * friend), 55], 0)

        infantry = ["SUPPORT_36", "SCOUT", "HEAVY_ANTI-TANK_TEAM", "RIFLEMEN_39", "ASSAULT_SQUAD_43"]

        for friend in range(5):
            agents.Infantry(self, random.choice(infantry), [35 + (10 * friend), 25], 0)

        # for enemy in range(4):
        #     agents.Vehicle(self, None, [35 + (10 * enemy), 35], 1)

        for enemy in range(5):
            agents.Infantry(self, random.choice(infantry), [35 + (10 * enemy), 45], 1)

    def load_level(self, load_dict):
        self.map = load_dict["map"]
        loading_agents = load_dict["agents"]

        for agent_id in loading_agents:
            loading_agent = loading_agents[agent_id]
            location = loading_agent["location"]
            team = loading_agent["team"]
            agent_type = loading_agent["agent_type"]

            agent_class = agents.Vehicle

            if agent_type == "VEHICLE":
                agent_class = agents.Vehicle

            elif agent_type == "INFANTRY":
                agent_class = agents.Infantry

            agent_class(self, None, location, team, agent_id=agent_id, load_dict=loading_agent)

    def save_level(self):
        saving_agents = {}
        for agent_id in self.agents:
            agent = self.agents[agent_id]
            saving_agents[agent_id] = agent.save()

        saved_map = {}
        for tile_key in self.map:
            tile = self.map[tile_key]
            tile["occupied"] = None
            saved_map[tile_key] = tile

        level_details = {"map": saved_map,
                         "agents": saving_agents}

        bgeutils.save_level(level_details)
        bge.logic.globalDict["next_level"] = "StartMenu"

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

        next_generation = {}

        for agent_id in self.agents:
            agent = self.agents[agent_id]
            if not agent.ended:
                agent.update()
                next_generation[agent_id] = agent
            else:
                agent.terminate()

        self.agents = next_generation

    def user_interface_update(self):
        # TODO write a full interface with button control
        if "pause" in self.manager.game_input.keys:
            self.paused = not self.paused

        command = None

        if "a" in self.manager.game_input.keys:
            command = {"label": "STANCE_CHANGE", "stance": "AGGRESSIVE"}
        if "s" in self.manager.game_input.keys:
            command = {"label": "STANCE_CHANGE", "stance": "SENTRY"}
        if "d" in self.manager.game_input.keys:
            command = {"label": "STANCE_CHANGE", "stance": "DEFEND"}
        if "f" in self.manager.game_input.keys:
            command = {"label": "STANCE_CHANGE", "stance": "FLANK"}

        if command:
            for agent_key in self.agents:
                agent = self.agents[agent_key]
                if agent.team == 0 and agent.selected:
                    agent.commands.append(command)

        self.manager.debugger.printer(self.paused, "paused")
        self.user_interface.update()

        if "escape" in self.manager.game_input.keys:
            self.save_level()

    def shoot(self, command):

        miss = True
        weapon = command["weapon"]
        owner = command["owner"]
        target = self.agents.get(command["target_id"])
        effect = command["effect"]
        rapid_fire = weapon.special == "RAPID_FIRE"
        accuracy = weapon.accuracy
        power = weapon.power
        weapon_range = weapon.range
        position = owner.box.worldPosition.copy()
        closest = 12000.0
        soldiers = []

        if command["label"] == "SMALL_ARMS_SHOOT":
            best_target = None
            hit_location = None

            if target:
                if target.agent_type == "INFANTRY":
                    prone_target = target.prone
                    if prone_target:
                        accuracy *= 0.5

                    soldiers = [s for s in target.soldiers if s.toughness > 0]

                    if soldiers:
                        for soldier in soldiers:
                            target_position = soldier.box.worldPosition.copy()
                            target_vector = target_position - position
                            distance = target_vector.length

                            if distance < closest:
                                closest = distance
                                best_target = soldier

                        target_distance = closest

                        if rapid_fire:
                            effective_range = max([(accuracy + weapon_range) * random.uniform(0.0, 1.0) for _ in range(3)])
                        else:
                            effective_range = (accuracy + weapon_range) * random.uniform(0.0, 1.0)

                        if effective_range > target_distance:
                            miss = False

                    if miss:
                        if soldiers:
                            base_location = best_target.box.worldPosition.copy()
                            random_vector = mathutils.Vector([random.uniform(-3.0, 3.0), random.uniform(-3.0, 3.0), 0.0])
                            hit_location = base_location + random_vector

                    else:
                        # TODO target toughness increased when in building

                        hit_location = best_target.box.worldPosition.copy()
                        effective_power = power * random.uniform(0.0, 1.0)

                        if effective_power > best_target.toughness:
                            damage = max(1, int(effective_power * 0.5))
                            best_target.toughness -= damage

            if hit_location and effect:

                if effect == "RED_STREAK":
                    particles.RedBulletStreak(self, list(position), list(hit_location))

                if effect == "YELLOW_STREAK":
                    particles.YellowBulletStreak(self, list(position), list(hit_location))

                    if rapid_fire:
                        particles.YellowBulletStreak(self, list(position), list(hit_location), delay=6)
                        particles.YellowBulletStreak(self, list(position), list(hit_location), delay=12)

    def process_commands(self):

        for command in self.commands:
            if "SHOOT" in command["label"]:
                self.shoot(command)

        self.commands = []

    def load(self):
        if self.check_assets_loaded():
            self.loaded = True
            if not self.load_dict:
                self.add_agents()

    def sound_update(self):

        for message in bge.logic.globalDict["sounds"]:
            if message["header"] == "SOUND_EFFECT":
                sound, owner, attenuation, volume_scale = message["content"]
                if not owner:
                    owner = self.listener

                self.game_audio.sound_effect(sound, owner, attenuation=attenuation, volume_scale=volume_scale)

        bge.logic.globalDict["sounds"] = []

    def update(self):
        self.camera_controller.update()
        self.game_audio.update()
        self.mouse_update()
        self.agent_update()
        self.particle_update()
        self.user_interface_update()
        self.sound_update()
        self.process_commands()
