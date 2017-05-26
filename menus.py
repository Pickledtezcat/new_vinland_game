import bge
import bgeutils
import mathutils
import game_audio
import user_interface

button_info = {"medium_button": {"size": (1.0, 0.5)},
               "screw_button": {"size": (2.0, 1.0)},
               "radio_button": {"size": (0.5, 0.5)},
               "option_button": {"size": (2.5, 0.5)},
               "large_button": {"size": (2.0, 1.0)},
               "text_box": {"size": (4.0, 1.0)},
               "undefined": {"size": (1.0, 0.5)},
               "display_text_box": {"size": (4.0, 1.0)}}

# Buttons


class TextCursor(object):
    def __init__(self, adder):
        self.adder = adder
        self.cursor = self.adder.scene.addObject("text_cursor", self.adder, 0)
        self.cursor.worldPosition.z += 0.1
        self.timer = 0.0
        self.visible = False

    def update(self):
        if self.visible:
            if self.timer < 4:
                self.cursor.visible = True
            else:
                self.cursor.visible = False

            if self.timer > 24:
                self.timer = 0

        else:
            self.cursor.visible = False

        self.timer += 1


class Button(object):
    is_text_box = False

    def __init__(self, widget, button_type, x_position, y_position, display_text, message, alt_message=None):
        self.widget = widget
        self.focus = False
        self.button_type = button_type
        self.on_mesh = "{}_on".format(self.button_type)
        self.off_mesh = "{}_off".format(self.button_type)
        self.button_object = self.widget.box.scene.addObject(self.off_mesh, self.widget.box, 0)
        self.button_object.worldPosition += mathutils.Vector([x_position, y_position, 0.10])
        self.button_object['owner'] = self
        self.text_object = bgeutils.get_ob("button_text", self.button_object.children)
        self.switch(False)

        self.button_width = button_info[button_type]["size"][0]
        self.text_width = max(1, int(self.button_width * 6))
        self.display_text = display_text
        self.text_object['Text'] = ""

        self.message = message
        self.alt_message = alt_message

        self.click = False
        self.alt_click = False
        self.clicked = False
        self.text_contents = ""
        self.recharge = 0
        self.text_cursor = None

        self.widget.buttons.append(self)

    def switch(self, on):
        if on:
            self.button_object.replaceMesh(self.on_mesh)
            self.text_object.color = [1.0, 1.0, 1.0, 1.0]
        else:
            self.button_object.replaceMesh(self.off_mesh)
            self.text_object.color = [0.0, 0.0, 0.01, 1.0]

    def set_display_text(self):

        display_text = self.display_text
        self.text_object['Text'] = bgeutils.split_in_lines(str(display_text), self.text_width, center=True)

    def update(self):
        self.set_display_text()

        if self.recharge == 0:
            if not self.clicked:
                if self.click:
                    bgeutils.sound_message("SOUND_EFFECT", ("SELECT_1", None, 0.3, 1.0))
                    self.click = False
                    self.clicked = True
            else:
                self.clicked = False
                self.recharge = 8
                self.switch(True)

        else:
            self.click = False
            if self.recharge == 1:
                self.switch(False)
                if self.message:
                    message = self.message
                    if self.alt_click:
                        message = self.alt_message
                        self.alt_click = False
                    if message:
                        self.widget.commands.append(message)
                self.recharge = 0
            else:
                self.recharge -= 1

    def end_button(self):
        self.button_object.endObject()


class TextButton(Button):
    is_text_box = True

    def __init__(self, widget, button_type, x_position, y_position, display_text, message, alt_message=None):
        super().__init__(widget, button_type, x_position, y_position, display_text, message, alt_message)

        self.text_cursor = TextCursor(self.button_object)
        self.text_cursor.visible = True

    def set_display_text(self):
        display_text = self.text_contents
        self.text_object['Text'] = bgeutils.split_in_lines(str(display_text), self.text_width, center=True)

    def keyboard_input(self):
        event_string = ""
        play_sound = False

        for event_key in bge.logic.keyboard.events:

            exclude = [130, 13, 160, 129]

            if event_key not in exclude:
                if event_key == 133:
                    event = bge.logic.keyboard.events[event_key]
                    if event == 1:
                        play_sound = True
                        self.text_contents = self.text_contents[:len(self.text_contents) - 1]

                elif event_key == 134:
                    event = bge.logic.keyboard.events[event_key]
                    if event == 1:
                        play_sound = True
                        self.text_contents = ""

                else:
                    event = bge.logic.keyboard.events[event_key]
                    shift_held = self.widget.shift_held
                    if event == 1:
                        play_sound = True
                        event_string = "{}{}".format(event_string, bge.events.EventToCharacter(event_key, shift_held))

        if play_sound:
            bgeutils.sound_message("SOUND_EFFECT", ("SELECT_2", None, 0.3, 1.0))

        self.text_contents = "{}{}".format(self.text_contents, event_string)
        self.text_contents = self.text_contents[:self.text_width]

    def update(self):
        self.set_display_text()
        self.text_cursor.update()

        if not self.focus:
            self.text_cursor.visible = False
            if self.click:
                bgeutils.sound_message("SOUND_EFFECT", ("SELECT_1", None, 0.3, 1.0))
                self.switch(True)
                self.click = False
                self.focus = True
        else:
            self.text_cursor.visible = True
            self.keyboard_input()
            if self.click:
                self.switch(False)
                self.click = False
                self.focus = False


