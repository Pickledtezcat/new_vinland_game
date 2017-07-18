import bge
import mathutils
import bgeutils
import builder_tools
import vehicle_parts


parts_dict = vehicle_parts.get_vehicle_parts()
color_dict = vehicle_parts.color_dict

status_dict = {"ammo": "yellow",
               "empty": "red",
               "carrying": "green",
               "disabled": "yellow",
               "knocked_out": "red",
               "shocked": "yellow",
               "broken": "red",
               "damaged": "red",
               "sentry": "green",
               "nothing": "green"}


class UserInterface(object):
    def __init__(self, level):

        self.level = level
        self.camera = self.level.scene.active_camera
        self.cursor = self.level.scene.addObject("movement_cursor", self.level.own, 0)
        self.cursor.setParent(self.camera)
        self.bounding_box = self.level.scene.addObject("bounding_box", self.level.own, 0)
        self.status_bars = {}

    def terminate(self):
        self.cursor.endObject()
        self.bounding_box.endObject()

        for status_bar_key in self.status_bars:
            status_bar = self.status_bars[status_bar_key]
            status_bar.terminate()

    def set_bounding_box(self, hide, start, end):

        if hide:
            self.bounding_box.visible = False
        else:
            self.bounding_box.visible = True

            x_limit = sorted([start[0], end[0]])
            y_limit = sorted([start[1], end[1]])

            start_hit = self.mouse_ray((x_limit[0], y_limit[0]))
            end_hit = self.mouse_ray((x_limit[1], y_limit[1]))
            corner_hit = self.mouse_ray((x_limit[1], y_limit[0]))

            start_vector = start_hit[1]
            end_vector = end_hit[1]
            corner_vector = corner_hit[1]

            x_length = (corner_vector - start_vector).length
            y_length = (end_vector - corner_vector).length

            self.bounding_box.worldPosition = start_vector
            self.bounding_box.worldOrientation = self.camera.worldOrientation
            self.bounding_box.localScale.x = x_length
            self.bounding_box.localScale.y = y_length

    def mouse_ray(self, position):
        x, y = position

        camera = self.camera
        screen_vect = camera.getScreenVect(x, y)
        target_position = camera.worldPosition - screen_vect
        mouse_hit = camera.rayCast(target_position, camera, 7.0, "cursor_plane", 0, 1, 0)

        return mouse_hit

    def update(self):

        mouse_hit = self.mouse_ray(self.level.manager.game_input.virtual_mouse)

        if mouse_hit[0]:

            location = mouse_hit[1]
            normal = mouse_hit[2]

            if self.level.mouse_control.context == "TARGET":
                self.cursor.replaceMesh("target_cursor")
            elif self.level.mouse_control.context == "SELECT":
                self.cursor.replaceMesh("select_cursor")
            elif self.level.mouse_control.context == "BUILDING":
                self.cursor.replaceMesh("building_cursor")
            elif self.level.mouse_control.context == "NO_ENTRY":
                self.cursor.replaceMesh("no_entry_cursor")
            else:
                self.cursor.replaceMesh("movement_cursor")

            self.cursor.worldPosition = location
            self.cursor.worldOrientation = normal.to_track_quat("Z", "Y")

        visible_agents = [agent_key for agent_key in self.level.agents if
                          self.level.agents[agent_key].visible and not self.level.agents[agent_key].dead]

        for screen_agent_key in visible_agents:
            if screen_agent_key not in self.status_bars:
                self.status_bars[screen_agent_key] = StatusBar(self, screen_agent_key)

        status_bar_keys = [bar_key for bar_key in self.status_bars]

        for status_bar_key in status_bar_keys:
            status_bar = self.status_bars[status_bar_key]
            if not status_bar.agent.visible or status_bar.agent.dead:
                status_bar.terminate()
                del self.status_bars[status_bar_key]
            else:
                status_bar.update()


