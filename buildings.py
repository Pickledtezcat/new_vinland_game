import bge
import mathutils
import bgeutils


class Building(object):
    agent_type = "BUILDING"
    building_type = "HOUSE"

    def __init__(self, level, load_name, location, direction, building_id=None, load_dict=None):

        self.level = level

        if not building_id:
            self.building_id = "{}${}".format(self.building_type, self.level.get_new_id())
        else:
            self.building_id = building_id

        self.location = location
        self.direction = direction
        self.load_name = load_name
        self.box = None
        self.doors = []
        self.windows = []
        self.occupier = None

        self.load_dict = load_dict
        if self.load_dict:
            self.reload(self.load_dict)

        self.add_box()
        self.set_location()
        self.get_doors_and_windows()

        self.level.buildings[self.building_id] = self

    def get_closest_door(self, origin):

        closest = 30
        best_door = None

        for door in self.doors:
            target_vector = mathutils.Vector(origin) - mathutils.Vector(door)
            distance = target_vector.length
            if distance < closest:
                closest = distance
                best_door = door

        if best_door:
            return best_door

    def get_closest_window(self, origin):

        closest = 2000
        best_window = None

        for window_list in self.windows:
            window = window_list[0]

            target_vector = mathutils.Vector(origin) - mathutils.Vector(window)
            distance = target_vector.length
            if distance < closest:
                closest = distance
                best_window = window

        if best_window:
            return best_window

    def get_doors_and_windows(self):

        doors = bgeutils.get_ob_list("door", self.box.children)
        windows = bgeutils.get_ob_list("window", self.box.children)

        for door in doors:
            position = door.worldPosition.copy()
            location = [round(axis) for axis in position]

            if location not in self.doors:
                self.doors.append(location)

        for window in windows:
            position = window.worldPosition.copy()
            direction = window.getAxisVect([0.0, 1.0, 0.0])
            self.windows.append([list(position), list(direction)])

    def terminate(self):
        self.box.endObject()

    def save(self):
        save_dict = {"load_name": self.load_name, "building_type": self.building_type, "location": self.location,
                     "direction": self.direction, "doors": self.doors, "windows": self.windows, "occupier": self.occupier}

        return save_dict

    def reload(self, building_dict):
        self.location = building_dict["location"]
        self.load_name = building_dict["load_name"]
        self.direction = building_dict["direction"]
        self.doors = building_dict["doors"]
        self.windows = building_dict["windows"]
        self.occupier = building_dict["occupier"]

    def set_location(self):
        location = self.level.map.get(bgeutils.get_key(self.location))
        if location:
            self.box.worldPosition = mathutils.Vector(location["position"]).to_3d()
            self.box.worldPosition.z = location["height"]

            direction = mathutils.Vector(self.direction).to_3d().to_track_quat("Y", "Z").to_matrix().to_3x3()
            self.box.worldOrientation = direction

    def add_box(self):
        self.box = self.level.scene.addObject(self.load_name, self.level.own, 0)
        self.box['building_id'] = self.building_id
