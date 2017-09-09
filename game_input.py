import bge


def get_keyboard_inputs():
    saved_keys = bge.logic.globalDict.get("keys")

    if saved_keys:
        default_keys = saved_keys
    else:
        default_keys = {"escape": (130, "escape_key", 1),
                        "shift": (129, "LEFTSHIFTKEY", 0),
                        "control": (124, "LEFTCNTRTKEY", 0),
                        "alt": (125, "LEFTALTTKEY", 0),
                        "save": (162, "f1", 1),
                        "pause": (32, "SPACEKEY", 1),
                        "info": (105, "i_key", 0),
                        "exit_vehicle": (122, "z_key", 1),
                        "1": (49, "1", 1),
                        "2": (50, "2", 1),
                        "3": (51, "3", 1),
                        "4": (52, "4", 1),
                        "5": (53, "5", 1),
                        "6": (54, "6", 1),
                        "7": (55, "7", 1),
                        "8": (56, "8", 1),
                        "9": (57, "9", 1),
                        "r": (114, "r", 0),
                        "w": (119, "w", 0),
                        "d": (100, "d", 0),
                        "s": (115, "s", 0),
                        "a": (97, "a", 0),
                        "f": (102, "f", 0)}

        default_keysx = {"escape": (130, "escape_key", 1),
                        "space": (32, "SPACEKEY", 1),
                        "control": (124, "LEFTCNTRTKEY", 0),
                        "shift": (129, "LEFTSHIFTKEY", 0),
                        "alt": (125, "LEFTALTTKEY", 0),
                        "pause": (112, "PKEY", 1),
                        "-": (159, "PADMINUS", 1),
                        "+": (161, "PADPLUSKEY", 1),
                        "w": (119, "w", 0),
                        "d": (100, "d", 0),
                        "s": (115, "s", 0),
                        "a": (97, "a", 0),
                        "r": (114, "r", 1),
                        "x": (120, "x", 1),
                        "cam_up": (146, "up", 1),
                        "cam_right": (145, "right", 1),
                        "cam_down": (144, "down", 1),
                        "cam_left": (143, "left", 1),
                        "c": (99, "c_key", 1),
                        "i": (105, "i_key", 1),
                        "pad1": (151, "pad1", 0),
                        "pad2": (147, "pad2", 0),
                        "pad3": (152, "pad3", 0),
                        "pad4": (148, "pad4", 0),
                        "pad5": (153, "pad5", 0),
                        "pad6": (149, "pad6", 0),
                        "pad7": (154, "pad7", 0),
                        "pad8": (150, "pad8", 0),
                        "pad9": (155, "pad9", 0),
                        "1": (49, "1", 1),
                        "2": (50, "2", 1),
                        "3": (51, "3", 1),
                        "m": (109, "m", 1),
                        "save": (162, "f1", 1)}

        bge.logic.globalDict["keys"] = default_keys

    return default_keys


def mouse_triggered(button, tap=False):
    mouse = bge.logic.mouse

    if tap:
        triggered = [1]
    else:
        triggered = [1, 2]

    if mouse.events[button] in triggered:
        return True


def key_triggered(key, tap=False):
    if tap:
        triggered = [1]
    else:
        triggered = [1, 2]

    if bge.logic.keyboard.events[key] in triggered:
        return True


class GameInput(object):
    def __init__(self):

        self.virtual_mouse = [0.5, 0.5]
        self.last_position = bge.logic.mouse.position
        bge.logic.mouse.position = (0.5, 0.5)
        self.sensitivity = bge.logic.globalDict.get("sensitivity", 0.95)
        self.keys = []
        self.buttons = []
        self.keyboard = get_keyboard_inputs()
        self.mouse_actions = {"left_button": (bge.events.LEFTMOUSE, True),
                              "left_drag": (bge.events.LEFTMOUSE, False),
                              "right_drag": (bge.events.RIGHTMOUSE, False),
                              "right_button": (bge.events.RIGHTMOUSE, True),
                              "middle_button": (bge.events.MIDDLEMOUSE, True),
                              "wheel_up": (bge.events.WHEELUPMOUSE, False),
                              "wheel_down": (bge.events.WHEELDOWNMOUSE, False)}

    def update(self):

        active_keys = []
        active_buttons = []

        for key_key in self.keyboard:
            key_data = self.keyboard[key_key]

            check_key_triggered = key_triggered(key_data[0], tap=key_data[2])
            if check_key_triggered:
                active_keys.append(key_key)

        for mouse_key in self.mouse_actions:
            mouse_data = self.mouse_actions[mouse_key]

            check_button_triggered = mouse_triggered(mouse_data[0], tap=mouse_data[1])
            if check_button_triggered:
                active_buttons.append(mouse_key)

        self.keys = active_keys
        self.buttons = active_buttons
        self.set_virtual_mouse()

    def set_virtual_mouse(self):

        x, y = bge.logic.mouse.position

        if bge.logic.mouse.position != (0.5, 0.5) or bge.logic.mouse.position != self.last_position:
            bge.logic.mouse.position = (0.5, 0.5)

        self.last_position = bge.logic.mouse.position

        x_dif = (0.5 - x) * self.sensitivity
        y_dif = (0.5 - y) * self.sensitivity

        if abs(x_dif) < 0.001:
            x_dif = 0.0
        if abs(y_dif) < 0.001:
            y_dif = 0.0

        self.virtual_mouse[0] = max(0.0, min(1.0, self.virtual_mouse[0] - x_dif))
        self.virtual_mouse[1] = max(0.0, min(1.0, self.virtual_mouse[1] - y_dif))