class StatusBar(object):
    def __init__(self, ui, agent_key):
        self.ui = ui
        self.level = self.ui.level
        self.agent = self.level.agents[agent_key]
        self.box = self.add_box()
        self.stance_icon = bgeutils.get_ob("stance_icon", self.box.children)
        self.health_bar = bgeutils.get_ob("health_bar", self.box.childrenRecursive)
        self.shock_bar = bgeutils.get_ob("shock_bar", self.box.childrenRecursive)
        self.group_number_icon = bgeutils.get_ob("group_number", self.box.children)
        self.rank_icon = bgeutils.get_ob("rank_icon", self.box.children)
        self.status_icon = bgeutils.get_ob("status_icon", self.box.children)

        self.group_number = None
        self.stance = None
        self.rank = None
        self.status = None

        self.status_icon.visible = False
        self.stance_icon.visible = False
        self.group_number_icon.visible = False
        self.rank_icon.visible = False

        self.green = [0.0, 1.0, 0.0, 1.0]
        self.red = [1.0, 0.0, 0.0, 1.0]
        self.yellow = [0.5, 0.5, 0.0, 1.0]
        self.hud = [0.07, 0.6, 0.05, 1.0]

        self.health_bar.color = self.green
        self.shock_bar.color = self.red
        self.shock_bar.localScale.x = 0.0

        self.status_icon.color = self.hud
        self.stance_icon.color = self.hud
        self.group_number_icon.color = self.hud
        self.rank_icon.color = self.hud

    def terminate(self):
        self.box.endObject()

    def add_box(self):
        return self.level.scene.addObject("status_bar_object", self.level.own, 0)

    def update_health(self):

        initial_health = self.agent.initial_health

        if self.agent.agent_type == "INFANTRY":

            health = 0
            for soldier in self.agent.soldiers:
                health += max(0, soldier.toughness)

        else:
            health = self.agent.health

        if initial_health > 0:
            health_ratio = health / self.agent.initial_health
            self.health_bar.localScale.x = health_ratio

            if health_ratio < 0.1:
                self.health_bar.color = self.red
            elif health_ratio < 0.5:
                self.health_bar.color = self.yellow
            else:
                self.health_bar.color = self.green

        shock_ratio = bgeutils.map_value(0.0, 50.0, self.agent.shock)
        self.shock_bar.localScale.x = min(1.0, shock_ratio)

    def secondary_icons(self, setting):

        self.stance_icon.visible = setting

        if setting:

            stance = self.agent.stance
            if self.stance != stance:
                self.stance = stance
                self.stance_icon.replaceMesh("UI_stance_{}".format(self.agent.stance))

            group_number = self.agent.selection_group

            if group_number:
                self.group_number_icon.visible = setting
                if group_number != self.group_number:
                    self.group_number = group_number
                    self.group_number_icon.replaceMesh("group_number_{}".format(group_number))

            rank_number = self.agent.rank
            if rank_number:
                self.rank_icon.visible = setting
                if self.rank != rank_number:
                    self.rank = rank_number
                    self.rank_icon.replaceMesh("rank_icon_{}".format(rank_number))

        else:
            self.rank_icon.visible = setting
            self.group_number_icon.visible = setting

        # TODO do other secondary icons (status, rank)

    def set_status_icon(self):
        status = self.get_status()
        if status == "noting":
            self.status_icon.visible = False
        else:
            self.status_icon.visible = True

            if status != self.status:
                self.status = status
                status_color = status_dict[self.status]
                self.status_icon.replaceMesh("status_{}".format(self.status))
                set_color = self.green
                if status_color == "yellow":
                    set_color = self.yellow
                if status_color == "red":
                    set_color = self.red
                self.status_icon.color = set_color

    def get_status(self):

        if self.agent.knocked_out:
            return "knocked_out"

        if self.agent.is_carrying:
            return "carrying"

        if self.agent.is_shocked == 1:
            return "broken"

        if self.agent.is_damaged == 1:
            return "disabled"

        if self.agent.has_ammo < 0:
            return "empty"

        if self.agent.is_shocked == 0:
            return "shocked"

        if self.agent.has_ammo < 1:
            return "ammo"

        if self.agent.is_damaged == 0:
            return "damaged"

        if self.agent.is_sentry:
            return "sentry"

        return "nothing"

    def update_position(self):

        if self.agent.agent_type == "INFANTRY":
            position = self.agent.get_infantry_center()
            if not position:
                self.box.localScale = [0.0, 0.0, 0.0]
                position = self.agent.box.worldPosition.copy()
        else:
            position = self.agent.box.worldPosition.copy()

        position.z += 2.5

        location = self.ui.camera.getScreenPosition(position)
        ray = self.ui.mouse_ray(location)
        if ray[0]:
            plane, screen_position, screen_normal = ray
            self.box.worldPosition = screen_position
            self.box.worldOrientation = screen_normal.to_track_quat("Z", "Y")

    def update(self):

        if self.agent.team == 0:
            self.update_health()
            self.update_position()
            self.set_status_icon()
            if self.agent.selected:
                self.secondary_icons(True)
            else:
                self.secondary_icons(False)

        else:
            if not self.agent.seen:
                self.box.localScale = [0.0, 0.0, 0.0]
            else:
                self.update_health()
                self.update_position()
                self.set_status_icon()
                self.box.localScale = [1.0, 1.0, 1.0]
                self.secondary_icons(False)


