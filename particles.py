import bge
import mathutils
import bgeutils


class Particle(object):

    def __init__(self, level):
        self.level = level
        self.ended = False
        self.box = self.add_box()
        self.timer = 0.0
        self.level.particles.append(self)

    def add_box(self):
        pass

    def terminate(self):
        if self.box:
            self.box.endObject()

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


class MovementPointIcon(Particle):

    def __init__(self, level, position):
        super().__init__(level)
        self.released = False
        self.invalid_location = False
        self.set_position(position)

    def add_box(self):
        return self.level.own.scene.addObject("movement_marker", self.level.own, 0)

    def set_position(self, position):
        if position:
            in_map = 0.0 < position[0] < self.level.map_size and 0.0 < position[1] < self.level.map_size

            if in_map:
                tile = self.level.map[bgeutils.get_key(position)]
                position = mathutils.Vector(tile["position"]).to_3d()
                position.z = tile["height"] + 0.5
                normal = tile["normal"]
                self.invalid_location = False

            else:
                position = position.to_3d()
                normal = mathutils.Vector([0.0, 0.0, 1.0])
                self.invalid_location = True

            self.box.worldPosition = position
            self.box.worldPosition.z += 0.5
            self.box.alignAxisToVect(normal)

    def update(self):

        if self.released:
            if self.timer >= 1.0:
                self.ended = True
            else:
                self.timer += 0.02
                color = bgeutils.smoothstep(1.0 - self.timer)
                self.box.color = [color, color, color, 1.0]


class BulletFlash(Particle):

    def __init__(self, level, position, target, delay=0):
        super().__init__(level)

        self.color = [1.0, 1.0, 1.0]
        self.position = position
        self.target = target
        self.delay = delay
        self.place_particle()

    def add_box(self):
        return self.level.own.scene.addObject("bullet_flash", self.level.own, 0)

    def place_particle(self):

        position = mathutils.Vector(self.position)
        target = mathutils.Vector(self.target)

        target_vector = target - position
        self.box.worldPosition = position
        self.box.worldOrientation = target_vector.to_track_quat("Y", "Z").to_matrix().to_3x3()
        self.box.localScale.y = target_vector.length

    def update(self):
        r, g, b = self.color

        if self.delay > 0:
            self.delay -= 1
            color = 0.0
        else:
            self.timer += 0.4
            color = 1.0 - self.timer

        self.box.color = [r * color, g * color, b * color, 1.0]
        self.box.localScale = [self.timer, self.timer, self.timer]

        if self.timer >= 1.0:
            self.ended = True


class YellowBulletFlash(BulletFlash):
    def __init__(self, level, position, target, delay=0):
        super().__init__(level, position, target, delay)

        self.color = [0.5, 0.5, 0.0]


class RedBulletFlash(BulletFlash):
    def __init__(self, level, position, target, delay=0):
        super().__init__(level, position, target, delay)

        self.color = [1.0, 0.0, 0.0]


class BulletStreak(Particle):

    def __init__(self, level, position, target, sound, delay=0):
        super().__init__(level)

        self.color = [1.0, 1.0, 1.0]
        self.sound = sound

        position[2] += 0.5
        target[2] += 0.5

        self.position = position
        self.target = target
        self.delay = delay + 18
        self.place_particle()

    def add_box(self):
        return self.level.own.scene.addObject("bullet_streak", self.level.own, 0)

    def place_particle(self):

        position = mathutils.Vector(self.position)
        target = mathutils.Vector(self.target)

        target_vector = target - position
        self.box.worldPosition = position
        self.box.worldOrientation = target_vector.to_track_quat("Y", "Z").to_matrix().to_3x3()
        self.box.localScale.y = target_vector.length

    def play_sound(self):
        if self.sound:
            sound_command = {"label": "SOUND_EFFECT",
                             "content": (self.sound, self.box, 0.5, 1.0)}
            self.level.commands.append(sound_command)
            self.sound = None

    def update(self):
        r, g, b = self.color

        if self.delay > 0:
            self.delay -= 1
            color = 0.0
        else:
            self.play_sound()
            self.timer += 0.4
            color = 1.0 - self.timer

        self.box.color = [r * color, g * color, b * color, 1.0]

        if self.timer >= 1.0:
            self.ended = True


class FaintBulletStreak(BulletStreak):
    def __init__(self, level, position, target, sound, delay=0):
        super().__init__(level, position, target, sound, delay)

        self.color = [0.1, 0.0, 0.0]


class YellowBulletStreak(BulletStreak):
    def __init__(self, level, position, target, sound, delay=0):
        super().__init__(level, position, target, sound, delay)

        self.color = [0.5, 0.5, 0.0]


class RedBulletStreak(BulletStreak):
    def __init__(self, level, position, target, sound, delay=0):
        super().__init__(level, position, target, sound, delay)

        self.color = [1.0, 0.0, 0.0]


class DummyExplosion(Particle):
    def __init__(self, level, location):
        super().__init__(level)

        self.color = [1.0, 1.0, 1.0]
        self.start_scale = mathutils.Vector([0.0, 0.0, 0.0])
        self.end_scale = mathutils.Vector([1.0, 1.0, 1.0])
        self.expansion = 0.05
        self.fall_off = 0.96
        tile = self.level.get_tile(location)
        if tile:
            position = mathutils.Vector([tile["position"][0], tile["position"][1], tile["height"]])
        else:
            position = location

        self.box.worldPosition = position
        sound_command = {"label": "SOUND_EFFECT", "content": ("I_GRENADE", self.box, 0.5, 1.0)}
        self.level.commands.append(sound_command)

    def add_box(self):
        return self.level.own.scene.addObject("dummy_explosion", self.level.own, 0)

    def update(self):

        if self.timer >= 1.0:
            self.ended = True
        else:
            self.expansion = max(0.0001, self.expansion * self.fall_off)

            self.timer += self.expansion
            color = bgeutils.smoothstep(1.0 - self.timer)
            self.box.color = [color, color * color, 0.0, 1.0]

            self.box.localScale = self.start_scale.lerp(self.end_scale, self.timer)






