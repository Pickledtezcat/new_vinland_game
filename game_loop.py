import bge
import game_input
import bgeutils
from menus import StartMenu, ProfileManagerMenu, VehicleManagerMenu, VehicleOptionMenu
from levels import Level


class DebugPrinter(object):
    def __init__(self, manager):
        self.manager = manager
        self.debug_text = bgeutils.get_ob("debug_text", self.manager.main_camera.children)
        self.debug_text.resolution = 8
        self.timer = 0
        self.debug_list = []
        self.debug_timer = {}

    def update(self):

        debug_text = ""
        self.timer += 1

        if "info" in self.manager.game_input.keys:
            if self.timer > 50:
                self.timer = 0

                sorted_keys = sorted([key for key in self.debug_timer])

                for debug_key in sorted_keys:
                    debug_text = "{}{}:{}\n".format(debug_text, debug_key, self.debug_timer[debug_key])

                self.debug_text["Text"] = debug_text

        else:
            debug_text = ""
            next_generation = []

            for item in self.debug_list:
                details = item[0]
                debug_text = "{}\n{}".format(details, debug_text)
                item[1] -= 1

                if item[1] > 0:
                    next_generation.append(item)

            self.debug_text["Text"] = debug_text
            self.debug_list = next_generation

    def printer(self, data, label="", decay=0):
        info = "{}:{}".format(label, data)
        self.debug_list.append([info, decay])


class GameLoop(object):

    def __init__(self, cont):
        bge.texture.setLogFile(bge.logic.expandPath("//saves/error_log.txt"))

        self.debug = True
        self.cont = cont
        self.own = cont.owner
        self.scene = self.own.scene
        self.main_camera = self.scene.active_camera
        self.debugger = DebugPrinter(self)

        self.game_input = game_input.GameInput()
        self.level = None

        bgeutils.load_settings()
        self.set_level()

    def update(self):
        self.input_update()
        self.debugger_update()
        self.level_update()

    def input_update(self):
        self.game_input.update()

    def debugger_update(self):
        self.debugger.update()

    def set_mode(self):

        next_menu_mode = "Menu" in bge.logic.globalDict["next_level"]
        current_menu_mode = bge.logic.globalDict["game_mode"] == "MENU_MODE"

        if next_menu_mode != current_menu_mode:
            if next_menu_mode:
                bge.logic.globalDict["game_mode"] = "MENU_MODE"
                bgeutils.save_settings()
                bge.logic.startGame("{}{}".format(bge.logic.expandPath("//"), "menu_blend.blend"))

            else:
                bge.logic.globalDict["game_mode"] = "GAME_MODE"
                bgeutils.save_settings()
                bge.logic.startGame("{}{}".format(bge.logic.expandPath("//"), "game_blend.blend"))

            bge.logic.globalDict["mode_change"] = True

    def end_level(self):
        if self.level:
            self.level.terminate()
            self.level = None
            return True

    def set_level(self):

        if bge.logic.globalDict["next_level"]:
            level_class = globals()[bge.logic.globalDict["next_level"]]
        else:
            level_class = globals()["StartMenu"]

        self.level = level_class(self)

        bge.logic.globalDict["next_level"] = None
        bgeutils.save_settings()

    def level_update(self):

        if bge.logic.globalDict["next_level"]:
            if not self.end_level() or "Menu" in bge.logic.globalDict["next_level"]:
                if not bge.logic.globalDict["mode_change"]:
                    self.set_mode()

                if not bge.logic.globalDict["mode_change"]:
                    self.set_level()

        if not bge.logic.globalDict["next_level"]:
            if not self.level.loaded:
                self.level.load()

            if self.level.loaded:
                self.level.update()






