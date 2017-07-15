import bge
import bgeutils
import mathutils
import game_audio
import user_interface
import vehicle_parts
import builder_tools
import random
import vehicle_stats
import model_display

parts_dict = vehicle_parts.get_vehicle_parts()

button_info = {"medium_button": {"size": (1.4, 0.7)},
               "screw_button": {"size": (2.0, 1.0)},
               "radio_button_yes": {"size": (1.7, 0.7)},
               "radio_button_no": {"size": (1.7, 0.7)},
               "option_button": {"size": (2.5, 0.5)},
               "large_button": {"size": (2.0, 1.0)},
               "square_button": {"size": (0.5, 1.0)},
               "text_box": {"size": (4.0, 1.0)},
               "undefined": {"size": (1.0, 0.5)},
               "contents_button":{"size": (6.5, 11.0)},
               "small_display_text_box": {"size": (3.0, 0.8)},
               "display_text_box": {"size": (4.0, 1.0)}}

color_dict = vehicle_parts.color_dict

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

    def __init__(self, widget, button_type, x_position, y_position, display_text, message, alt_message=None, color=None, help_text=""):
        self.widget = widget
        self.focus = False
        self.button_type = button_type
        self.on_mesh = "{}_on".format(self.button_type)
        self.off_mesh = "{}_off".format(self.button_type)
        self.button_object = self.widget.box.scene.addObject(self.off_mesh, self.widget.box, 0)
        self.button_object.worldPosition += mathutils.Vector([x_position, y_position, 0.10])
        if color:
            self.button_object.color = color
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
        self.click_location = None
        self.alt_click = False
        self.clicked = False
        self.text_contents = ""
        self.recharge = 0
        self.text_cursor = None
        self.help_text = help_text
        self.set_display_text()

        self.widget.buttons.append(self)

    def get_help_text(self, mouse_position):
        return self.help_text

    def switch(self, on):
        on_color = [1.0, 1.0, 1.0, 1.0]
        off_color = [0.0, 0.0, 0.01, 1.0]

        if self.button_type == "medium_button" or "radio" in self.button_type:
            on_color = [0.0, 0.0, 0.01, 1.0]
            off_color = [1.0, 1.0, 1.0, 1.0]

        if on:
            self.button_object.replaceMesh(self.on_mesh)
            self.text_object.color = on_color
        else:
            self.button_object.replaceMesh(self.off_mesh)
            self.text_object.color = off_color

    def set_display_text(self):
        display_text = self.display_text
        self.text_object['Text'] = bgeutils.split_in_lines(str(display_text), self.text_width, center=True)

    def update(self):
        self.set_display_text()

        if self.recharge == 0:
            if not self.clicked:
                if self.click:
                    sound_command = {"label": "SOUND_EFFECT", "content": ("SELECT_1", None, 0.3, 1.0)}
                    self.widget.menu.commands.append(sound_command)

                    self.click = False
                    self.click_location = None
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

    def __init__(self, widget, button_type, x_position, y_position, display_text, message, alt_message=None, color=None, help_text=""):
        super().__init__(widget, button_type, x_position, y_position, display_text, message, alt_message, color, help_text)

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
            sound_command = {"label": "SOUND_EFFECT", "content": ("SELECT_2", None, 0.3, 1.0)}
            self.widget.menu.commands.append(sound_command)

        self.text_contents = "{}{}".format(self.text_contents, event_string)
        self.text_contents = self.text_contents[:self.text_width]

    def update(self):
        self.set_display_text()
        self.text_cursor.update()

        if not self.focus:
            self.text_cursor.visible = False
            if self.click:
                sound_command = {"label": "SOUND_EFFECT", "content": ("SELECT_1", None, 0.3, 1.0)}
                self.widget.menu.commands.append(sound_command)

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
    def __init__(self, widget, button_type, x_position, y_position, display_text, message, alt_message=None, color=None, help_text=""):
        super().__init__(widget, button_type, x_position, y_position, display_text, message, alt_message, color, help_text)
        self.switch(True)

    def set_display_text(self):
        display_text = self.widget.__dict__.get(self.display_text)
        self.text_object['Text'] = bgeutils.split_in_lines(str(display_text), self.text_width, center=True)

    def update(self):
        self.set_display_text()


