import bge
import mathutils


class Particle(object):

    def __init__(self, level):
        self.level = level
        self.ended = False
        self.box = self.add_box()

        self.level.particles.append(self)

    def add_box(self):
        pass

    def terminate(self):
        pass

    def update(self):
        pass


class DebugLabel(Particle):

    def __init__(self, level, owner):
        super().__init__(level)

        self.owner = owner
        self.text_object = self.box.children[0]

    def add_box(self):
        return self.level.own.scene.addObject("debug_label", self.level.own, 0)

    def update(self):
        self.box.worldPosition = self.owner.box.worldPosition.copy()
        self.text_object["Text"] = self.owner.debug_text

        if self.owner.selected:
            self.text_object.color = [0.0, 1.0, 0.0, 1.0]
        else:
            self.text_object.color = [1.0, 0.0, 0.0, 1.0]







