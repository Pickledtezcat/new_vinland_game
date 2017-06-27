import bge
import bgeutils
import vehicle_parts
import mathutils

parts_dict = vehicle_parts.get_vehicle_parts()
color_dict = vehicle_parts.color_dict


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

    bgeutils.save_settings()

    return vehicle_id


def get_editing_vehicle():
    active_profile = bge.logic.globalDict["profiles"][bge.logic.globalDict["active_profile"]]
    return active_profile["vehicles"][active_profile["editing"]]


def write_editing_vehicle(vehicle):
    active_profile = bge.logic.globalDict["profiles"][bge.logic.globalDict["active_profile"]]
    active_profile["vehicles"][active_profile["editing"]] = vehicle


def replace_holding_part():

    active_profile = bge.logic.globalDict["profiles"][bge.logic.globalDict["active_profile"]]
    holding_key = active_profile["holding"]

    if holding_key:
        active_profile["rotated"] = False
        inventory_group = [holding_key, parts_dict[holding_key]["level"], parts_dict[holding_key]["part_type"]]

        active_profile["inventory"].append(inventory_group)
        active_profile["holding"] = None


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


def create_vehicle_layout():
    editing = get_editing_vehicle()

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
    write_editing_vehicle(editing)


def get_location_key(button, position):

    scale = 2.0

    parent = button.button_object
    origin = parent.worldPosition.copy()
    editing = get_editing_vehicle()

    chassis_dict = vehicle_parts.chassis_dict
    turret_dict = vehicle_parts.turret_dict

    chassis = chassis_dict[editing["chassis"]]
    turret = turret_dict[editing["turret"]]

    max_x = chassis["x"]
    max_y = max(chassis["y"] + 3, chassis["y"] + turret["y"])

    offset = mathutils.Vector([(max_x * 0.5) - 0.5, max_y * 0.5, 0.2])
    origin -= offset

    position = position.copy()
    position *= scale
    local_position = position - origin

    return bgeutils.get_key(local_position)


def check_adding_part(location_key):
    editing = get_editing_vehicle()
    parent_tile = editing["contents"].get(location_key)
    print(parent_tile)

    if not parent_tile:
        return "Click on chassis to add parts."
    else:
        parent_location = parent_tile["location"]

        if parent_location == "BLOCKED":
            return "That item cannot be placed there."
        else:

            active_profile = bge.logic.globalDict["profiles"][bge.logic.globalDict["active_profile"]]
            holding_key = active_profile["holding"]
            if not holding_key:
                return "Left click item from inventory to pick up and place."

            rotated = active_profile["rotated"]
            holding_part = parts_dict[holding_key]

            holding_part_type = holding_part["part_type"]

            # TODO include more placement checks
            chassis_only = ["DRIVE", "ENGINE"]

            invalid_location = parent_location == "TURRET" and holding_part_type in chassis_only

            if invalid_location:
                return "That item cannot be placed there."
            else:
                holding_x = holding_part["x_size"]
                holding_y = holding_part["y_size"]

                x, y = bgeutils.get_loc(location_key)

                if rotated:
                    holding_x, holding_y = holding_y, holding_x

                for nx in range(holding_x):
                    for ny in range(holding_y):
                        n_key = bgeutils.get_key((x + nx, y + ny))
                        n_tile = editing["contents"].get(n_key)

                        if not n_tile:
                            return "Place part inside the vehicle."
                        else:
                            if n_tile["part"]:
                                return "An item is already placed here."

                            if n_tile["location"] != parent_location:
                                return "Place part in a single location. Turret, Front or Flanks."

        return "Part Placed."


def place_part(location_key):
    editing = get_editing_vehicle()

    active_profile = bge.logic.globalDict["profiles"][bge.logic.globalDict["active_profile"]]
    holding_key = active_profile["holding"]
    rotated = active_profile["rotated"]
    holding_part = parts_dict[holding_key]
    holding_x = holding_part["x_size"]
    holding_y = holding_part["y_size"]

    x, y = bgeutils.get_loc(location_key)

    if rotated:
        holding_x, holding_y = holding_y, holding_x

    for nx in range(holding_x):
        for ny in range(holding_y):
            n_key = bgeutils.get_key((x + nx, y + ny))
            editing["contents"][n_key]["part"] = holding_key
            editing["contents"][n_key]["parent_tile"] = location_key
            editing["contents"][n_key]["rotated"] = rotated

    write_editing_vehicle(editing)

    bge.logic.globalDict["profiles"][bge.logic.globalDict["active_profile"]]["holding"] = None
    bge.logic.globalDict["profiles"][bge.logic.globalDict["active_profile"]]["rotated"] = False


def draw_parts(button):

    editing = get_editing_vehicle()
    contents = editing["contents"]
    origin = button.button_object.worldPosition.copy()

    chassis_dict = vehicle_parts.chassis_dict
    turret_dict = vehicle_parts.turret_dict

    chassis = chassis_dict[editing["chassis"]]
    turret = turret_dict[editing["turret"]]

    max_x = chassis["x"]
    max_y = max(chassis["y"] + 3, chassis["y"] + turret["y"])

    sub_offset_vector = mathutils.Vector([0.25, 0.25, 0.0])

    parents = []
    for tile_key in contents:
        tile = contents[tile_key]
        parent_tile = tile["parent_tile"]

        if parent_tile:
            if parent_tile not in parents:
                parents.append(parent_tile)

    for parent_tile_key in parents:
        parent_tile = contents[parent_tile_key]
        part_key = parent_tile["part"]
        rotated = parent_tile["rotated"]
        part = parts_dict[part_key]
        part_type = part["part_type"]
        part_x = part["x_size"]
        part_y = part["y_size"]

        if rotated:
            part_x, part_y = part_y, part_x

        part_color = color_dict[part_type.lower()]
        scale = 0.5

        x, y = bgeutils.get_loc(parent_tile_key)

        for tx in range(x - 1, x + part_x + 1):
            for ty in range(y - 1, y + part_y + 1):

                search_array = [(1, 0, 1), (1, 1, 2), (0, 1, 4), (0, 0, 8)]
                tile_number = 0

                for n in search_array:
                    nx = tx + n[0]
                    ny = ty + n[1]

                    if x < nx < x + part_x + 1:
                        if y < ny < y + part_y + 1:
                            tile_number += n[2]

                    if tile_number > 0:
                        tile_name = "m_parts.{}".format(str(tile_number).zfill(3))
                        tile = button.button_object.scene.addObject(tile_name, button.button_object, 0)
                        offset = mathutils.Vector([(tx + 0.5) - (max_x * 0.5), ty - (max_y * 0.5), 0.2])
                        position = origin + offset
                        position *= scale
                        tile.worldPosition = position
                        tile.worldPosition -= sub_offset_vector
                        tile.color = part_color
                        tile.localScale *= scale
                        button.tiles.append(tile)


def draw_base(button):

    scale = 0.5

    parent = button.button_object
    origin = parent.worldPosition.copy()
    editing = get_editing_vehicle()
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