class ContentsButton(Button):
    def __init__(self, widget, button_type, x_position, y_position, display_text, message, alt_message=None, color=None, help_text=""):
        super().__init__(widget, button_type, x_position, y_position, display_text, message, alt_message, color,
                         help_text)

        self.tiles = []

        # TODO set text to show adding errors
        self.text_object["Text"] = "Right click to rotate."
        builder_tools.draw_base(self)
        builder_tools.draw_parts(self)

    def reset_button(self):
        for tile in self.tiles:
            tile.endObject()
        self.tiles = []

        builder_tools.draw_base(self)
        builder_tools.draw_parts(self)

    def get_help_text(self, mouse_position):
        location_key = builder_tools.get_location_key(self, mouse_position)
        self.widget.menu.manager.debugger.printer(location_key, label="key")

        editing = builder_tools.get_editing_vehicle()
        contents = editing["contents"]
        tile = contents.get(location_key)

        if tile:
            location = tile["location"]
            if location == "BLOCKED":
                return "Location blocked by turret."

            part_key = tile["part"]

            if part_key:
                part = parts_dict.get(part_key)
                if part:
                    name = part["name"].upper()
                    description = part["description"]
                    return "{}\n{}\n-----------\n{}".format(location.title(), name, description)

            return tile["location"].title()
        else:
            holding = bge.logic.globalDict["profiles"][bge.logic.globalDict["active_profile"]]["holding"]
            if holding:
                return "Right click to rotate. Left Click to drop held item back to inventory."

            return ""

    def update(self):
        self.set_display_text()

        if self.recharge == 0:
            if self.click:
                location = builder_tools.get_location_key(self, self.click_location)

                if self.alt_click:
                    message = bgeutils.GeneralMessage("REMOVE_CONTENTS", location)
                    self.widget.commands.append(message)
                else:
                    message = bgeutils.GeneralMessage("ADD_CONTENTS", location)
                    self.widget.commands.append(message)

                self.click = False
                self.alt_click = False
                self.recharge = 12
                self.click_location = None

        else:
            self.click = False
            self.alt_click = False
            self.click_location = None
            self.recharge -= 1

    def end_button(self):
        self.button_object.endObject()
        for tile in self.tiles:
            tile.endObject()
        self.tiles = []

# widgets


class Widget(object):
    header_text = ""
    header_formatted = True
    text_width = 45

    def __init__(self, menu, adder):
        self.menu = menu
        self.adder = adder
        self.box = self.add_box()
        self.header_text_object = bgeutils.get_ob("button_text", self.box.children)
        if self.header_formatted:
            self.header_text_object['Text'] = bgeutils.split_in_lines(self.header_text, self.text_width, center=True)
        else:
            self.header_text_object['Text'] = self.header_text
        self.commands = []
        self.buttons = []
        self.add_buttons()
        self.shift_held = False
        self.menu.widgets.append(self)

    def update_display(self):
        pass

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
                self.menu.manager.unload_white_canvas()
                bge.logic.endGame()

            if command.header == "NEW_LEVEL":
                # TODO unload white canvas when joining a game

                if command.content == "Level":
                    self.menu.manager.unload_white_canvas()

                self.menu.new_level = command.content

        self.commands = []

    def end_widget(self):
        for button in self.buttons:
            button.end_button()

        self.box.endObject()


class NarrowWidget(Widget):
    text_width = 18

    def add_box(self):
        return self.adder.scene.addObject("narrow_widget", self.adder, 0)


