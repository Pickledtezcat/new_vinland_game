import bge
import bgeutils
import vehicle_parts

parts_dict = vehicle_parts.get_vehicle_parts()


class VehicleWeapon(object):

    def __init__(self, part_key, location, weapon_location):

        part = parts_dict[part_key]
        self.part_key = part_key
        self.part = part
        self.location = location
        self.weapon_location = weapon_location

        self.name = self.part['name']
        self.rating = self.part['rating']
        self.flag = self.part['flag']

        advanced = ["IMPROVED_GUN", "ADVANCED_GUN"]
        support = ["MORTAR", "SUPPORT_GUN", "PRIMITIVE_GUN"]

        size = 0

        if self.part["rating"] > 4:
            if self.flag in support:
                size = 4
            elif self.flag in advanced:
                if self.part["rating"] > 7:
                    size = 5
                else:
                    size = 3
            else:
                if self.part["rating"] > 7:
                    size = 6
                else:
                    size = 3

        elif self.part["rating"] > 1:
            if self.flag in support:
                size = 2
            elif self.flag in advanced:
                size = 3
            else:
                size = 1

        self.visual = size
        self.rate_of_fire = 0
        self.emitter = None

    def set_emitter(self, emitter):
        self.emitter = emitter

    def update(self):
        pass


class InstalledPart(object):
    def __init__(self, part_key, location, weapon_location):
        part = parts_dict[part_key]
        self.part_key = part_key
        self.weight = part["x_size"] * part["y_size"]
        self.rating = part["rating"]
        self.level = part["level"]
        self.item_type = part["part_type"]
        self.flag = part["flag"]
        self.location = location
        self.weapon_location = weapon_location


