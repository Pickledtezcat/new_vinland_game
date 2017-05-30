import bge
import user_interface
import bgeutils
import agents
import mathutils
import particles
import camera_control
import game_audio
import random
import buildings
import LOS


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
            mouse_over = self.level.get_tile(tile_over)

            if mouse_over:
                self.mouse_over = mouse_over

            self.over_units = []

            for x in range(-1, 2):
                for y in range(-1, 2):

                    tx, ty = tile_over
                    neighbor = [x + tx, y + ty]
                    neighbor_tile = self.level.get_tile(neighbor)

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

        selected_agents = [self.level.agents[agent_id] for agent_id in self.level.agents if
                           self.level.agents[agent_id].selected]

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

        active_agents = [self.level.agents[agent_id] for agent_id in self.level.agents if
                         self.level.agents[agent_id].team == 0]

        for agent in active_agents:
            agent.commands.append(message)

        self.start = None
        self.end = None

    def set_targets(self):
        enemy = None

        if self.over_units:
            for unit_id in self.over_units:
                target = self.level.agents[unit_id]
                if target.team != 0 and target.seen and not target.dead:
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

        elif self.mouse_over:
            if self.mouse_over["building"]:
                building = self.level.buildings.get(self.mouse_over["building"])
                if building:
                    if not building.occupier:
                        self.context = "BUILDING"
                        click = "right_button" in self.level.manager.game_input.buttons

                        if click:
                            selected_agents = [self.level.agents[agent_id] for agent_id in self.level.agents if
                                               self.level.agents[agent_id].selected]

                            if selected_agents:
                                target_id = self.mouse_over["building"]
                                message = {"label": "ENTER_BUILDING", "target_id": target_id}

                                for agent in selected_agents:
                                    agent.commands.append(message)

                    else:
                        # TODO setup if enemy occupier

                        self.context = "NO_ENTRY"

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
        print("GAME_MODE")

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
        self.map_size = 128
        self.agent_id_index = 0
        self.loaded = False
        self.visibility_timer = 0
        self.LOS = LOS.VisionPaint(self)

        self.agents_added = False
        self.buildings_added = False
        self.buildings_mapped = False

        self.map = {}
        self.agents = {}
        self.buildings = {}
        self.particles = []
        self.messages = []
        self.bullets = []
        # TODO add bullets, for artillery weapons

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

    def check_level_loaded(self):

        if not self.map:
            self.get_map()
            return False

        if not self.buildings_added:
            self.add_buildings()
            return False

        for asset in self.assets:
            if not asset:
                return False

        if not self.buildings_mapped:
            self.get_buildings()
            return False

        if not self.agents_added:
            self.add_agents()

        return True

    def get_tile(self, tile_key):
        if 0 < tile_key[0] < self.map_size and 0 < tile_key[1] < self.map_size:
            map_key = bgeutils.get_key(tile_key)

            return self.map[map_key]

    def set_tile(self, tile_key, setting, value):
        if 0 < tile_key[0] < self.map_size and 0 < tile_key[1] < self.map_size:
            map_key = bgeutils.get_key(tile_key)
            try:
                self.map[map_key][setting] = value
            except KeyError:
                print("problem setting tile value")

    def get_map(self):

        map = {}
        for x in range(self.map_size):
            for y in range(self.map_size):
                x_pos = x + 0.5
                y_pos = y + 0.5

                target_position = [x_pos, y_pos, -10.0]
                origin = [x_pos, y_pos, 10.0]

                ray = self.own.rayCast(target_position, origin, 0.0, "ground", 1, 1, 1)

                if ray[0]:
                    tile = {"position": [x_pos, y_pos], "occupied": None, "height": ray[1][2], "normal": list(ray[2]),
                            "building": None}

                    map[bgeutils.get_key((x, y))] = tile

        self.map = map

    def get_buildings(self):

        for x in range(self.map_size):
            for y in range(self.map_size):
                x_pos = x + 0.5
                y_pos = y + 0.5

                target_position = [x_pos, y_pos, -10.0]
                origin = [x_pos, y_pos, 10.0]

                ray = self.own.rayCast(target_position, origin, 0.0, "building", 0, 1, 0)
                if ray[0]:
                    building_id = ray[0]["building_id"]
                    self.set_tile((x, y), "building", building_id)

        for building_id in self.buildings:
            building = self.buildings[building_id]
            for door_loc in building.doors:
                self.set_tile(door_loc, "building", None)

        self.buildings_mapped = True

    def terminate(self):
        self.user_interface.terminate()

        for particle in self.particles:
            particle.terminate()

        for agent_id in self.agents:
            agent = self.agents[agent_id]
            agent.terminate()

        for building_id in self.buildings:
            building = self.buildings[building_id]
            building.terminate()

    def add_agents(self):

        # for friend in range(4):
        #     agents.Vehicle(self, None, [35 + (10 * friend), 55], 0)

        infantry = ["SUPPORT_36", "SCOUT", "HEAVY_ANTI-TANK_TEAM", "RIFLEMEN_39", "ASSAULT_SQUAD_43"]

        for friend in range(5):
            agents.Infantry(self, random.choice(infantry), [35 + (10 * friend), 45], 0)

        # agents.Infantry(self, "SUPPORT_36", [35, 25], 0)

        # for enemy in range(4):
        #     agents.Vehicle(self, None, [35 + (10 * enemy), 35], 1)

        for enemy in range(5):
            agents.Infantry(self, random.choice(infantry), [35 + (10 * enemy), 25], 1)

        self.agents_added = True

    def add_buildings(self):

        buildings.Building(self, "basic_house", [35, 35], [-1, 1])
        buildings.Building(self, "basic_house", [45, 35], [1, 0])
        buildings.Building(self, "basic_house", [55, 35], [0, 1])

        self.buildings_added = True

    def load_level(self, load_dict):
        self.map = load_dict["map"]
        loading_agents = load_dict["agents"]

        for agent_id in loading_agents:
            loading_agent = loading_agents[agent_id]
            location = loading_agent["location"]
            team = loading_agent["team"]
            agent_type = loading_agent["agent_type"]
            load_name = loading_agent["load_name"]

            agent_class = agents.Vehicle

            if agent_type == "VEHICLE":
                agent_class = agents.Vehicle

            elif agent_type == "INFANTRY":
                agent_class = agents.Infantry

            agent_class(self, load_name, location, team, agent_id=agent_id, load_dict=loading_agent)

        loading_buildings = load_dict["buildings"]

        for building_id in loading_buildings:
            loading_building = loading_buildings[building_id]
            load_name = loading_building["load_name"]
            location = loading_building["location"]
            direction = loading_building["direction"]
            building_type = loading_building["building_type"]

            # TODO different building types

            building_class = buildings.Building
            building_class(self, load_name, location, direction, building_id=building_id, load_dict=loading_building)

        self.agents_added = True
        self.buildings_added = True
        self.buildings_mapped = True

    def save_level(self):
        saving_agents = {}
        for agent_id in self.agents:
            agent = self.agents[agent_id]
            saving_agents[agent_id] = agent.save()

        saved_map = {}

        saving_buildings = {}
        for building_id in self.buildings:
            building = self.buildings[building_id]
            saving_buildings[building_id] = building.save()

        for tile_key in self.map:
            tile = self.map[tile_key]
            tile["occupied"] = None
            saved_map[tile_key] = tile

        level_details = {"map": saved_map,
                         "buildings": saving_buildings,
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

        target_position = None
        weapon = command["weapon"]
        owner = command["owner"]
        target = self.agents.get(command["target_id"])
        effect = command["effect"]
        origin = mathutils.Vector(command["origin"]).to_3d()
        effective_range = command["effective_range"]
        effective_power = command["effective_power"]

        if command["label"] == "SMALL_ARMS_SHOOT":
            best_target = None
            target_position = None

            if target:
                if target.agent_type == "INFANTRY":

                    best_target, target_distance = target.get_closest_soldier(origin)
                    if best_target:
                        if best_target.in_building:
                            if random.randint(0, 3) >= 3:
                                target_position = None

                            target_building = self.buildings.get(best_target.in_building)
                            if target_building:
                                target_position = target_building.get_closest_window(origin)
                        else:
                            target_position = best_target.box.worldPosition.copy()

                        if effective_range < target_distance:
                            target_position = None

                    if target_position:
                        if effective_power > best_target.toughness:
                            damage = max(1, int(effective_power * 0.5))
                            best_target.toughness -= damage

                    else:
                        if best_target:
                            base_location = best_target.box.worldPosition.copy()
                            random_vector = mathutils.Vector(
                                [random.uniform(-3.0, 3.0), random.uniform(-3.0, 3.0), 0.0])
                            target_position = base_location + random_vector

            if target_position and effect:
                if effect == "RED_STREAK":
                    particles.RedBulletStreak(self, list(origin), list(target_position))

                if effect == "YELLOW_STREAK":
                    particles.YellowBulletStreak(self, list(origin), list(target_position))

                if effect == "RAPID_YELLOW_STREAK":
                    particles.YellowBulletStreak(self, list(origin), list(target_position))
                    particles.YellowBulletStreak(self, list(origin), list(target_position), delay=6)
                    particles.YellowBulletStreak(self, list(origin), list(target_position), delay=12)

    def process_commands(self):

        for command in self.commands:
            if "SHOOT" in command["label"]:
                self.shoot(command)

        self.commands = []

    def load(self):
        if self.check_level_loaded():
            self.loaded = True

    def sound_update(self):

        for message in bge.logic.globalDict["sounds"]:
            if message["header"] == "SOUND_EFFECT":
                sound, owner, attenuation, volume_scale = message["content"]
                if not owner:
                    owner = self.listener

                self.game_audio.sound_effect(sound, owner, attenuation=attenuation, volume_scale=volume_scale)

        bge.logic.globalDict["sounds"] = []

    def inside_camera(self, agent):

        if agent.agent_type == "INFANTRY":
            soldiers = [soldier for soldier in agent.soldiers if not soldier.dead]

            for soldier in agent.soldiers:
                if self.camera_controller.main_camera.pointInsideFrustum(soldier.box.worldPosition.copy()):
                    return True

        else:
            if self.camera_controller.main_camera.sphereInsideFrustum(agent.box.worldPosition.copy(), 4):
                return True

    def visibility_update(self):

        """visible means the agent can be seen on screen, seen means they can be targeted by AI, suspect means that they
        can be investigated by AI and suggested on screen"""

        self.visibility_timer -= 1

        if self.visibility_timer < 0:
            self.visibility_timer = 12
            visibility_dict = {}

            seen_agents = []

            for agent_key in self.agents:
                agent = self.agents[agent_key]
                agent.set_visible(False)
                agent.set_seen(False)
                agent.set_suspect(False)

            for agent_key in self.agents:
                agent = self.agents[agent_key]

                if not agent.dead:
                    enemy = agent.team != 0
                    visibility_distance = agent.get_visual_range()
                    max_distance = visibility_distance * 8
                    suspect_distance = max_distance * 1.5

                    if not enemy:
                        visibility_dict[agent_key] = {"enemy": enemy, "distance": visibility_distance,
                                                      "location": agent.location}
                        if self.inside_camera(agent):
                            agent.set_visible(True)

                        for enemy_key in self.agents:
                            enemy = self.agents[enemy_key]

                            if enemy.team != 0:
                                if enemy_key not in seen_agents:
                                    distance = agent.box.getDistanceTo(enemy.box)
                                    if distance <= max_distance:
                                        seen_agents.append(enemy_key)
                                        enemy.set_seen(True)
                                        enemy.set_visible(True)
                                        visibility_dict[enemy_key] = {"enemy": True, "distance": 0,
                                                                      "location": enemy.location}

                                    elif distance < suspect_distance:
                                        enemy.set_suspect(True)

                            else:
                                if enemy.dead:
                                    distance = agent.box.getDistanceTo(enemy.box)
                                    if distance <= max_distance:
                                        if self.inside_camera(enemy):
                                            enemy.set_visible(True)

                    else:
                        for player_key in self.agents:
                            player = self.agents[player_key]

                            if player.team == 0:
                                if player_key not in seen_agents:
                                    distance = agent.box.getDistanceTo(player.box)
                                    if distance <= max_distance:
                                        seen_agents.append(player_key)
                                        player.set_seen(True)
                                    elif distance < suspect_distance:
                                        player.set_suspect(True)

            self.LOS.do_paint(visibility_dict)

    def update(self):
        self.camera_controller.update()
        self.game_audio.update()
        self.mouse_update()
        self.agent_update()
        self.particle_update()
        self.user_interface_update()
        self.sound_update()
        self.process_commands()
        self.visibility_update()