class StartWidget(NarrowWidget):
    header_text = "Start Menu"

    def add_buttons(self):
        button_size = button_info["large_button"]["size"]
        zero = 0.5
        spacing = button_size[1] + 0.1

        Button(self, "large_button", 0.0, zero + spacing, "Set\nProfile",
               bgeutils.GeneralMessage("NEW_LEVEL", "ProfileManagerMenu"))
        Button(self, "large_button", 0.0, zero, "Manage\nVehicles",
               bgeutils.GeneralMessage("NEW_LEVEL", "VehicleManagerMenu"))
        Button(self, "large_button", 0.0, zero - spacing, "Start\nGame", bgeutils.GeneralMessage("NEW_LEVEL", "Level"))
        Button(self, "large_button", 0.0, zero - (spacing * 2.0), "Exit", bgeutils.GeneralMessage("EXIT"), color=color_dict["cancel"])


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
        Button(self, "large_button", 0.0, zero - spacing, "Go\nBack", bgeutils.GeneralMessage("NEW_LEVEL", "StartMenu"), color=color_dict["cancel"])

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

        Button(self, "large_button", 0.0, y, "Go\nBack", bgeutils.GeneralMessage("NEW_LEVEL", "StartMenu"), color=color_dict["cancel"])


class VehicleOptionsSettingWidget(Widget):
    header_text = "Set vehicle options"

    def __init__(self, menu, adder):
        super().__init__(menu, adder)

        self.vehicle_name = self.get_vehicle_name()

    def get_vehicle_name(self):
        current_vehicle = builder_tools.get_editing_vehicle()
        return current_vehicle['name']

    def add_buttons(self):
        button_size = button_info["large_button"]["size"]
        zero = 0.2
        spacing = button_size[1] + 0.1

        Button(self, "large_button", 0.0, zero - (spacing * 2.0), "Go\nback", bgeutils.GeneralMessage("NEW_LEVEL", "VehicleManagerMenu"), color=color_dict["cancel"])
        current_vehicle = builder_tools.get_editing_vehicle()

        DisplayTextButton(self, "display_text_box", 0.0, zero + spacing, "vehicle_name", None)

        vehicle_name = TextButton(self, "text_box", 0.0, zero, current_vehicle["name"], None, help_text="Enter new name here.")
        Button(self, "large_button", 0.0, zero - spacing, "Rename\nVehicle",
               bgeutils.GeneralMessage("RENAME_VEHICLE", vehicle_name))

    def process_commands(self):
        self.vehicle_name = self.get_vehicle_name()

        for command in self.commands:
            if command.header == "NEW_LEVEL":
                self.menu.new_level = command.content

            if command.header == "RENAME_VEHICLE":
                vehicle_name_button = command.content
                if vehicle_name_button.text_contents:

                    editing_vehicle = builder_tools.get_editing_vehicle()
                    editing_vehicle['name'] = vehicle_name_button.text_contents
                    builder_tools.write_editing_vehicle(editing_vehicle)

        self.commands = []


class VehicleOptionsWidget(Widget):
    def __init__(self, menu, adder):
        super().__init__(menu, adder)

    def add_buttons(self):

        max_y = 2.0
        min_y = -2.0

        x = -2.7
        y = max_y
        x_spacing, y_spacing = button_info["radio_button_yes"]["size"]

        profile = bge.logic.globalDict["profiles"][bge.logic.globalDict["active_profile"]]
        vehicles = profile["vehicles"]
        current_vehicle = vehicles[profile["editing"]]

        vehicle_options = current_vehicle["options"]
        options = vehicle_parts.get_design_rules()
        for option_set in vehicle_options:
            option_key = option_set[0]
            option = options[option_key]

            setting = "no"
            if option_set[1]:
                setting = "yes"

            name = option["name"]

            Button(self, "radio_button_{}".format(setting), x, y, name, bgeutils.GeneralMessage("TOGGLE_OPTION", option_key), help_text=option["description"])

            if y > min_y:
                y -= y_spacing
            else:
                y = max_y
                x += 2

    def set_toggle_option(self, toggle_key):

        profile = bge.logic.globalDict["profiles"][bge.logic.globalDict["active_profile"]]
        vehicles = profile["vehicles"]
        current_vehicle = vehicles[profile["editing"]]
        vehicle_options = current_vehicle["options"]
        options = vehicle_parts.get_design_rules()

        for o in range(len(vehicle_options)):
            option_set = vehicle_options[o]
            option_key = option_set[0]
            if toggle_key == option_key:
                toggle_option = options[option_key]
                setting = option_set[1]
                toggle_type = toggle_option["option_type"]

                if not setting:
                    if toggle_type:
                        for i in range(len(vehicle_options)):
                            other_option_set = vehicle_options[i]
                            other_option_key = other_option_set[0]
                            other_option = options[other_option_key]

                            if other_option["option_type"] == toggle_type:
                                current_vehicle["options"][i][1] = False

                current_vehicle["options"][o][1] = not setting
                current_vehicle["contents"] = {}

        builder_tools.write_editing_vehicle(current_vehicle)

    def process_commands(self):
        for command in self.commands:
            if command.header == "TOGGLE_OPTION":
                toggle_key = command.content
                self.set_toggle_option(toggle_key)
                self.menu.new_level = "VehicleOptionMenu"

        self.commands = []


