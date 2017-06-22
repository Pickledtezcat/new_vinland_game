import bge
import bgeutils
import vehicle_parts


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

            tile = {"x_y": chassis_key, "location": location, "weapon_location": weapon_location}
            contents[bgeutils.get_key(chassis_key)] = tile

    turret_padding_x = int((chassis["x"] - (turret["x"])) * 0.5)
    turret_padding_y = int(chassis["y"]) + 1

    for x in range(turret_padding_x, turret_padding_x + turret["x"]):
        for y in range(turret_padding_y, turret_padding_y + turret["y"]):
            turret_key = (x, y)
            tile = {"x_y": turret_key, "location": "TURRET", "weapon_location": "TURRET"}
            contents[bgeutils.get_key(turret_key)] = tile

    editing["contents"] = contents
    return editing