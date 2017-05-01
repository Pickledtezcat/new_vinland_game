import bge
import camera_control
import game_input
import levels
import bgeutils
import time


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

        if "control" in self.manager.game_input.keys:
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

        self.cont = cont
        self.own = cont.owner
        self.scene = self.own.scene
        self.main_camera = self.scene.active_camera
        self.debugger = DebugPrinter(self)

        self.camera = camera_control.CameraControl(self)
        self.game_input = game_input.GameInput()
        self.next_level = None
        self.level = None

        self.profile("set_level", one_time=True)

    def update(self):
        self.profile("input_update")
        self.profile("camera_update")
        self.profile("debugger_update")
        self.profile("level_update")

    def input_update(self):
        self.game_input.update()

    def camera_update(self):
        self.camera.update()

    def debugger_update(self):
        self.debugger.update()

    def set_level(self):
        if self.level:
            self.level.terminate()

        self.level = levels.Level(self)
        self.next_level = None

    def level_update(self):

        if "save" in self.game_input.keys:
            self.next_level = True

        if self.next_level:
            self.profile("set_level", one_time=True)
        else:
            self.level.update()

    def profile(self, method_name, one_time=False):

        loop_methods = {"debugger_update": self.debugger_update,
                        "camera_update": self.camera_update,
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