class VehicleSizeWidget(Widget):
    def __init__(self, menu, adder):
        super().__init__(menu, adder)

        self.chassis_dict = vehicle_parts.chassis_dict
        self.chassis_size = self.get_chassis_size()
        self.turret_dict = vehicle_parts.turret_dict
        self.turret_size = self.get_turret_size()

    def get_chassis_size(self):
        current_vehicle = builder_tools.get_editing_vehicle()
        chassis_size = current_vehicle['chassis']
        return self.chassis_dict[chassis_size]["name"].upper().replace("_", " ")

    def get_turret_size(self):
        current_vehicle = builder_tools.get_editing_vehicle()
        turret_size = current_vehicle['turret']
        return self.turret_dict[turret_size]["name"].upper().replace("_", " ")

    def add_buttons(self):

        button_size = button_info["square_button"]["size"]
        zero = 1.8
        spacing = button_size[1] + 0.2

        left = -1.0
        right = 1.0
        center = 0.0

        DisplayTextButton(self, "display_text_box", center, zero, "chassis_size", None)
        Button(self, "square_button", left, zero - spacing, "<<", bgeutils.GeneralMessage("CHASSIS_SIZE", -1))
        Button(self, "square_button", right, zero - spacing, ">>", bgeutils.GeneralMessage("CHASSIS_SIZE", 1))

        DisplayTextButton(self, "display_text_box", center, zero - (spacing * 2.0), "turret_size", None)
        Button(self, "square_button", left, zero - (spacing * 3.0), "<<", bgeutils.GeneralMessage("TURRET_SIZE", -1))
        Button(self, "square_button", right, zero - (spacing * 3.0), ">>", bgeutils.GeneralMessage("TURRET_SIZE", 1))

    def process_commands(self):
        self.chassis_size = self.get_chassis_size()
        self.turret_size = self.get_turret_size()

        for command in self.commands:
            if command.header == "EXIT":
                bge.logic.endGame()

            if command.header == "CHASSIS_SIZE":
                current_vehicle = builder_tools.get_editing_vehicle()
                change = command.content
                current_vehicle["chassis"] = min(4, max(1, current_vehicle["chassis"] + change))
                max_turret_size = current_vehicle["chassis"] + 1
                current_vehicle["turret"] = min(current_vehicle["turret"], max_turret_size)
                current_vehicle["contents"] = {}

            if command.header == "TURRET_SIZE":
                current_vehicle = builder_tools.get_editing_vehicle()
                change = command.content
                max_turret_size = current_vehicle["chassis"] + 1
                current_vehicle["turret"] = min(max_turret_size, max(0, current_vehicle["turret"] + change))
                current_vehicle["contents"] = {}

        self.commands = []


class VehicleManagerSettingsWidget(Widget):
    header_text = "Add / Remove vehicles\n(Right click to remove)"

    def add_buttons(self):
        button_size = button_info["large_button"]["size"]
        zero = 0.2
        spacing = button_size[1] + 0.1

        Button(self, "large_button", 0.0, zero + spacing, "Add\nnew\nvehicle", bgeutils.GeneralMessage("ADD_VEHICLE", None), help_text="Add a new vehicle type.")
        Button(self, "large_button", 0.0, zero, "Go\nback", bgeutils.GeneralMessage("NEW_LEVEL", "StartMenu"), color=color_dict["cancel"])

    def process_commands(self):
        for command in self.commands:
            if command.header == "EXIT":
                bge.logic.endGame()

            if command.header == "NEW_LEVEL":
                self.menu.new_level = command.content

            if command.header == "RENAME_VEHICLE":
                vehicle_name = command.content
                editing_vehicle = builder_tools.get_editing_vehicle()
                editing_vehicle['name'] = vehicle_name
                builder_tools.write_editing_vehicle(editing_vehicle)

            if command.header == "ADD_VEHICLE":
                vehicle = builder_tools.build_base_vehicle()

                builder_tools.add_new_vehicle(vehicle)
                self.menu.new_level = "VehicleManagerMenu"

        self.commands = []


