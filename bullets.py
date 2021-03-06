import bge
import bgeutils
import mathutils
import particles
import random


class Bullet(object):

    def __init__(self, level, curve, agent, damage, timer=0.0, index=0, agent_id=None):

        self.bullet_type = self.set_bullet_type()
        self.level = level
        self.box = self.add_box()
        self.box.visible = False
        self.damage = damage

        self.curve = curve
        self.curve_vector = None
        self.timer = timer
        self.index = index
        if not agent:
            self.agent = self.level.agents[agent_id]
        else:
            self.agent = agent
        self.speed = 0.15
        self.done = False
        self.level.artillery_bullets.append(self)

    def set_bullet_type(self):
        return "BULLET"

    def terminate(self):
        self.box.endObject()

    def add_box(self):
        return self.level.scene.addObject("grenade_object", self.level.own, 0)

    def detonate(self):
        command = {"label": "EXPLOSION", "effect": "DUMMY_EXPLOSION", "damage": 1, "position": self.box.worldPosition.copy(), "agent": self.agent}
        self.level.commands.append(command)
        self.done = True

    def update(self):
        curve_length = len(self.curve)

        self.timer = min(1.0, self.timer + self.speed)
        if self.timer >= 1.0:
            self.timer = 0.0
            self.index += 1

        if self.index >= curve_length - 1:
            self.detonate()
        else:
            next_point = mathutils.Vector(self.curve[self.index + 1])
            current_point = mathutils.Vector(self.curve[self.index])

            self.curve_vector = next_point - current_point
            curve_position = current_point.lerp(next_point, self.timer)
            if self.curve_vector:
                self.box.worldOrientation = self.curve_vector.to_3d().to_track_quat("Y", "Z").to_matrix().to_3x3()
                self.box.worldPosition = curve_position
                self.box.visible = True
            else:
                self.done = True


class Grenade(Bullet):
    def set_bullet_type(self):
        return "GRENADE"

    def detonate(self):
        command = {"label": "EXPLOSION", "effect": "EXPLOSION", "damage": self.damage, "position": self.box.worldPosition.copy(), "agent": self.agent}
        self.level.commands.append(command)
        self.done = True


class Rocket(Bullet):
    def set_bullet_type(self):
        return "ROCKET"

    def detonate(self):
        command = {"label": "EXPLOSION", "effect": "EXPLOSION", "damage": self.damage, "position": self.box.worldPosition.copy(), "agent": self.agent}
        self.level.commands.append(command)
        self.done = True


class Shell(Bullet):
    def set_bullet_type(self):
        return "SHELL"

    def detonate(self):
        command = {"label": "EXPLOSION", "effect": "EXPLOSION", "damage": self.damage, "position": self.box.worldPosition.copy(), "agent": self.agent}
        self.level.commands.append(command)
        self.done = True