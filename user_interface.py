import bge
import mathutils
import bgeutils


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
        self.group_number = bgeutils.get_ob("group_number", self.box.children)
        self.rank_icon = bgeutils.get_ob("rank_icon", self.box.children)
        self.status_icon = bgeutils.get_ob("status_icon", self.box.children)

        self.status_icon.visible = False
        self.stance_icon.visible = False
        self.group_number.visible = False
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
        self.group_number.color = self.hud
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

            if initial_health > 0:
                health_ratio = health / self.agent.initial_health
                self.health_bar.localScale.x = health_ratio

                if health_ratio < 0.1:
                    self.health_bar.color = self.red
                elif health_ratio < 0.5:
                    self.health_bar.color = self.yellow
                else:
                    self.health_bar.color = self.green

    def secondary_icons(self, setting):
        self.stance_icon.visible = setting

        if setting:
            self.stance_icon.replaceMesh("UI_stance_{}".format(self.agent.stance))

        # TODO do other secondary icons

    def update(self):
        self.update_health()

        position = self.agent.box.worldPosition.copy()
        position.z += 2.0
        location = self.ui.camera.getScreenPosition(position)
        ray = self.ui.mouse_ray(location)
        if ray[0]:
            plane, screen_position, screen_normal = ray
            self.box.worldPosition = screen_position
            self.box.worldOrientation = screen_normal.to_track_quat("Z", "Y")

        if self.agent.team == 0:
            if self.agent.selected:
                self.secondary_icons(True)
            else:
                self.secondary_icons(False)

        else:
            self.secondary_icons(False)


class MenuInterface(object):
    def __init__(self, level):
        self.level = level
        self.manager = self.level.manager
        self.cursor = self.manager.own.scene.addObject("movement_cursor", self.manager.own, 0)
        self.cursor.setParent(self.manager.main_camera)

    def terminate(self):
        self.cursor.endObject()

    def mouse_ray(self, position):
        x, y = position

        camera = self.manager.main_camera
        screen_vect = camera.getScreenVect(x, y)
        target_position = camera.worldPosition - screen_vect
        mouse_hit = camera.rayCast(target_position, camera, 7.0, "cursor_plane", 0, 1, 0)

        return mouse_hit

    def update(self):
        mouse_hit = self.mouse_ray(self.manager.game_input.virtual_mouse)

        if mouse_hit[0]:
            location = mouse_hit[1]

            # TODO add context sensitive cursor for menus

            # if self.level.context == "TARGET":
            #     self.cursor.replaceMesh("target_cursor")
            # else:
            #     self.cursor.replaceMesh("movement_cursor")
            self.cursor.worldPosition = location