class HoldingInventory(object):
    def __init__(self, interface):
        self.interface = interface
        self.cursor = self.interface.cursor
        self.holding = None
        self.rotated = False
        self.tiles = []

    def clear_tiles(self):
        for tile in self.tiles:
            tile.endObject()
        self.tiles = []

    def update(self):

        holding = bge.logic.globalDict["profiles"][bge.logic.globalDict["active_profile"]]["holding"]
        rotated = bge.logic.globalDict["profiles"][bge.logic.globalDict["active_profile"]]["rotated"]

        if holding != self.holding or rotated != self.rotated:
            self.clear_tiles()

            if holding:
                self.rotated = rotated
                self.holding = holding

                part = parts_dict[self.holding]
                part_x = part["x_size"]
                part_y = part["y_size"]

                if self.rotated:
                    part_x, part_y = part_y, part_x

                part_type = part["part_type"]
                part_color = color_dict[part_type.lower()]
                scale = 0.05

                for x in range(-1, part_x + 1):
                    for y in range(-1, part_y + 1):

                        search_array = [(1, 0, 1), (1, 1, 2), (0, 1, 4), (0, 0, 8)]
                        tile_number = 0

                        for n in search_array:
                            nx = x + n[0]
                            ny = y + n[1]

                            if 0 < nx < part_x + 1:
                                if 0 < ny < part_y + 1:
                                    tile_number += n[2]

                        if tile_number > 0:
                            tile_name = "m_parts.{}".format(str(tile_number).zfill(3))
                            tile = self.cursor.scene.addObject(tile_name, self.cursor, 0)
                            offset = mathutils.Vector([(x - 0.5) * scale, (y - 0.5) * scale, -0.02])
                            tile.worldPosition += offset
                            tile.setParent(self.cursor)
                            tile.color = part_color
                            tile.localScale *= scale
                            self.tiles.append(tile)


class MenuInterface(object):
    def __init__(self, menu):
        self.menu = menu
        self.manager = self.menu.manager
        self.cursor = self.manager.own.scene.addObject("movement_cursor", self.manager.own, 0)
        self.cursor.setParent(self.manager.main_camera)
        self.tool_tip = bgeutils.get_ob("tool_tip", self.cursor.children)
        self.tool_tip.resolution = 8
        self.tool_tip_background = bgeutils.get_ob("tool_tip_background", self.cursor.children)
        self.tool_tip_contents = "x"
        self.set_tool_tip()
        self.holding = HoldingInventory(self)

    def set_tool_tip(self):

        if self.menu.tool_tip_text != self.tool_tip_contents:
            self.tool_tip_contents = self.menu.tool_tip_text
            tool_tip_text = bgeutils.split_in_lines(self.menu.tool_tip_text, 18)

            self.tool_tip["Text"] = tool_tip_text
            lines = tool_tip_text.splitlines()
            width = 0
            for line in lines:
                line_width = len(line)
                if line_width > width:
                    width = line_width

            height = len(lines)

            x_scale = 0.0052
            y_scale = 0.0087

            self.tool_tip_background.localScale.x = x_scale * width
            self.tool_tip_background.localScale.y = y_scale * height

    def terminate(self):
        self.cursor.endObject()
        self.holding.clear_tiles()

    def mouse_ray(self, position):
        x, y = position

        camera = self.manager.main_camera
        screen_vect = camera.getScreenVect(x, y)
        target_position = camera.worldPosition - screen_vect
        mouse_hit = camera.rayCast(target_position, camera, 7.0, "cursor_plane", 0, 1, 0)

        return mouse_hit

    def update(self):
        self.set_tool_tip()
        self.holding.update()

        mouse_hit = self.mouse_ray(self.manager.game_input.virtual_mouse)

        if mouse_hit[0]:
            location = mouse_hit[1]

            # TODO add context sensitive cursor for menus

            # if self.menu.context == "TARGET":
            #     self.cursor.replaceMesh("target_cursor")
            # else:
            #     self.cursor.replaceMesh("movement_cursor")
            self.cursor.worldPosition = location