class VehicleManagerWidget(Widget):
    def __init__(self, menu, adder):
        super().__init__(menu, adder)

    def add_buttons(self):
        max_y = 1.8
        min_y = -1.8

        x = -2.0
        y = max_y
        x_spacing, y_spacing = button_info["screw_button"]["size"]

        vehicle_keys = [v_key for v_key in bge.logic.globalDict["profiles"][bge.logic.globalDict["active_profile"]]["vehicles"]]
        for vehicle_key in vehicle_keys:
            vehicle = bge.logic.globalDict["profiles"][bge.logic.globalDict["active_profile"]]["vehicles"][vehicle_key]
            vehicle_name = vehicle["name"]

            Button(self, "screw_button", x, y, vehicle_name, bgeutils.GeneralMessage("EDIT_VEHICLE", vehicle_key), alt_message=bgeutils.GeneralMessage("REMOVE_VEHICLE", vehicle_key), help_text="Left click to edit, right click to delete.")

            if y > min_y:
                y -= y_spacing
            else:
                y = max_y
                x += 2

    def process_commands(self):
        for command in self.commands:
            if command.header == "NEW_LEVEL":
                self.menu.new_level = command.content

            if command.header == "REMOVE_VEHICLE":
                remove_vehicle_id = command.content
                if remove_vehicle_id in bge.logic.globalDict["profiles"][bge.logic.globalDict["active_profile"]]["vehicles"]:
                    del bge.logic.globalDict["profiles"][bge.logic.globalDict["active_profile"]]["vehicles"][remove_vehicle_id]
                self.menu.new_level = "VehicleManagerMenu"

            if command.header == "EDIT_VEHICLE":
                edit_vehicle_id = command.content
                bge.logic.globalDict["profiles"][bge.logic.globalDict["active_profile"]]["editing"] = edit_vehicle_id
                self.menu.new_level = "VehicleOptionMenu"

        self.commands = []


class VehicleGoToContentsWidget(NarrowWidget):
    header_text = "Modify vehicle contents"

    def __init__(self, menu, adder):
        super().__init__(menu, adder)

    def add_buttons(self):
        Button(self, "large_button", 0.0, 1.0, "Modify\nContents", bgeutils.GeneralMessage("NEW_LEVEL", "VehicleContentsMenu"))
        Button(self, "large_button", 0.0, 0.0, "Save\nTo\nDisk", bgeutils.GeneralMessage("SAVE_VEHICLE", ""))

    def process_commands(self):
        for command in self.commands:
            if command.header == "NEW_LEVEL":
                self.menu.new_level = command.content
                bge.logic.globalDict["profiles"][bge.logic.globalDict["active_profile"]][
                    "part_filter"] = "weapon"
                bge.logic.globalDict["profiles"][bge.logic.globalDict["active_profile"]]["part_page"] = 0

            if command.header == "SAVE_VEHICLE":
                builder_tools.save_testing_vehicle()

        self.commands = []


class VehicleContentsSettingsWidget(Widget):
    header_text = "Select contents filter"

    def __init__(self, menu, adder):
        super().__init__(menu, adder)

    def add_buttons(self):
        zero = 1.8

        x_spacing, y_spacing = button_info["radio_button_yes"]["size"]

        y = 0

        types = ["weapon", "armor", "engine", "crew", "drive", "utility"]

        for part_type in types:
            part_filter = bge.logic.globalDict["profiles"][bge.logic.globalDict["active_profile"]]["part_filter"]

            if part_type != part_filter:
                setting = "no"
            else:
                setting = "yes"

            Button(self, "radio_button_{}".format(setting), 0.0, zero - (y * (y_spacing + 0.1)), part_type,
                   bgeutils.GeneralMessage("SWITCH_PART_TYPE", part_type), color=color_dict[part_type])

            y += 1

        Button(self, "large_button", - 1.8, zero - 0.2, "Go\nback", bgeutils.GeneralMessage("NEW_LEVEL", "VehicleOptionMenu"), color=color_dict["cancel"])

    def process_commands(self):
        for command in self.commands:
            if command.header == "NEW_LEVEL":
                builder_tools.replace_holding_part()
                self.menu.new_level = command.content

            if command.header == "SWITCH_PART_TYPE":
                bge.logic.globalDict["profiles"][bge.logic.globalDict["active_profile"]]["part_filter"] = command.content
                bge.logic.globalDict["profiles"][bge.logic.globalDict["active_profile"]]["part_page"] = 0
                self.menu.new_level = "VehicleContentsMenu"

        self.commands = []