class DisplayTextButton(Button):
    def __init__(self, widget, button_type, x_position, y_position, display_text, message, alt_message=None):
        super().__init__(widget, button_type, x_position, y_position, display_text, message, alt_message)
        self.switch(True)

    def set_display_text(self):
        display_text = self.widget.__dict__.get(self.display_text)
        self.text_object['Text'] = bgeutils.split_in_lines(str(display_text), self.text_width, center=True)

    def update(self):
        self.set_display_text()


# widgets


class Widget(object):
    header_text = ""
    text_width = 45

    def __init__(self, menu, adder):
        self.menu = menu
        self.adder = adder
        self.box = self.add_box()
        self.header_text_object = bgeutils.get_ob("button_text", self.box.children)
        self.header_text_object['Text'] = bgeutils.split_in_lines(self.header_text, self.text_width, center=True)
        self.commands = []
        self.buttons = []
        self.add_buttons()
        self.shift_held = False
        self.menu.widgets.append(self)

    def add_box(self):
        return self.adder.scene.addObject("default_widget", self.adder, 0)

    def defocus_buttons(self, exclude):

        for button in self.buttons:
            if button.is_text_box and button.focus and button != exclude:
                button.click = True

    def add_buttons(self):
        pass

    def update(self):
        for button in self.buttons:
            button.update()
        self.process_commands()

    def process_commands(self):
        for command in self.commands:
            if command.header == "EXIT":
                bge.logic.endGame()

            if command.header == "NEW_LEVEL":
                self.menu.new_level = command.content

        self.commands = []

    def end_widget(self):
        for button in self.buttons:
            button.end_button()

        self.box.endObject()


class StartWidget(Widget):
    header_text = "Start Menu"

    def add_buttons(self):
        button_size = button_info["large_button"]["size"]
        zero = 0.2
        spacing = button_size[1] + 0.1

        Button(self, "large_button", 0.0, zero + spacing, "Set\nProfile",
               bgeutils.GeneralMessage("NEW_LEVEL", "ProfileManagerMenu"))
        Button(self, "large_button", 0.0, zero, "Vehicle\nbuilder",
               bgeutils.GeneralMessage("NEW_LEVEL", "VehicleManagerMenu"))
        Button(self, "large_button", 0.0, zero - spacing, "Start\nGame", bgeutils.GeneralMessage("NEW_LEVEL", "Level"))
        Button(self, "large_button", 0.0, zero - (spacing * 2.0), "Exit", bgeutils.GeneralMessage("EXIT"))


class AddProfileWidget(Widget):
    header_text = "Add New Profile"

    def __init__(self, menu, adder):
        super().__init__(menu, adder)

        self.error_message = ""

    def add_buttons(self):

        button_size = button_info["large_button"]["size"]
        zero = 0.2
        spacing = button_size[1] + 0.1

        profile_name = TextButton(self, "text_box", 0.0, zero + spacing, "<<Enter name>>", None)
        Button(self, "large_button", 0.0, zero, "Add\nProfile", bgeutils.GeneralMessage("SAVE_PROFILE", profile_name))
        Button(self, "large_button", 0.0, zero - spacing, "Go\nBack", bgeutils.GeneralMessage("NEW_LEVEL", "StartMenu"))

    def process_commands(self):
        for command in self.commands:
            if command.header == "EXIT":
                bge.logic.endGame()

            if command.header == "NEW_LEVEL":
                self.menu.new_level = command.content

            if command.header == "SAVE_PROFILE":
                profile_name_button = command.content
                if profile_name_button.text_contents:
                    if profile_name_button.text_contents not in bge.logic.globalDict["profiles"]:
                        bgeutils.add_new_profile(profile_name_button.text_contents)
                        bgeutils.save_settings()

                        self.menu.new_level = "ProfileManagerMenu"

        self.commands = []


