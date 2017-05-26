import bge
import mathutils
import bgeutils


class Building(object):
    building_type = "HOUSE"

    def __init__(self, level, load_name, location, direction, building_id=None, load_dict=None):

        self.level = level

        if not building_id:
            self.building_id = "{}${}".format(self.building_type, self.level.agent_id_index)
            self.level.agent_id_index += 1
        else:
            self.building_id = building_id

        self.location = location
        self.direction = direction
        self.load_name = load_name
        self.box = None
        self.mesh = None

        self.load_dict = load_dict
        if self.load_dict:
            self.reload(self.load_dict)

        self.add_box()
        self.set_location()

        self.level.buildings[self.building_id] = self

    def terminate(self):
        self.box.endObject()

    def save(self):
        save_dict = {"load_name": self.load_name, "building_type": self.building_type, "location": self.location,
                     "direction": self.direction}

        return save_dict

    def reload(self, building_dict):
        self.location = building_dict["location"]
        self.load_name = building_dict["load_name"]
        self.direction = building_dict["direction"]

    def set_location(self):
        location = self.level.map.get(bgeutils.get_key(self.location))
        if location:
            self.box.worldPosition = mathutils.Vector(location["position"]).to_3d()
            self.box.worldPosition.z = location["height"]

            direction = mathutils.Vector(self.direction).to_3d().to_track_quat("Y", "Z").to_matrix().to_3x3()
            self.box.worldOrientation = direction

    def add_box(self):
        self.box = self.level.scene.addObject(self.load_name, self.level.own, 0)
        self.mesh = bgeutils.get_ob("building_mesh", self.box.childrenRecursive)
        self.box['building_id'] = self.building_id