class InventoryWidget(Widget):
    def __init__(self, menu, adder):
        self.max_page = 0
        self.page = self.get_page()
        super().__init__(menu, adder)

    def get_page(self):
        page = bge.logic.globalDict["profiles"][bge.logic.globalDict["active_profile"]]["part_page"]
        return "PAGE {}/{}".format(page + 1, self.max_page + 1)

    def add_buttons(self):

        max_y = 2.2
        min_y = -0.6

        x = -2.2
        y = max_y
        x_spacing, y_spacing = button_info["medium_button"]["size"]

        part_filter = bge.logic.globalDict["profiles"][bge.logic.globalDict["active_profile"]]["part_filter"]
        inventory = bge.logic.globalDict["profiles"][bge.logic.globalDict["active_profile"]]["inventory"]
        page = bge.logic.globalDict["profiles"][bge.logic.globalDict["active_profile"]]["part_page"]
        filtered_parts = [p for p in inventory if p[2] == part_filter.upper()]

        inventory = sorted(filtered_parts, key=lambda entry: entry[1])
        self.max_page = max(1, int(len(inventory) / 24.0) - 0)

        if len(inventory) > 0:

            for i in range(24):
                inventory_index = i + (page * 24)

                if inventory_index < len(inventory):
                    part_group = inventory[inventory_index]
                    part_key = part_group[0]
                    part = parts_dict[part_key]
                    name = part["name"].upper()
                    description = part["description"]
                    help_text = "{}\n{}".format(name, description)

                    part_name = part["name"]

                    Button(self, "medium_button", x, y, part_name,
                           bgeutils.GeneralMessage("PICK_PART", part_key), color=color_dict[part_filter], help_text=help_text)

                    if y > min_y:
                        y -= y_spacing
                    else:
                        y = max_y
                        x += x_spacing + 0.1

        if page != self.max_page:
            Button(self, "square_button", 2.0, -2.0, ">",
                   bgeutils.GeneralMessage("SET_PAGE", page + 1))
            Button(self, "square_button", 2.5, -2.0, ">>",
                   bgeutils.GeneralMessage("SET_PAGE", self.max_page))

        DisplayTextButton(self, "small_display_text_box", 0, -2, "page", None)

        if page > 0:
            Button(self, "square_button", -2.0, -2.0, "<",
                   bgeutils.GeneralMessage("SET_PAGE", page - 1))
            Button(self, "square_button", -2.5, -2.0, "<<",
                   bgeutils.GeneralMessage("SET_PAGE", 0))

    def process_commands(self):
        self.page = self.get_page()
        reboot = False

        for command in self.commands:
            if command.header == "SET_PAGE":
                bge.logic.globalDict["profiles"][bge.logic.globalDict["active_profile"]][
                    "part_page"] = command.content
                self.menu.new_level = "VehicleContentsMenu"

            if command.header == "PICK_PART":
                if bge.logic.globalDict["profiles"][bge.logic.globalDict["active_profile"]]["holding"]:
                    builder_tools.replace_holding_part()
                    reboot = True

                new_inventory = []
                part_key = command.content
                removed = False
                inventory = bge.logic.globalDict["profiles"][bge.logic.globalDict["active_profile"]]["inventory"]
                for part_group in inventory:
                    if part_group[0] == part_key and not removed:
                        removed = True
                    else:
                        new_inventory.append(part_group)

                bge.logic.globalDict["profiles"][bge.logic.globalDict["active_profile"]]["holding"] = part_key
                bge.logic.globalDict["profiles"][bge.logic.globalDict["active_profile"]]["inventory"] = new_inventory
                self.menu.new_level = "VehicleContentsMenu"

        self.commands = []
        if reboot:
            self.menu.reboot_widget(InventoryWidget)