class VehicleStats(object):

    def __init__(self, vehicle):

        self.faction_number = 1
        # TODO handle getting factions
        self.vehicle_type = "TANK"
        self.options = vehicle["options"]
        self.turret_size = vehicle["turret"]
        self.chassis_size = vehicle["chassis"]
        self.contents = vehicle["contents"]
        self.display_name = vehicle["name"]

        self.design_rules = vehicle_parts.get_design_rules()

        self.turret_dict = vehicle_parts.turret_dict[self.turret_size]
        self.chassis_dict = vehicle_parts.chassis_dict[self.chassis_size]

        self.speed = []
        self.handling = []
        self.reverse_speed_mod = 0

        self.drive_type = "WHEELED"
        self.drive_dict = vehicle_parts.drive_dict["WHEELED"]
        self.suspension_type = "UNSPRUNG"
        self.suspension_dict = vehicle_parts.suspension_dict["UNSPRUNG"]
        self.suspension_rating = 0
        self.engine_handling = 0
        self.suspension_ratio = 0
        self.engine_rating = 0
        self.stability = 0
        self.vision_distance = 1
        self.turret_speed = 0

        self.weight = 0
        self.crew = 0
        self.range = 0
        self.stores = 0
        self.ammo = 0
        self.reliability = 0
        self.cost = 0

        self.flags = []
        self.armor = dict(TURRET=0, FRONT=0, FLANKS=0)
        self.manpower = dict(TURRET=0, FRONT=0, FLANKS=0)
        self.crits = dict(TURRET=[], FRONT=[], FLANKS=[])
        self.weapons = []
        self.durability = 0
        self.armored = False
        self.open_top = False

        self.artillery = False
        self.invalid = []

        self.get_design()
        self.generate_stats()

    def get_design(self):

        for option_set in self.options:

            option_key = option_set[0]
            option = self.design_rules[option_key]
            setting = option_set[1]

            if setting:
                if option["flag"] == "GUN_CARRIAGE":
                    self.vehicle_type = "GUN_CARRIAGE"

                elif option["option_type"] == "DRIVE":
                    flag = option["flag"]
                    if flag == "WHEELED":
                        self.vehicle_type = "CAR"
                    elif flag == "HALFTRACK":
                        self.vehicle_type = "HALFTRACK"
                    else:
                        self.vehicle_type = "TANK"

                    self.drive_type = option["flag"]
                    self.drive_dict = vehicle_parts.drive_dict[self.drive_type]

                self.flags.append(option["flag"])

    def generate_stats(self):

        parents =[]
        items = []
        for tile_key in self.contents:
            content = self.contents[tile_key]
            if content["part"]:
                if content["parent_tile"] not in parents:
                    parents.append(content["parent_tile"])
                    item = InstalledPart(content["part"], content["location"], content["weapon_location"])
                    if item.item_type == "WEAPON":
                        self.weight += item.weight
                        self.durability += item.weight * 0.5
                        self.ammo += 0.5

                        cost = ((5 + item.level) * 20) * item.weight
                        self.cost += cost
                        weapon = VehicleWeapon(item.part_key, item.location, item.weapon_location)
                        self.weapons.append(weapon)

                    if item.flag not in self.flags:
                        self.flags.append(item.flag)
                    items.append(item)

        sorted_items = sorted(items, key=lambda this_item: this_item.rating)

        for item in sorted_items:
            rating = item.rating
            flag = item.flag
            item_type = item.item_type
            level = item.level
            weight = item.weight
            location = item.location

            for i in range(weight):
                self.crits[location].append(item_type)

            if item_type == "CREW":
                self.crew += 1
                self.manpower[location] += rating
                self.weight += 0.5
                self.cost += ((5 + level) * 20) * weight

            elif item_type == "ENGINE":
                if not self.engine_handling:
                    self.engine_handling = rating * 0.5
                    self.engine_rating = rating
                else:
                    self.engine_rating += rating * 0.5

                self.weight += weight
                self.durability += weight
                self.cost += ((5 + level) * 20) * weight

            elif item_type == "DRIVE":
                suspension_type = vehicle_parts.suspension_dict.get(flag)
                if suspension_type:
                    self.suspension_type = flag
                    self.suspension_rating += rating

                self.durability += weight
                self.weight += weight
                self.cost += ((5 + level) * 20) * weight

            elif item_type == "ARMOR":
                if location == "TURRET":
                    armor_scale = self.turret_dict["armor_scale"]
                else:
                    armor_scale = self.chassis_dict["armor_scale"]

                self.weight += weight
                self.durability += weight

                if self.armor[location] > 0:
                    self.armor[location] += (rating * 5.0) * armor_scale
                else:
                    self.armor[location] += (rating * 10.0) * armor_scale

                self.cost += ((5 + level) * 15) * weight

                spalling = ["CAST", "RIVETED", "THIN"]
                if flag in spalling:
                    for s in range(int(weight)):
                        self.crits[location].append("SPALLING")

            else:
                self.weight += weight
                self.durability += weight * 0.5
                self.cost += ((5 + level) * 5) * weight

            for section_key in self.armor:
                self.armor[section_key] = round(self.armor[section_key])
                if self.armor[section_key] > 0:
                    self.armored = True

            if flag == "AMMO":
                self.ammo += rating

            # TODO handle other flags, handle reliability

        if self.vehicle_type == "GUN_CARRIAGE":
            self.get_carriage_movement()
        else:
            self.get_vehicle_movement()
            self.get_vision()

    def get_carriage_movement(self):

        self.stability = 6

        on_road_handling = max(1, int(self.weight / max(1, self.crew)))
        off_road_handling = int(on_road_handling * 0.5)

        self.handling = [on_road_handling, off_road_handling]
        self.speed = [on_road_handling, off_road_handling]

    def get_vehicle_movement(self):
        power_to_weight = (self.engine_rating * 50.0) / max(1.0, self.weight)

        drive_mods = self.drive_dict
        suspension_mods = self.suspension_dict

        stability = suspension_mods["stability"] + drive_mods["stability"]
        on_road_handling = suspension_mods["handling"][0] + drive_mods["handling"][
            0] + self.engine_handling
        off_road_handling = suspension_mods["handling"][1] + drive_mods["handling"][
            1] + self.engine_handling

        tonnage_mod = round(self.weight * 0.1)

        on_road_handling -= tonnage_mod
        off_road_handling -= tonnage_mod

        on_road_speed = power_to_weight * (suspension_mods["on_road"] + drive_mods["on_road"])
        off_road_speed = power_to_weight * (suspension_mods["off_road"] + drive_mods["off_road"])

        if self.suspension_rating <= 0:
            weight_scale = 0.0
        else:
            weight_scale = self.suspension_rating / max(1.0, self.weight)

        on_road_speed = min(99, round(on_road_speed * weight_scale))
        off_road_speed = min(49, round(off_road_speed * weight_scale))
        on_road_handling = max(1, round(on_road_handling * weight_scale))
        off_road_handling = max(1, round(off_road_handling * weight_scale))

        self.stability = max(1, stability)
        self.handling = [on_road_handling, off_road_handling]
        self.speed = [on_road_speed, off_road_speed]

    def get_vision(self):

        vision_distance = 1
        good_vision = False
        great_vision = False

        if "OPEN_TOP" in self.flags:
            good_vision = True
            self.open_top = True

        if self.turret_size > 0:
            if "OPEN_TOP" in self.flags:
                great_vision = True
            else:
                good_vision = True

        if "COMMANDER" in self.flags:
            if self.turret_size > 0:
                great_vision = True
            else:
                good_vision = True

        if "COMMANDERS_CUPOLA" in self.flags:
            if self.turret_size > 0:
                great_vision = True
            else:
                good_vision = True

        if not self.armored:
            vision_distance += 1

        if great_vision:
            vision_distance += 2

        elif good_vision:
            vision_distance += 1

        if "NIGHT_VISION_CUPOLA" in self.flags:
            vision_distance += 1

        self.vision_distance = vision_distance
        self.durability = round(self.durability)
        self.weight = round(self.weight, 1)























