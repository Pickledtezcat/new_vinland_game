import bge
import bgeutils
import vehicle_parts
import mathutils


def build_base_vehicle():
    vehicle = {}

    options = vehicle_parts.get_design_rules()
    for option_key in options:
        option = options[option_key]

        if option["name"] == "tracked drive":
            option["setting"] = True
        else:
            option["setting"] = False

        options[option_key] = option

    vehicle["options"] = options
    vehicle["turret"] = 0
    vehicle["chassis"] = 1
    vehicle["contents"] = {}
    vehicle["name"] = "new vehicle"

    return vehicle


def create_vehicle_layout(editing):

    chassis_dict = vehicle_parts.chassis_dict
    turret_dict = vehicle_parts.turret_dict

    chassis = chassis_dict[editing["chassis"]]
    turret = turret_dict[editing["turret"]]

    contents = {}
    blocked_tiles = []

    block_padding_x = int((chassis["x"] - turret["block_x"]) * 0.5)
    block_padding_y = chassis["front"]

    for x in range(block_padding_x, block_padding_x + turret["block_x"]):
        for y in range(block_padding_y, block_padding_y + turret["block_y"]):
            blocked_tiles.append((x, y))

    for x in range(chassis["x"]):
        for y in range(chassis["y"]):
            chassis_key = (x, y)

            if chassis_key in blocked_tiles:
                location = "BLOCKED"

            elif y > chassis["front"]:
                location = "FRONT"

            else:
                location = "FLANKS"

            weapon_location = location

            if location == "FLANKS":
                if y < 1:
                    weapon_location = "BACK"
                elif x >= (chassis["x"] * 0.5):
                    weapon_location = "RIGHT"
                else:
                    weapon_location = "LEFT"

            tile = {"x_y": chassis_key, "location": location, "weapon_location": weapon_location, "part": None, "parent_tile": None, "rotated": False}
            contents[bgeutils.get_key(chassis_key)] = tile

    turret_padding_x = int((chassis["x"] - (turret["x"])) * 0.5)
    turret_padding_y = int(chassis["y"]) + 1

    for x in range(turret_padding_x, turret_padding_x + turret["x"]):
        for y in range(turret_padding_y, turret_padding_y + turret["y"]):
            turret_key = (x, y)
            tile = {"x_y": turret_key, "location": "TURRET", "weapon_location": "TURRET", "part": None, "parent_tile": None, "rotated": False}
            contents[bgeutils.get_key(turret_key)] = tile

    editing["contents"] = contents
    return editing


def get_location_key(button, position):

    scale = 2.0

    parent = button.button_object
    origin = parent.worldPosition.copy()
    editing = bgeutils.get_editing_vehicle()

    chassis_dict = vehicle_parts.chassis_dict
    turret_dict = vehicle_parts.turret_dict

    chassis = chassis_dict[editing["chassis"]]
    turret = turret_dict[editing["turret"]]

    max_x = chassis["x"]
    max_y = max(chassis["y"] + 3, chassis["y"] + turret["y"])

    offset = mathutils.Vector([(max_x * 0.5) - 0.5, max_y * 0.5, 0.2])
    origin -= offset

    position *= scale
    local_position = position - origin

    return bgeutils.get_key(local_position)


def draw_base(button):

    scale = 0.5

    parent = button.button_object
    origin = parent.worldPosition.copy()
    editing = bgeutils.get_editing_vehicle()
    contents = editing["contents"]

    chassis_dict = vehicle_parts.chassis_dict
    turret_dict = vehicle_parts.turret_dict

    chassis = chassis_dict[editing["chassis"]]
    turret = turret_dict[editing["turret"]]

    tile_types = ["FRONT", "FLANKS", "TURRET", "BLOCKED"]

    max_x = chassis["x"]
    max_y = max(chassis["y"] + 3, chassis["y"] + turret["y"])

    sub_offset_vector = mathutils.Vector([0.25, 0.25, 0.0])

    for tile_type in tile_types:

        if tile_type != "BLOCKED":
            tile_ob = "m_empty"
            tile_color = [1.0, 1.0, 1.0, 1.0]
        else:
            tile_ob = "m_parts"
            tile_color = [0.5, 0.5, 0.5, 1.0]

        for x in range(-1, max_x + 1):
            for y in range(-1, max_y + 1):
                offset = mathutils.Vector([(x + 0.5) - (max_x * 0.5), y - (max_y * 0.5), 0.2])
                position = origin + offset
                position *= scale

                search_array = [(1, 0, 1), (1, 1, 2), (0, 1, 4), (0, 0, 8)]
                tile_number = 0

                for n in search_array:
                    search_key = (x + n[0], y + n[1])

                    n_tile = contents.get(bgeutils.get_key(search_key))
                    if n_tile:
                        if n_tile["location"] == tile_type:
                            tile_number += n[2]

                    if tile_number > 0:
                        tile_name = "{}.{}".format(tile_ob, str(tile_number).zfill(3))
                        tile_object = parent.scene.addObject(tile_name, parent, 0)
                        tile_object.worldPosition = position.copy()
                        tile_object.color = tile_color
                        tile_object.worldPosition += sub_offset_vector
                        tile_object.localScale *= scale
                        button.tiles.append(tile_object)