class VehicleContentsWidget(Widget):

    def __init__(self, menu, adder):
        self.button = None
        editing = builder_tools.get_editing_vehicle()
        if not editing["contents"]:
            builder_tools.create_vehicle_layout()

        super().__init__(menu, adder)
        self.box.visible = False

    def add_buttons(self):
        # TODO add a contents layout button

        self.button = ContentsButton(self, "contents_button", 0, 0, "", None, None)

    def process_commands(self):

        for command in self.commands:
            if command.header == "ADD_CONTENTS":
                placement = builder_tools.check_adding_part(command.content)
                self.button.display_text = placement
                if placement == "Part Placed.":

                    sound_command = {"label": "SOUND_EFFECT", "content": ("SELECT_1", None, 0.3, 1.0)}
                    self.menu.commands.append(sound_command)
                    placed = builder_tools.place_part(command.content)
                    # TODO add particle effect for removing items using placed

                    self.button.reset_button()
                    self.menu.reboot_widget(StatDisplayWidget)

                else:
                    builder_tools.replace_holding_part()
                    self.menu.reboot_widget(InventoryWidget)
                    sound_command = {"label": "SOUND_EFFECT", "content": ("SELECT_2", None, 0.3, 1.0)}
                    self.menu.commands.append(sound_command)

            if command.header == "REMOVE_CONTENTS":

                removed = builder_tools.remove_part(command.content)
                if removed:
                    sound_command = {"label": "SOUND_EFFECT", "content": ("SELECT_2", None, 0.3, 1.0)}
                    self.menu.commands.append(sound_command)
                    self.button.display_text = removed[0]
                    # TODO add particle effect for removing items using removed[1]
                    self.button.reset_button()
                    self.menu.reboot_widget(InventoryWidget)
                    self.menu.reboot_widget(StatDisplayWidget)
                else:
                    bgeutils.rotate_holding()

        self.commands = []