class LoadProfileWidget(Widget):
    header_text = "Load / Remove Profile\n(Right click to remove)"

    def __init__(self, menu, adder):
        super().__init__(menu, adder)

        self.active_profile = bge.logic.globalDict["active_profile"]

    def add_buttons(self):

        x_spacing, y_spacing = button_info["screw_button"]["size"]
        x_spacing += 0.1
        y_spacing += 0.1

        start_x = - 2.1
        start_y = 1.5
        profiles = bge.logic.globalDict["profiles"]

        x = 0
        y = 1

        DisplayTextButton(self, "display_text_box", 0.0, start_y, "active_profile", None)

        for profile in profiles:
            Button(self, "screw_button", start_x + (x_spacing * x), start_y + (y_spacing * -y), profile,
                   bgeutils.GeneralMessage("LOAD_PROFILE", profile),
                   alt_message=bgeutils.GeneralMessage("REMOVE_PROFILE", profile))

            if x > 1:
                y += 1
                x = 0
            else:
                x += 1

    def process_commands(self):
        for command in self.commands:
            if command.header == "EXIT":
                bge.logic.endGame()

            if command.header == "NEW_LEVEL":
                self.menu.new_level = command.content

            if command.header == "LOAD_PROFILE":
                bge.logic.globalDict["active_profile"] = command.content
                bgeutils.save_settings()
                self.menu.new_level = "ProfileManagerMenu"

            if command.header == "REMOVE_PROFILE":
                if command.content in bge.logic.globalDict["profiles"]:
                    if command.content == "Default Profile":
                        del (bge.logic.globalDict["profiles"][command.content])
                        bgeutils.add_new_profile("Default Profile")
                        bge.logic.globalDict["active_profile"] = "Default Profile"
                        bgeutils.save_settings()
                    else:
                        del (bge.logic.globalDict["profiles"][command.content])
                        bge.logic.globalDict["active_profile"] = [name for name in bge.logic.globalDict["profiles"]][0]
                        bgeutils.save_settings()

                    self.menu.new_level = "ProfileManagerMenu"

        self.commands = []


class ProfileDetails(Widget):
    def __init__(self, menu, adder):
        super().__init__(menu, adder)

        self.active_profile = "Player: {}".format(bge.logic.globalDict["active_profile"])
        profile = bge.logic.globalDict["profiles"][bge.logic.globalDict["active_profile"]]
        self.money = "Money: {}".format(profile["money"])
        self.faction = "Faction: {}".format(profile["faction"])
        self.game_turn = "Game Turn: {}".format(profile["game_turn"])

    def add_buttons(self):

        y = 2.0

        labels = ["active_profile", "money", "faction", "game_turn"]
        for label in labels:
            DisplayTextButton(self, "display_text_box", 0.0, y, label, None)
            y -= 1.0

        Button(self, "large_button", 0.0, y, "Go\nBack", bgeutils.GeneralMessage("NEW_LEVEL", "StartMenu"))


class VehicleName(Widget):
    klef = False


# menus

class Menu(object):

    def __init__(self, manager):
        print("MENU_MODE")
        self.manager = manager
        self.loaded = False
        self.loading = 0
        self.level_object = self.manager.scene.addObject("menu_background", self.manager.own, 0)
        self.scene = self.level_object.scene
        self.listener = self.manager.main_camera
        self.game_audio = game_audio.Audio(self)
        self.user_interface = user_interface.MenuInterface(self)

        widget_adders = bgeutils.get_ob_list("widget_adder", self.level_object.children)
        self.adders = sorted(widget_adders, key=lambda adder: adder.get("widget_adder"))
        self.widgets = []
        self.new_level = None

    def load(self):
        if self.loading >= 0:
            self.activate()
            self.loaded = True
        else:
            self.loading += 1

    def activate(self):
        pass

    def terminate(self):
        for widget in self.widgets:
            widget.end_widget()
        self.level_object.endObject()
        self.user_interface.terminate()

    def mouse_hit_ray(self, string):

        camera = self.manager.main_camera
        x, y = self.manager.game_input.virtual_mouse
        screen_vect = camera.getScreenVect(x, y)
        target_position = camera.worldPosition.copy() - screen_vect
        target_ray = camera.rayCast(target_position, camera, 180.0, string, 0, 1, 0)

        return target_ray

    def update(self):
        
        for message in bge.logic.globalDict["sounds"]:                        
            if message["header"] == "SOUND_EFFECT":
                sound, owner, attenuation, volume_scale = message["content"]
                if not owner:
                    owner = self.listener

                self.game_audio.sound_effect(sound, owner, attenuation=attenuation, volume_scale=volume_scale)

        bge.logic.globalDict["sounds"] = []

        self.game_audio.update()

        left_click = "left_button" in self.manager.game_input.buttons
        right_click = "right_button" in self.manager.game_input.buttons

        clicked = left_click or right_click

        if clicked:
            hit_ray = self.mouse_hit_ray("button")
            exclude = None

            if hit_ray[0]:
                hit_ray[0]['owner'].click = True
                if right_click:
                    hit_ray[0]['owner'].alt_click = True
                exclude = hit_ray[0]['owner']

            for widget in self.widgets:
                widget.defocus_buttons(exclude)

        shift_held = "shift" in self.manager.game_input.keys

        for widget in self.widgets:
            if shift_held:
                widget.shift_held = True
            else:
                widget.shift_held = False

            widget.update()

        self.user_interface.update()

        if self.new_level:
            bge.logic.globalDict["next_level"] = str(self.new_level)


class StartMenu(Menu):
    def activate(self):
        StartWidget(self, self.adders[0])


class ProfileManagerMenu(Menu):
    def activate(self):
        AddProfileWidget(self, self.adders[5])
        LoadProfileWidget(self, self.adders[2])


class VehicleManagerMenu(Menu):
    def activate(self):
        ProfileDetails(self, self.adders[1])
