import bge
import camera_control
import game_input
import levels
import bgeutils
import time
import json
import menus


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
        self.debug = True
        self.load_settings()

        self.cont = cont
        self.own = cont.owner
        self.scene = self.own.scene
        self.main_camera = self.scene.active_camera
        self.debugger = DebugPrinter(self)

        self.game_input = game_input.GameInput()
        self.next_level = None
        self.level = None

        self.profile("set_level", one_time=True)

    def load_settings(self):
        in_path = bge.logic.expandPath("//saves/saves.txt")
        with open(in_path, "r") as infile:
            bge.logic.globalDict = json.load(infile)

        if not bge.logic.globalDict.get("version"):
            bge.logic.globalDict["version"] = "0.1a"
            bge.logic.globalDict["sounds"] = []
            bge.logic.globalDict["profiles"] = {}
            bge.logic.globalDict["current_game_mode"] = None
            bge.logic.globalDict["next_game_mode"] = "MENU_MODE"
            bge.logic.globalDict["next_level"] = None
            self.add_new_profile("Default Profile")
            self.save_settings()

    def save_settings(self):
        out_path = bge.logic.expandPath("//saves/saves.txt")
        with open(out_path, "w") as outfile:
            json.dump(bge.logic.globalDict, outfile)

    def add_new_profile(self, profile_name):
        default_profile = {"version": "0.1a", "volume": 1.0, "sensitivity": 0.95, "vehicles": {}, "editing": None,
                           "inventory": {}, "game_turn": 0, "faction": "vinland", "money": 5000, "saved_game": None}
        bge.logic.globalDict["profiles"][profile_name] = default_profile
        bge.logic.globalDict["active_profile"] = profile_name

    def update(self):
        self.profile("input_update")
        self.profile("debugger_update")
        self.profile("level_update")

    def input_update(self):
        self.game_input.update()

    def debugger_update(self):
        self.debugger.update()

    def set_level(self):
        # TODO finish designing menu/game interface
        # get level from globalDict and load it, switch from menu blend to game blend as required.

        if self.level:
            self.level.terminate()

        self.level = menus.StartMenu(self)#levels.Level(self, self.next_level)
        self.next_level = None

    def level_update(self):

        # temporary method for saving
        # from now save in active profile

        if "save" in self.game_input.keys:

            saving_agents = self.level.save_agents()
            saved_map = self.level.save_map()

            level_details = {"map": saved_map,
                             "agents": saving_agents}

            self.next_level = level_details

        if self.next_level:
            self.profile("set_level", one_time=True)
        else:
            if self.level.loaded:
                self.level.update()
            else:
                self.level.load()

    def profile(self, method_name, one_time=False):

        loop_methods = {"debugger_update": self.debugger_update,
                        "input_update": self.input_update,
                        "set_level": self.set_level,
                        "level_update": self.level_update}

        if method_name in loop_methods:
            timer = time.clock()
            loop_methods[method_name]()

            timer = time.clock() - timer

            if one_time:
                finished = "*DONE "
            else:
                finished = ""

            method_string = method_name

            time_string = "{}{}ms".format(finished, str(round(timer * 1000, 3)))
            self.debugger.debug_timer[method_name] = "{:<30}:{:>18}".format(method_string, time_string)

        else:
            print("not method called [{}] on game loop".format(method_name))