class StatDisplayWidget(Widget):

    def __init__(self, menu, adder):
        editing = builder_tools.get_editing_vehicle()
        self.stats = vehicle_stats.VehicleStats(editing)
        stats, help_text = builder_tools.display_stats(self.stats)
        self.header_formatted = False
        self.header_text = stats

        super().__init__(menu, adder)
        self.model = model_display.VehicleModel(self.menu.adders[7], self, 0.5)

    def end_widget(self):
        for button in self.buttons:
            button.end_button()

        self.box.endObject()
        self.model.end_vehicle()

    def update_display(self):
        self.model.preview_update()

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
        self.tool_tip_text = ""
        self.user_interface = user_interface.MenuInterface(self)
        self.commands = []
        self.white_canvas = None

        widget_adders = bgeutils.get_ob_list("widget_adder", self.level_object.children)
        self.adders = sorted(widget_adders, key=lambda adder: adder.get("widget_adder"))
        self.widgets = []
        self.new_level = None

        self.assets = []
        self.loading_progress = 0

        if not self.manager.assets_loaded:
            vehicle_path = bge.logic.expandPath("//models/vehicles.blend")
            self.assets.append(bge.logic.LibLoad(vehicle_path, "Scene", async=True))
            self.manager.assets_loaded = True

        self.holding_part = None

    def check_loaded(self):

        loaded = True

        for asset in self.assets:
            if not asset.finished:
                loaded = False

        self.loading_progress += 1
        return loaded

    def set_white_canvas(self):
        texture = "vin_vehicles_texture"
        texture_object = self.scene.addObject(texture, self.manager.own, 0)
        texture_object.worldPosition.y += 120
        material_id = bge.texture.materialID(texture_object, "MAvin_vehicles_texture_mat")

        self.manager.white_canvas = bge.texture.Texture(texture_object, material_id)
        path = bge.logic.expandPath("//textures//white_canvas.png")
        tex = bge.texture.ImageFFmpeg(path)

        self.manager.white_canvas.source = tex
        self.manager.white_canvas.refresh(False)

    def load(self):
        if self.check_loaded():
            self.set_white_canvas()
            self.activate()
            self.loaded = True
        else:
            self.tool_tip_text = "LOADING ({})".format(self.loading_progress)
            self.user_interface.update()

    def activate(self):
        pass

    def terminate(self):
        for widget in self.widgets:
            widget.end_widget()
        self.level_object.endObject()
        self.user_interface.terminate()

    def reboot_widget(self, widget_name):

        new_widgets = []
        adder = None

        for widget in self.widgets:
            if not isinstance(widget, widget_name):
                new_widgets.append(widget)
            else:
                adder = widget.adder
                widget.end_widget()

        if adder:
            self.widgets = new_widgets
            widget_name(self, adder)

    def mouse_hit_ray(self, string):

        camera = self.manager.main_camera
        x, y = self.manager.game_input.virtual_mouse
        screen_vect = camera.getScreenVect(x, y)
        target_position = camera.worldPosition.copy() - screen_vect
        target_ray = camera.rayCast(target_position, camera, 180.0, string, 0, 1, 0)

        return target_ray

    def update(self):
        #self.manager.white_canvas.refresh(False)

        for widget in self.widgets:
            widget.update_display()

        self.manager.debugger.printer(type(self).__name__, "menu mode: ")

        for command in self.commands:
            if command["label"] == "SOUND_EFFECT":
                sound, owner, attenuation, volume_scale = command["content"]
                if not owner:
                    owner = self.listener

                self.game_audio.sound_effect(sound, owner, attenuation=attenuation, volume_scale=volume_scale)

        self.commands = []

        self.game_audio.update()

        hit_ray = self.mouse_hit_ray("button")
        help_text = ""

        if hit_ray[0]:

            shift_held = "shift" in self.manager.game_input.keys

            for widget in self.widgets:
                if shift_held:
                    widget.shift_held = True
                else:
                    widget.shift_held = False

                widget.update()

            left_click = "left_button" in self.manager.game_input.buttons
            right_click = "right_button" in self.manager.game_input.buttons

            clicked = left_click or right_click

            owner = hit_ray[0]["owner"]
            hit_position = hit_ray[1].copy()

            help_text = owner.get_help_text(hit_position.copy())

            if clicked:
                owner.click_location = hit_position.copy()
                owner.click = True
                if right_click:
                    owner.alt_click = True

                for widget in self.widgets:
                    widget.defocus_buttons(owner)

        self.tool_tip_text = help_text
        self.user_interface.update()

        if self.new_level:
            bge.logic.globalDict["next_level"] = str(self.new_level)


class StartMenu(Menu):
    def __init__(self, manager):
        super().__init__(manager)

    def activate(self):
        StartWidget(self, self.adders[0])


class ProfileManagerMenu(Menu):
    def activate(self):
        AddProfileWidget(self, self.adders[5])
        LoadProfileWidget(self, self.adders[2])


class VehicleManagerMenu(Menu):
    def __init__(self, manager):
        super().__init__(manager)

        # TODO make sure this happens every time you leave the vehicle contents / options editor

        bge.logic.globalDict["profiles"][bge.logic.globalDict["active_profile"]]["editing"] = None
        bge.logic.globalDict["profiles"][bge.logic.globalDict["active_profile"]]["part_page"] = 0

    def activate(self):
        VehicleManagerWidget(self, self.adders[5])
        VehicleManagerSettingsWidget(self, self.adders[2])


class VehicleOptionMenu(Menu):
    def activate(self):
        VehicleOptionsWidget(self, self.adders[3])
        VehicleOptionsSettingWidget(self, self.adders[1])
        VehicleSizeWidget(self, self.adders[2])
        VehicleGoToContentsWidget(self, self.adders[5])


class VehicleContentsMenu(Menu):

    def activate(self):
        VehicleContentsSettingsWidget(self, self.adders[1])
        InventoryWidget(self, self.adders[3])
        VehicleContentsWidget(self, self.adders[0])
        StatDisplayWidget(self, self.adders[4])

