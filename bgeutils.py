import bge
import mathutils
import json
import vehicle_parts

vinland_version = "0.1"


class GeneralMessage(object):
    def __init__(self, header, content=None):
        self.header = header
        self.content = content


def get_key(position):
    return "{}${}".format(int(round(position[0])), int(round(position[1])))


def get_loc(key):
    return [int(v) for v in key.split("$")]


def position_to_location(position):
    return [int(round(v)) for v in position][:2]


def smoothstep(x):
    return x * x * (3 - 2 * x)


def get_distance(a, b):
    vector = mathutils.Vector(b).to_3d() - mathutils.Vector(a).to_3d()
    return vector.length


def get_ob(string, ob_list):
    ob_list = [ob for ob in ob_list if string in ob]
    if ob_list:
        return ob_list[0]


def get_ob_list(string, ob_list):
    ob_list = [ob for ob in ob_list if string in ob]

    return ob_list


def interpolate_float(current, target, factor):

    return (current * (1.0 - factor)) + (target * factor)


def diagonal(location):
    x, y = location
    if abs(x) - abs(y) == 0:
        return True


def split_in_lines(contents, line_length, center=False):

    new_lines = []

    split_lines = contents.splitlines()

    for line in split_lines:
        words = line.split()

        new_line = []
        lines = []
        letters = 0

        for word in words:
            letters += len(word)

            if letters < line_length:
                new_line.append(word)
            else:
                lines.append(" ".join(new_line))
                new_line = [word]
                letters = len(word)

        if new_line:
            lines.append(" ".join(new_line))

        lines = [line for line in lines if line != ""]

        if center:
            lines = ["{:^{length}}".format(line, length=line_length) for line in lines]

        if lines:
            if len(lines) > 1:
                new_contents = "\n".join(lines)
            else:
                new_contents = lines[0]

            new_lines.append(new_contents)

    if not new_lines:
        return ""
    elif len(new_lines) > 1:
        return "\n".join(new_lines)
    else:
        return new_lines[0]


def save_level(level):
    save_name = "level_{}".format(bge.logic.globalDict["active_profile"])
    bge.logic.globalDict["profiles"][bge.logic.globalDict["active_profile"]]["saved_game"] = save_name

    out_path = bge.logic.expandPath("//saves/{}.txt".format(save_name))
    with open(out_path, "w") as outfile:
        json.dump(level, outfile)


def load_level():
    load_name = bge.logic.globalDict["profiles"][bge.logic.globalDict["active_profile"]]["saved_game"]
    in_path = bge.logic.expandPath("//saves/{}.txt".format(load_name))
    with open(in_path, "r") as infile:
        level = json.load(infile)

    return level


def load_settings():
    in_path = bge.logic.expandPath("//saves/saves.txt")
    with open(in_path, "r") as infile:
        bge.logic.globalDict = json.load(infile)

    if not bge.logic.globalDict.get("version"):
        bge.logic.globalDict["version"] = vinland_version
        bge.logic.globalDict["profiles"] = {}
        bge.logic.globalDict["game_mode"] = "MENU_MODE"
        bge.logic.globalDict["mode_change"] = False
        bge.logic.globalDict["next_level"] = "StartMenu"
        add_new_profile("Default Profile")
        save_settings()

    bge.logic.globalDict["mode_change"] = False


def save_settings():
    out_path = bge.logic.expandPath("//saves/saves.txt")
    with open(out_path, "w") as outfile:
        json.dump(bge.logic.globalDict, outfile)


def add_new_vehicle(vehicle):

    def get_vehicle_id(vehicle_id_number):
        return "vehicle_{}".format(vehicle_id_number)

    vehicle_id = None

    id_number = 0
    added = False
    while not added:
        vehicle_id = get_vehicle_id(id_number)
        if vehicle_id not in bge.logic.globalDict["profiles"][bge.logic.globalDict["active_profile"]]["vehicles"]:
            bge.logic.globalDict["profiles"][bge.logic.globalDict["active_profile"]]["vehicles"][vehicle_id] = vehicle
            added = True
        id_number += 1

    save_settings()

    return vehicle_id


def get_editing_vehicle():
    active_profile = bge.logic.globalDict["profiles"][bge.logic.globalDict["active_profile"]]
    return active_profile["vehicles"][active_profile["editing"]]


def write_editing_vehicle(vehicle):
    active_profile = bge.logic.globalDict["profiles"][bge.logic.globalDict["active_profile"]]
    active_profile["vehicles"][active_profile["editing"]] = vehicle


def generate_inventory():
    inventory = []
    parts = vehicle_parts.get_vehicle_parts()

    for part_key in parts:
        for i in range(3):
            inventory.append([part_key, parts[part_key]["level"], parts[part_key]["part_type"]])

    return inventory


def add_new_profile(profile_name):
    debug_inventory = generate_inventory()

    default_profile = {"version": vinland_version, "volume": 1.0, "sensitivity": 0.95, "vehicles": {}, "editing": None,
                       "part_filter": "weapon", "inventory": debug_inventory, "game_turn": 0, "faction": "vinland", "money": 5000,
                       "saved_game": None, "part_page": 0}
    bge.logic.globalDict["profiles"][profile_name] = default_profile
    bge.logic.globalDict["active_profile"] = profile_name


def create_brush(brush_size, radius, RGB, outer=0, smooth=False):

    brush = bytearray(brush_size * brush_size * 4)
    center = mathutils.Vector([brush_size * 0.5, brush_size * 0.5])
    rgb = RGB
    half_rgb = [int(color * 0.5) for color in rgb]
    quarter_rgb = [int(color * 0.2) for color in half_rgb]

    for x in range(brush_size):
        for y in range(brush_size):
            i = y * (brush_size * 4) + x * 4
            location = mathutils.Vector([x, y])
            target_vector = location - center
            length = int(round(target_vector.length))

            if length == radius and smooth:
                pixel = half_rgb
            elif length > radius:
                if outer > 0 and length <= outer:
                    if length == outer:
                        pixel = quarter_rgb
                    else:
                        pixel = half_rgb
                else:
                    pixel = [0, 0, 0]
            else:
                pixel = rgb

            brush[i] = pixel[0]
            brush[i + 1] = pixel[1]
            brush[i + 2] = pixel[2]
            brush[i + 3] = 255

    return brush


def create_pixel(rbga):
    r, g, b, a = rbga
    pixel = bytearray(1 * 1 * 4)
    pixel[0] = r
    pixel[1] = g
    pixel[2] = b
    pixel[3] = a

    return pixel


def map_value(lowest_value, highest_value, current_value):
    return (current_value - lowest_value) / (highest_value - lowest_value)


def get_closest_vector(target_vector):

    if target_vector.length <= 0.0:
        target_vector = mathutils.Vector([0.0, 1.0])

    search_array = [[1, 0], [1, 1], [0, 1], [1, -1], [-1, 0], [-1, 1], [0, -1], [-1, -1]]

    best_facing = None
    best_angle = 4.0

    for facing in search_array:
        facing_vector = mathutils.Vector(facing)
        angle = facing_vector.angle(target_vector.to_2d())
        if angle < best_angle:
            best_facing = facing
            best_angle = angle

    return best_facing