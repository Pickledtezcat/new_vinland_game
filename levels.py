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
import map_generation
import bullets
import builder_tools
import static_dicts


class VisibilityMarker(object):
    def __init__(self, level, location):
        self.level = level
        self.marker_id = "visibility_marker_{}".format(self.level.get_new_id())
        self.decay = 18.0
        self.location = location

        self.level.visibility_markers.append(self)

    def update(self):
        self.decay = max(0.0, self.decay - 0.05)


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
        box_vector = mathutils.Vector(self.end) - mathutils.Vector(self.start)
        box_size = box_vector.length

        x_limit = sorted([self.start[0], self.end[0]])
        y_limit = sorted([self.start[1], self.end[1]])

        if box_size < 0.01:
            friends = [friend_id for friend_id in self.over_units if self.level.agents[friend_id].team == 0]
        else:
            friends = []

        message = {"label": "SELECT", "x_limit": x_limit, "y_limit": y_limit, "additive": additive, "friends": friends}

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
            selected_agents = [self.level.agents[agent_id] for agent_id in self.level.agents if
                               self.level.agents[agent_id].selected]

            if selected_agents:
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

                selected_agents = [self.level.agents[agent_id] for agent_id in self.level.agents if
                                   self.level.agents[agent_id].selected]

                if selected_agents:
                    building = self.level.buildings.get(self.mouse_over["building"])
                    if building:
                        if not building.occupier:
                            self.context = "BUILDING"
                            click = "right_button" in self.level.manager.game_input.buttons

                            if click:
                                target_id = self.mouse_over["building"]
                                message = {"label": "ENTER_BUILDING", "target_id": target_id}

                                for agent in selected_agents:
                                    agent.commands.append(message)

                        else:
                            occupying_agent = self.level.agents[building.occupier]
                            if occupying_agent.team != 0:
                                enemy_occupier = building.occupier
                                self.context = "TARGET"
                                click = "right_button" in self.level.manager.game_input.buttons

                                if click:
                                    message = {"label": "TARGET_ENEMY", "target_id": enemy_occupier}

                                    for agent in selected_agents:
                                        agent.commands.append(message)

                            else:
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
        self.visibility_markers = []
        self.mouse_control = MouseControl(self)
        self.paused = False
        self.map_size = 128
        self.level_id_index = 0
        self.loaded = False
        self.visibility_timer = 0
        self.LOS = None
        self.terrain = None

        self.agents_added = False
        self.buildings_added = False
        self.buildings_mapped = False

        self.world_dict = static_dicts.get_world("summer")

        self.map = {}
        self.agents = {}
        self.buildings = {}
        self.particles = []
        self.decals = []
        self.artillery_bullets = []
        # TODO add bullets, for artillery weapons

        self.factions = {0: "HRE",
                         1: "VIN"}

        hre_infantry_path = bge.logic.expandPath("//infantry_sprites/hre_summer_sprites.blend")
        vin_infantry_path = bge.logic.expandPath("//infantry_sprites/vin_summer_sprites.blend")
        vehicle_path = bge.logic.expandPath("//models/vehicles.blend")

        self.infantry_textures = []
        self.assets = []

        if not self.manager.assets_loaded:
            self.assets.append(bge.logic.LibLoad(hre_infantry_path, "Scene"))
            self.assets.append(bge.logic.LibLoad(vin_infantry_path, "Scene"))
            self.assets.append(bge.logic.LibLoad(vehicle_path, "Scene"))
            self.manager.assets_loaded = True

        self.load_dict = None
        load_name = bge.logic.globalDict["profiles"][bge.logic.globalDict["active_profile"]]["saved_game"]
        if load_name:
            self.load_dict = bgeutils.load_level()
            self.load_level(self.load_dict)

    def get_new_id(self):
        new_id = self.level_id_index
        self.level_id_index += 1
        return new_id

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

        if not self.infantry_textures:
            self.load_infantry_textures()
            return False

        if not self.buildings_mapped:
            self.get_buildings()
            return False

        if not self.agents_added:
            self.add_agents()

        return True

    def load_infantry_textures(self):
        texture_list = ["hre_summer_texture", "vin_summer_texture", "vin_vehicles_texture"]
        for texture in texture_list:
            owner = self.scene.addObject(texture, self.own, 0)
            owner.worldPosition.z = 300
            texture_set = {"name": texture, "saved": None, "owner": owner}
            self.infantry_textures.append(texture_set)

        self.LOS = LOS.VisionPaint(self)

    def get_tile(self, tile_key, fallback=None):
        if 0 < tile_key[0] < self.map_size and 0 < tile_key[1] < self.map_size:
            map_key = bgeutils.get_key(tile_key)

            return self.map[map_key]
        return fallback

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
                            "building": None, "terrain": 1}

                    map[bgeutils.get_key((x, y))] = tile

        self.map = map
        self.terrain = map_generation.BaseMapGen(self)

    def paint_around(self, x, y):
        paint_array = [[1, 0], [1, 1], [0, 1], [1, -1], [-1, 0], [-1, 1], [0, -1], [-1, -1]]

        for p in paint_array:
            neighbor_key = (x + p[0], y + p[1])
            self.set_tile(neighbor_key, "terrain", 255)

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
                    self.paint_around(x, y)

        for building_id in self.buildings:
            building = self.buildings[building_id]
            for door_loc in building.doors:
                self.set_tile(door_loc, "building", None)

        self.terrain.paint_map()
        # TODO find another way of updating terrain
        self.terrain.canvas.refresh(True)
        self.terrain.normal.refresh(True)
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

        try:
            del self.LOS.canvas

            for texture_set in self.infantry_textures:
                del texture_set["saved"]
        except:
            print("error on exit")

    def add_agents(self):

        vehicle_testing = True

        # for friend in range(4):
        #     agents.Vehicle(self, None, [35 + (10 * friend), 55], 0)

        infantry = ["GRENADIERS", "HEAVY_SUPPORT_TEAM", "SUPPORT_41", "SUPPORT_39", "PARATROOPERS"]

        for friend in range(5):
            agents.Infantry(self, random.choice(infantry), [35 + (10 * friend), 60], 0)

        # agents.Infantry(self, "SUPPORT_36", [35, 25], 0)

        # for enemy in range(4):
        #     agents.Vehicle(self, None, [35 + (10 * enemy), 35], 1)

        if vehicle_testing:
            vehicles = builder_tools.load_testing_vehicles()
            bge.logic.globalDict["profiles"][bge.logic.globalDict["active_profile"]]["vehicles"] = vehicles
            vehicle_keys = [v_key for v_key in vehicles]
            for v in range(len(vehicle_keys)):
                # TODO set agent type based on vehicle
                vehicle = vehicles[vehicle_keys[v]]

                team = random.choice([0, 1])
                if team == 0:
                    y = 50
                else:
                    y = 15

                agents.Vehicle(self, vehicle_keys[v], [35 + (10 * v), y], team)

        for enemy in range(5):
            agents.Infantry(self, random.choice(infantry), [35 + (10 * enemy), 25], 1)

        self.agents_added = True

    def add_buildings(self):

        buildings.Building(self, "basic_house", [35, 35], [-1, 1])
        buildings.Building(self, "basic_house", [45, 35], [1, 0])
        buildings.Building(self, "basic_house", [55, 35], [0, 1])

        self.buildings_added = True

    def load_level(self, load_dict):

        level_details = load_dict["level_details"]

        self.camera_controller.camera_hook.worldPosition = level_details["camera_position"]
        self.camera_controller.zoom_in = level_details["camera_zoom_in"]
        self.camera_controller.zoom_timer = level_details["camera_zoom_timer"]
        self.level_id_index = level_details["level_id_index"]

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

        bullet_list = load_dict["bullets"]
        self.load_bullets(bullet_list)

        decal_list = load_dict["decals"]
        self.load_decals(decal_list)

        self.agents_added = True
        self.buildings_added = True
        self.buildings_mapped = True

        self.terrain = map_generation.BaseMapGen(self, loaded=True)
        self.terrain.paint_map()

    def save_level(self):

        camera_position = list(self.camera_controller.camera_hook.worldPosition.copy())
        camera_zoom_in = self.camera_controller.zoom_in
        camera_zoom_timer = self.camera_controller.zoom_timer
        level_id_index = self.level_id_index

        level_details = {"camera_position": camera_position, "camera_zoom_in": camera_zoom_in,
                         "camera_zoom_timer": camera_zoom_timer, "level_id_index": level_id_index}

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

        bullet_list = self.save_bullets()
        decal_list = self.save_decals()

        level_details = {"map": saved_map,
                         "level_details": level_details,
                         "buildings": saving_buildings,
                         "agents": saving_agents,
                         "bullets": bullet_list,
                         "decals": decal_list}

        bgeutils.save_level(level_details)
        bge.logic.globalDict["next_level"] = "StartMenu"

    def save_bullets(self):
        bullet_list = []

        for bullet in self.artillery_bullets:
            agent_id = bullet.agent.agent_id
            curve = bullet.curve
            bullet_type = bullet.bullet_type
            damage = bullet.damage
            index = bullet.index
            timer = bullet.timer

            bullet_dict = {"agent_id": agent_id,
                           "curve": curve,
                           "bullet_type": bullet_type,
                           "damage": damage,
                           "index": index,
                           "timer": timer}

            bullet_list.append(bullet_dict)

        print(bullet_list)

        return bullet_list

    def load_bullets(self, bullet_list):

        for bullet in bullet_list:
            agent_id = bullet["agent_id"]
            curve = bullet["curve"]
            bullet_type = bullet["bullet_type"]
            damage = bullet["damage"]
            index = bullet["index"]
            timer = bullet["timer"]

            if bullet_type == "GRENADE":
                bullets.Grenade(self, curve, None, damage, timer=timer, index=index, agent_id=agent_id)
            if bullet_type == "ROCKET":
                bullets.Rocket(self, curve, None, damage, timer=timer, index=index, agent_id=agent_id)
            if bullet_type == "SHELL":
                bullets.Shell(self, curve, None, damage, timer=timer, index=index, agent_id=agent_id)

    def save_decals(self):

        decal_list = []

        for decal in self.decals:
            decal_object = decal["game_ob"]
            transform = [list(row) for row in decal_object.worldTransform.row]
            scale = decal["scale"]
            mesh_name = decal["mesh"]

            decal_dict = {"mesh": mesh_name, "scale": scale, "transform": transform}

            decal_object.endObject()
            decal_list.append(decal_dict)

        return decal_list

    def load_decals(self, decal_list):

        for decal in decal_list:
            decal_ob = self.scene.addObject(decal["mesh"], self.own, 0)
            decal_ob.worldTransform = decal["transform"]
            s = decal["scale"]
            decal_ob.localScale = [s, s, s]
            decal_ob.color = self.world_dict["dirt_color"]

            crater_dict = {"game_ob": decal_ob, "mesh": decal["mesh"], "scale": decal["scale"]}
            self.decals.append(crater_dict)

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

    def bullets_update(self):
        next_generation = []

        for bullet in self.artillery_bullets:
            if not bullet.done:
                bullet.update()
                next_generation.append(bullet)
            else:
                bullet.terminate()

        self.artillery_bullets = next_generation

    def user_interface_update(self):
        # TODO write a full interface with button control
        # TODO use commands to control AI, including selection groups
        if "pause" in self.manager.game_input.keys:
            self.paused = not self.paused

        player_agents = []
        for agent_key in self.agents:
            agent = self.agents[agent_key]
            if agent.team == 0:
                player_agents.append(agent)

        command = None

        if "a" in self.manager.game_input.keys:
            command = {"label": "STANCE_CHANGE", "stance": "AGGRESSIVE"}
        if "s" in self.manager.game_input.keys:
            command = {"label": "STANCE_CHANGE", "stance": "SENTRY"}
        if "d" in self.manager.game_input.keys:
            command = {"label": "STANCE_CHANGE", "stance": "DEFEND"}
        if "f" in self.manager.game_input.keys:
            command = {"label": "STANCE_CHANGE", "stance": "FLANK"}

            # TODO experiment with making troops knocked out

            # for agent in player_agents:
            #     if agent.selection_group == 2:
            #         agent.knocked_out = True

        number_command = None

        additive = "shift" in self.manager.game_input.keys
        setting = "control" in self.manager.game_input.keys

        for n in range(10):
            number_key = str(n)
            if number_key in self.manager.game_input.keys:
                number_command = {"label": "GROUP_SELECT", "additive": additive, "setting": setting, "number": n}

        for agent in player_agents:
            if command and agent.selected:
                agent.commands.append(command)
            if number_command:
                agent.commands.append(number_command)

        self.manager.debugger.printer(self.paused, "paused")
        self.user_interface.update()

        if "2" in self.manager.game_input.keys:
            for agent_key in self.agents:
                agent = self.agents[agent_key]
                if agent.team != 0 and not agent.enter_building:
                    buildings = [building_key for building_key in self.buildings]
                    building_choice = random.choice(buildings)
                    agent.mount_building(building_choice)

        if "escape" in self.manager.game_input.keys:
            self.save_level()

    def small_arms_shoot(self, command):

        agent = command["agent"]
        weapon = command["weapon"]
        origin = command["origin"]

        target = agent.agent_targeter.enemy_target
        if target:
            target_distance = agent.agent_targeter.target_distance
            effective_range = weapon.effective_range

            if target.agent_type == "INFANTRY":
                closest_soldier = agent.agent_targeter.closest_soldier
                power = weapon.power * random.uniform(0.0, 1.0)
                shock = power
                if closest_soldier:

                    if agent.agent_type != "INFANTRY":
                        if not agent.movement.done:
                            effective_range *= 0.5

                    building = self.buildings.get(closest_soldier.in_building)

                    if building:
                        power *= building.damage_reduction
                        target_position = building.get_closest_window(origin)
                        shock *= building.damage_reduction

                    else:
                        target_position = closest_soldier.box.worldPosition.copy()
                        target_position.z += 0.5

                    if closest_soldier.behavior.prone:

                        if target_distance > 10:
                            shock *= 0.5
                            effective_range *= 0.5

                    to_hit = (effective_range / target_distance) * 0.25
                    target_hit = to_hit > random.uniform(0.0, 1.0)

                    if target_hit:

                        damage = int(power)
                        if power < closest_soldier.toughness:
                            damage *= 0.5

                        closest_soldier.toughness -= max(1, int(damage))

                    else:
                        shock *= 0.5
                        base_location = closest_soldier.box.worldPosition.copy()
                        random_vector = mathutils.Vector(
                            [random.uniform(-3.0, 3.0), random.uniform(-3.0, 3.0), 0.0])
                        target_position = base_location + random_vector

                else:
                    shock *= 0.5
                    base_location = target.box.worldPosition.copy()
                    random_vector = mathutils.Vector(
                        [random.uniform(-3.0, 3.0), random.uniform(-3.0, 3.0), 0.0])
                    target_position = base_location + random_vector

                target.shock += shock

            else:
                variance = target.size
                random_vector = mathutils.Vector(
                    [random.uniform(-variance, variance), random.uniform(-variance, variance), 0.0])
                target_position = target.box.worldPosition.copy() + random_vector

                target_size = target.stats.turret_size + target.stats.chassis_size
                effective_range += target_size

                target_speed = round(target.speed * 100)
                effective_range -= target_speed

                to_hit = (effective_range / target_distance) * 0.25
                if to_hit > random.uniform(0.0, 1.0):
                    hit = {"label": "HIT", "origin": origin, "sector": None, "weapon": weapon, "agent": agent}
                    target.hits.append(hit)

            if agent.agent_type == "INFANTRY":
                particles.InfantryBullet(self, target_position, weapon, origin)
            else:
                rapid = ["QUICK", "RAPID"]

                instances = 1
                delay = 8
                if weapon.flag in rapid:
                    if weapon.flag == "RAPID":
                        delay = 4

                    instances = 3

                for i in range(instances):
                    particles.BulletFlash(self, weapon, delay=delay * i)
                    particles.BulletHitGround(self, list(target_position), delay=8 * i)

                    # TODO handle infantry weapons vs vehicles

    def shoot_shells(self, command):

        agent = command["agent"]
        weapon = command["weapon"]
        origin = command["origin"]

        target = agent.agent_targeter.enemy_target
        if target:
            target_distance = agent.agent_targeter.target_distance
            effective_range = weapon.effective_range
            scatter = target_distance / weapon.total_accuracy

            if target.agent_type == "INFANTRY":
                closest_soldier = agent.agent_targeter.closest_soldier
                if closest_soldier:
                    target_position = closest_soldier.box.worldPosition.copy()
                else:
                    target_position = target.center.copy()

                random_vector = mathutils.Vector(
                    [random.uniform(-scatter, scatter), random.uniform(-scatter, scatter), 0.0])

                target_position += random_vector
                command = {"label": "EXPLOSION", "effect": "EXPLOSION", "damage": weapon.power,
                           "position": target_position, "agent": agent}
                self.commands.append(command)

            else:
                # TODO handle vehicle vs vehicle shooting
                target_size = target.stats.turret_size + target.stats.chassis_size
                effective_range += target_size

                target_speed = round(target.speed * 100)
                effective_range -= target_speed

                to_hit = (effective_range / target_distance) * 0.25

                if to_hit < random.uniform(0.0, 1.0):
                    random_vector = mathutils.Vector(
                        [random.uniform(-scatter, scatter), random.uniform(-scatter, scatter), 0.0])

                    target_position = target.box.worldPosition.copy() + random_vector
                    command = {"label": "EXPLOSION", "effect": "EXPLOSION", "damage": weapon.power,
                               "position": target_position, "agent": agent}

                    self.commands.append(command)
                else:
                    hit = {"label": "HIT", "sector": None, "origin": origin, "weapon": weapon, "agent": agent}
                    target.hits.append(hit)

            rapid = ["QUICK", "RAPID"]

            instances = 1
            delay = 8
            if weapon.flag in rapid:
                if weapon.flag == "RAPID":
                    delay = 4

                instances = 3

            for i in range(instances):
                particles.BulletFlash(self, weapon, delay=delay * i)

    def shoot_artillery(self, command):

        agent = command["agent"]
        weapon = command["weapon"]
        hook = command["hook"]
        origin = hook.worldPosition.copy()

        target = agent.agent_targeter.enemy_target

        if not target:
            print("error firing {}".format(agent.agent_id))

        if target:
            closest_soldier = agent.agent_targeter.closest_soldier
            target_distance = agent.agent_targeter.target_distance

            accuracy = weapon.total_accuracy
            bullet = weapon.bullet
            effect = weapon.effect

            if closest_soldier:
                target_position = closest_soldier.box.worldPosition.copy()
            else:
                target_position = target.center.copy()

            scatter = max(1.0, target_distance / accuracy)

            scatter_vector = mathutils.Vector([random.uniform(- scatter, scatter) for _ in range(3)])
            target_position += scatter_vector

            high_point = target_distance * 0.3
            start = origin.copy()
            end = target_position
            mid_point = start.lerp(end, 0.5)

            start_handle = mid_point.copy()
            start_handle.z += high_point
            end_handle = target_position.copy()
            end_handle.z += high_point

            resolution = max(3, int(target_distance * 0.5))

            curve = mathutils.geometry.interpolate_bezier(start, start_handle, end_handle, end, resolution)
            bullet_arc = [list(point) for point in curve]

            if bullet == "GRENADE":
                bullets.Grenade(self, bullet_arc, agent, weapon.power)
            if bullet == "ROCKET":
                bullets.Rocket(self, bullet_arc, agent, weapon.power)
            if bullet == "SHELL":
                bullets.Shell(self, bullet_arc, agent, weapon.power)

            if effect:
                particles.BulletFlash(self, weapon)

    def explosion(self, command):

        agent = command["agent"]
        # TODO give xp etc... to owner passed as agent_id
        position = command["position"]
        location = [int(position[0]), int(position[1])]
        x, y = location

        target_tile = self.get_tile([x, y])

        if target_tile:
            effect = command["effect"]
            damage = command["damage"]

            #explosion_chart = [8, 16, 32, 64, 128, 256, 512, 1024, 2048, 4096]
            explosion_chart = [0, 16, 64, 256, 1024, 4096]

            max_fall_off = 0

            airburst = False
            occupier = target_tile["occupied"]
            if occupier:
                occupying_agent = self.agents[occupier]
                if occupying_agent.agent_type != "INFANTRY":
                    airburst = True

            building = target_tile["building"]
            if building:
                airburst = True

            if effect:
                if effect == "EXPLOSION":
                    particles.NormalExplosion(self, target_tile, damage, airburst=airburst)
                else:
                    particles.DummyExplosion(self, location)

            for i in range(5):
                fall_off = explosion_chart[i]
                if damage > fall_off:
                    max_fall_off = i

            max_fall_off = min(5, max_fall_off + 2)

            buildings_hit = []
            vehicles_hit = []

            for ex in range(-max_fall_off, max_fall_off):
                for ey in range(-max_fall_off, max_fall_off):
                    damage_reduction = explosion_chart[abs(ex)]
                    shock_reduction = explosion_chart[max(0, abs(ex) - 1)]

                    effective_damage = max(0.0, damage - damage_reduction) * random.uniform(0.0, 1.0)
                    shock = max(0.0, damage - shock_reduction) * random.uniform(0.0, 1.0)

                    if damage > 0.0 or shock > 0.0:
                        explosion_key = [x + ex, y + ey]
                        tile = self.get_tile(explosion_key)
                        if tile:
                            building_id = tile["building"]
                            if building_id:
                                if building_id not in buildings_hit:
                                    buildings_hit.append(building_id)

                            occupant = tile["occupied"]
                            if occupant:
                                target_agent = self.agents.get(occupant)

                                if target_agent:
                                    if target_agent.agent_type == "INFANTRY":
                                        soldier_list = [soldier for soldier in target_agent.soldiers if
                                                        soldier.location == explosion_key]
                                        if soldier_list:
                                            soldier = soldier_list[0]
                                            personal_damage = effective_damage
                                            if not soldier.in_building:
                                                if soldier.behavior.prone:
                                                    shock *= 0.5
                                                    personal_damage *= 0.5

                                                if personal_damage > 0.0:
                                                    if personal_damage < soldier.toughness:
                                                        personal_damage *= 0.5
                                                        shock *= 0.5

                                                    soldier.toughness -= max(1, int(personal_damage))

                                                if shock > 0.0:
                                                    target_agent.shock += shock
                                    else:
                                        if occupant not in vehicles_hit:
                                            vehicles_hit.append(occupant)

            if vehicles_hit:
                for vehicle_key in vehicles_hit:
                    vehicle = self.agents[vehicle_key]

                    explosive_distance = int((vehicle.center.copy() - position.copy()).length)
                    explosive_distance = min(5, explosive_distance)

                    explosive_reduction = explosion_chart[explosive_distance]
                    effective_vehicle_damage = max(0.0, damage - explosive_reduction)

                    if effective_vehicle_damage > 1.0:
                        hit = {"label": "SPLASH_DAMAGE", "sector": None,
                               "damage": effective_vehicle_damage,
                               "origin": position.copy(), "agent": agent}
                        vehicle.hits.append(hit)

            if buildings_hit:
                for building_key in buildings_hit:

                    building = self.buildings[building_key]
                    explosive_distance = int((building.box.worldPosition.copy() - position.copy()).length)
                    explosive_distance = min(5, explosive_distance)

                    explosive_reduction = explosion_chart[explosive_distance]

                    in_building_damage = max(0.0, damage - explosive_reduction) * building.damage_reduction

                    building_occupant = building.occupier

                    if building_occupant:
                        hit_agent = self.agents[building_occupant]
                        if explosive_distance < 2:
                            hit_agent.shock += in_building_damage

                        if in_building_damage > 0.0:
                            for soldier in hit_agent.soldiers:
                                personal_damage = in_building_damage

                                if soldier.in_building:
                                    if personal_damage > 0.0:
                                        personal_damage *= random.uniform(0.0, 1.0)

                                        if personal_damage < soldier.toughness:
                                            personal_damage *= 0.5

                                        soldier.toughness -= max(1, int(personal_damage))

    def process_commands(self):

        for command in self.commands:

            if command["label"] == "VISIBILITY_MARKER":
                location = command["location"]
                VisibilityMarker(self, location)

            if command["label"] == "SMALL_ARMS":
                self.small_arms_shoot(command)

            if command["label"] == "SHOOT_SHELLS":
                self.shoot_shells(command)

            if "ARTILLERY" in command["label"]:
                self.shoot_artillery(command)

            if "EXPLOSION" in command["label"]:
                self.explosion(command)

            if command["label"] == "SOUND_EFFECT":
                sound, owner, attenuation, volume_scale = command["content"]
                if not owner:
                    owner = self.listener

                sound = self.game_audio.sound_effect(sound, owner, attenuation=attenuation, volume_scale=volume_scale)
                sound.pitch = random.uniform(0.9, 1.1)

        self.commands = []

    def load(self):
        if self.check_level_loaded():
            self.loaded = True

    def visibility_update(self):

        """visible means the agent can be seen on screen, seen means they can be targeted by AI, suspect means that they
        can be investigated by AI and suggested on screen"""

        if self.LOS:
            visibility_dict = {}

            next_generation = []

            for marker in self.visibility_markers:
                marker.update()
                location = marker.location
                decay = marker.decay
                marker_id = marker.marker_id

                visibility_dict[marker_id] = {"enemy": False, "distance": round(decay),
                                              "location": location, "decayed": True}

                if decay > 0.0:
                    next_generation.append(marker)

            self.visibility_markers = next_generation

            self.visibility_timer -= 1

            if self.visibility_timer < 0:
                self.visibility_timer = 12

                seen_agents = []

                for agent_key in self.agents:
                    agent = self.agents[agent_key]
                    agent.set_seen(False)
                    agent.set_suspect(False)

                for agent_key in self.agents:
                    agent = self.agents[agent_key]
                    knocked_out = agent.knocked_out

                    if not agent.dead and not agent.knocked_out:
                        is_enemy = agent.team != 0

                        visibility_distance = agent.get_visual_range()

                        max_distance = 17
                        suspect_distance = max_distance * 2.0

                        if not is_enemy:
                            position = agent.center.copy()
                            location = bgeutils.position_to_location(position)

                            visibility_dict[agent_key] = {"enemy": is_enemy, "distance": visibility_distance,
                                                          "location": location, "decayed": False}

                            for enemy_key in self.agents:
                                enemy = self.agents[enemy_key]

                                if enemy.team != 0:
                                    if not knocked_out:
                                        if enemy_key not in seen_agents:
                                            closest_soldier, target_vector = enemy.get_target(agent)
                                            enemy_distance = target_vector.length

                                            if enemy_distance <= max_distance:
                                                seen_agents.append(enemy_key)
                                                enemy.set_seen(True)
                                                visibility_dict[enemy_key] = {"enemy": True, "distance": 0,
                                                                              "location": enemy.location,
                                                                              "decayed": False}

                                            elif enemy_distance < suspect_distance:
                                                enemy.set_suspect(True)

                        else:
                            for player_key in self.agents:
                                player = self.agents[player_key]

                                if player.team == 0:
                                    if player_key not in seen_agents:
                                        closest_soldier, target_vector = player.get_target(agent)
                                        player_distance = target_vector.length

                                        if player_distance <= max_distance:
                                            seen_agents.append(player_key)
                                            player.set_seen(True)
                                        elif player_distance < suspect_distance:
                                            player.set_suspect(True)

                self.LOS.do_paint(visibility_dict)

    def update(self):
        self.camera_controller.update()
        self.game_audio.update()
        self.mouse_update()
        self.agent_update()

        self.user_interface_update()
        self.process_commands()

        if not self.paused:
            self.bullets_update()
            self.particle_update()
            self.visibility_update()

