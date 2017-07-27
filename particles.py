import bge
import mathutils
import bgeutils
import random

infantry_bullet_dict = {"PISTOL": {"color": None, "instances": 1},
                        "MG": {"color": None, "instances": 3},
                        "LIGHT_MG": {"color": None, "instances": 3},
                        "RIFLE": {"color": None, "instances": 1},
                        "HEAVY_RIFLE": {"color": [1.0, 1.0, 1.0], "instances": 1},
                        "ANTI_TANK": {"color": [1.0, 0.2, 0.0], "instances": 1},
                        "SMG": {"color": None, "instances": 3}}

particle_ranges = {"chunk_1": 8,
                   "dirt_1": 8,
                   "gun_flash": 4,
                   "after_flash": 4,
                   "smoke_blast": 4,
                   "dirt_blast": 4,
                   "sparks": 8,
                   "explosion_1": 8,
                   "bang_1": 8,
                   "bang_2": 8,
                   "bang_3": 8,
                   "simple_dirt": 8,
                   "round_smoke": 8,
                   "bubble_smoke": 8}


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
        self.process()

    def process(self):
        pass


class AnimatedParticle(Particle):

    mesh_name = None

    def __init__(self, level):

        self.mesh_name = self.get_mesh_name()
        super().__init__(level)

        self.max_frame = particle_ranges[self.mesh_name]
        self.max_sub_frame = 4

        self.sub_frame = 0
        self.frame = random.randint(1, self.max_frame)

        self.switch_frame()

    def get_mesh_name(self):
        return "chunk_1"

    def add_box(self):
        return self.level.own.scene.addObject(self.mesh_name, self.level.own, 0)

    def animation_update(self):
        if self.sub_frame < self.max_sub_frame:
            self.sub_frame += 1
        else:
            self.frame += 1
            self.sub_frame = 0
            self.switch_frame()

            if self.frame >= self.max_frame:
                self.frame = 1

    def switch_frame(self):

        if 0 < self.frame < self.max_frame:
            frame_name = "{}.{}".format(self.mesh_name, str(self.frame).zfill(3))
            self.box.replaceMesh(frame_name)

    def update(self):
        self.animation_update()
        self.process()


class DebugLabel(Particle):
    def __init__(self, level, owner):
        super().__init__(level)

        self.owner = owner
        self.text_object = self.box.children[0]

    def add_box(self):
        return self.level.own.scene.addObject("debug_label", self.level.own, 0)

    def process(self):
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

    def process(self):

        if self.released:
            if self.timer >= 1.0:
                self.ended = True
            else:
                self.timer += 0.02
                color = bgeutils.smoothstep(1.0 - self.timer)
                self.box.color = [color, color, color, 1.0]


class NormalHit(Particle):

    def __init__(self, level, tile, rating):
        super().__init__(level)

        height = tile["height"]
        position = mathutils.Vector(tile["position"]).to_3d()
        scatter = mathutils.Vector([random.uniform(-0.5, 0.5) for _ in range(3)])
        position += scatter
        position.z = height + 0.2
        self.rating = rating

        intensity = 1

        if self.rating > 100:
            intensity = 3
        elif self.rating > 50:
            intensity = 2

        self.scale = self.rating * 0.1

        ground_position = position.copy()
        ground_position.z += 1.0

        if intensity == 1:
            for i in range(3):
                ArmorSparks(self.level, self.scale * 0.8, ground_position.copy())
                ArmorBlast(self.level, self.scale * 0.3, ground_position.copy())
            SmallSmoke(self.level, self.scale * 1.5, ground_position.copy(), delay=12)

        else:
            if intensity == 2:
                number = 4
            else:
                number = 8

            for i in range(number):
                ArmorSparks(self.level, self.scale * 0.4, ground_position.copy())
                LargeSmoke(self.level, self.scale * 0.6, ground_position.copy(), delay=4)
                ArmorBlast(self.level, self.scale * 0.2, ground_position.copy())

        ExplosionSound(self.level, ground_position.copy(), intensity)

        self.ended = True


class ArmorSparks(Particle):

    def __init__(self, level, growth, position):
        super().__init__(level)

        self.grow = 1.002 * growth
        s = 0.01
        self.up_force = mathutils.Vector([random.uniform(-s, s), random.uniform(-s, s), random.uniform(-s, s)])

        self.box.worldPosition = position.copy()

    def add_box(self):
        mesh = "{}.{}".format("sparks", str(random.randint(1, 8)).zfill(3))
        return self.level.own.scene.addObject(mesh, self.level.own, 0)

    def process(self):

        if self.timer >= 1.0:
            self.ended = True
        else:
            self.timer += 0.01
            c = 1.0 - self.timer
            a = 1.0 - (self.timer * 0.5)

            self.box.color = [c, c, c, a]

            self.box.worldPosition += self.up_force
            scale = (1.0 * self.grow) * self.timer

            self.box.localScale = [scale, scale, scale]


class ArmorBlast(Particle):

    def __init__(self, level, growth, position):
        super().__init__(level)

        self.grow = 1.002 * growth

        s = 0.05
        self.up_force = mathutils.Vector([random.uniform(-s, s), random.uniform(-s, s), random.uniform(-s, s)])
        self.down_force = mathutils.Vector([0.0, 0.0, -0.05])

        self.box.worldPosition = position.copy()
        self.box.color *= 0.5
        self.box.color[3] = 1.0

    def add_box(self):
        mesh = "{}.{}".format("simple_dirt", str(random.randint(1, 8)).zfill(3))
        return self.level.own.scene.addObject(mesh, self.level.own, 0)

    def process(self):

        if self.timer >= 1.0:
            self.ended = True

        else:
            self.timer += 0.008
            c = 1.0 - self.timer
            a = 1.0 - (self.timer * 0.5)

            self.box.color = [c, c, c, a]

            up_force = self.up_force.lerp(self.down_force, self.timer)
            self.box.worldPosition += up_force
            scale = (1.0 * self.grow) * self.timer

            self.box.localScale = [scale, scale, scale]


class NormalExplosion(Particle):

    def __init__(self, level, tile, rating, airburst=False):
        super().__init__(level)

        height = tile["height"]
        self.normal = tile["normal"]
        self.position = mathutils.Vector(tile["position"]).to_3d()
        scatter = mathutils.Vector([random.uniform(-0.5, 0.5) for _ in range(3)])
        self.position += scatter
        self.position.z = height + 0.2
        self.rating = rating
        self.delay = 12
        self.airburst = airburst

        if self.airburst:
            self.rating *= 0.5

        self.intensity = 1

        if self.rating > 100.0:
            self.intensity = 3
        elif self.rating > 50.0:
            self.intensity = 2

        self.scale = self.rating * 0.1

    def activate(self):

        ground_position = self.position.copy()
        smoke_position = self.position.copy()
        smoke_position.z += 0.5

        if self.airburst:
            self.position.z += 1.5
        else:
            ScorchMark(self.level, ground_position.copy(), self.scale * 0.2, self.normal.copy())

        if self.intensity == 1:
            for i in range(3):
                SmallBlast(self.level, self.scale * 0.6, ground_position.copy())
            SmallSmoke(self.level, self.scale * 1.5, smoke_position.copy(), delay=12)

        else:
            if self.intensity == 2:
                number = 6
                scale_mod = 0.3
            else:
                number = 12
                scale_mod = 0.15

            for i in range(number):
                LargeBlast(self.level, self.scale * (scale_mod * 0.6), ground_position.copy())
                LargeSmoke(self.level, self.scale * scale_mod, smoke_position.copy(), delay=4)
                DirtBlast(self.level, self.scale * scale_mod, ground_position.copy())

        ExplosionSound(self.level, ground_position.copy(), self.intensity)

        self.ended = True

    def process(self):
        if self.delay > 0:
            self.delay -= 1
        else:
            self.activate()


class ExplosionSound(Particle):

    def __init__(self, level, position, intensity):
        super().__init__(level)
        self.box.worldPosition = position.copy()
        sound_command = {"label": "SOUND_EFFECT", "content": ("EXPLODE_{}".format(intensity), self.box, 0.5, 1.0)}
        self.level.commands.append(sound_command)

    def add_box(self):
        return self.level.own.scene.addObject("sound_hook", self.level.own, 0)

    def process(self):
        if self.timer > 1.0:
            self.ended = True
        else:
            self.timer += 0.001


class LargeBlast(AnimatedParticle):

    def __init__(self, level, growth, position):
        super().__init__(level)
        self.max_sub_frame = 4

        self.grow = 1.002 * growth
        s = 0.013

        self.up_force = mathutils.Vector([random.uniform(-s, s), random.uniform(-s, s), s * 3.0])
        self.down_force = mathutils.Vector([0.0, 0.0, -0.01])

        self.box.worldPosition = position.copy()

    def get_mesh_name(self):

        meshes = ["bang_1", "bang_3", "explosion_1"]
        return random.choice(meshes)

    def process(self):

        if self.timer >= 1.0:
            self.ended = True

        else:
            self.timer += 0.01
            c = 1.0 - self.timer
            c = c * c

            a = 1.0
            self.box.color = [c, c, c, a]

            up_force = self.up_force.lerp(self.down_force, self.timer)

            self.box.worldPosition += up_force
            scale = (1.0 * self.grow) * self.timer

            self.box.localScale = [scale, scale, scale]


class DirtBlast(Particle):

    def __init__(self, level, growth, position):
        super().__init__(level)

        self.grow = 1.002 * growth

        s = 0.05
        self.up_force = mathutils.Vector([random.uniform(-s, s), random.uniform(-s, s), s * 1.0])
        self.down_force = mathutils.Vector([0.0, 0.0, -0.05])

        self.box.worldPosition = position.copy()
        self.box.color = mathutils.Vector(self.level.world_dict["dirt_color"]) * 0.5

    def add_box(self):
        mesh = "{}.{}".format("dirt_1", str(random.randint(1, 8)).zfill(3))
        return self.level.own.scene.addObject(mesh, self.level.own, 0)

    def process(self):

        if self.timer >= 1.0:
            self.ended = True

        else:
            self.timer += 0.008
            self.box.color[3] = 1.0 - (self.timer * 0.5)

            up_force = self.up_force.lerp(self.down_force, self.timer)
            self.box.worldPosition += up_force
            scale = (1.0 * self.grow) * self.timer

            self.box.localScale = [scale, scale, scale]


class LargeSmoke(AnimatedParticle):

    def __init__(self, level, growth, position, delay=0):
        super().__init__(level)
        self.max_sub_frame = 24

        self.grow = 1.002 * growth
        s = 0.013

        self.up_force = mathutils.Vector([random.uniform(-s, s), random.uniform(-s, s), s * 3.0])
        self.down_force = mathutils.Vector([0.0, 0.0, -0.01])

        self.box.worldPosition = position.copy()
        self.delay = delay

    def get_mesh_name(self):
        return "bubble_smoke"

    def process(self):

        if self.delay > 0:
            self.box.color = [0.0, 0.0, 0.0, 0.0]
            self.delay -= 1

        else:
            if self.timer >= 1.0:
                self.ended = True

            else:
                self.timer += 0.008
                c = 1.0 - self.timer
                a = 1.0 - self.timer
                a = a * a

                self.box.color = [c, c, c, a]

                up_force = self.up_force.lerp(self.down_force, self.timer)

                self.box.worldPosition += up_force
                scale = (1.0 * self.grow) * self.timer

                self.box.localScale = [scale, scale, scale]


class SmallBlast(AnimatedParticle):

    def __init__(self, level, growth, position):
        super().__init__(level)
        self.max_sub_frame = 4
        self.grow = 1.002 * growth
        s = 0.013
        self.up_force = mathutils.Vector([random.uniform(-s, s), random.uniform(-s, s), s * 3.0])
        self.position = position
        self.box.worldPosition = position.copy()

    def get_mesh_name(self):
        return "bang_2"

    def process(self):

        if self.timer >= 1.0:
            self.ended = True

        else:
            self.timer += 0.02
            c = 1.0 - self.timer
            a = 1.0
            a = a * a

            self.box.color = [c, c, c, a]

            up_force = self.up_force * (0.9999 * self.timer)
            self.box.worldPosition += up_force
            scale = (1.0 * self.grow) * self.timer

            self.box.localScale = [scale, scale, scale]


class ScorchMark(Particle):

    def __init__(self, level, position, scale, normal):
        super().__init__(level)
        self.box.worldPosition = position
        self.box.alignAxisToVect(normal, 2, 1.0)
        self.scale = scale
        self.grow_timer = 0.0
        self.color = mathutils.Vector(self.level.world_dict["dirt_color"]) * 0.5
        self.box.color = self.color

    def process(self):

        if self.grow_timer < 1.0:
            self.grow_timer += 0.05
            s = self.scale * self.grow_timer
            self.box.localScale = [s, s, s]
        else:
            if self.timer < 1.0:
                self.timer += 0.001
                self.box.color[3] = 1.0 - (self.timer * 0.5)
            else:
                self.ended = True

    def add_box(self):
        mesh = "{}.{}".format("ground_hit", str(random.randint(1, 8)).zfill(3))
        return self.level.own.scene.addObject(mesh, self.level.own, 0)


class SmallSmoke(AnimatedParticle):

    def __init__(self, level, growth, position, delay=0):
        super().__init__(level)
        self.max_sub_frame = 24
        self.grow = 1.002 * growth
        self.up_force = mathutils.Vector([0.0, 0.0, 0.01])
        self.position = position
        self.box.worldPosition = position.copy()
        self.delay = delay

    def get_mesh_name(self):
        return "bubble_smoke"

    def process(self):

        if self.delay > 0:
            self.box.color = [0.0, 0.0, 0.0, 0.0]
            self.delay -= 1

        else:
            if self.timer >= 1.0:
                self.ended = True

            else:
                self.timer += 0.01
                c = (1.0 - (self.timer * 0.5)) + 0.75
                a = (1.0 - self.timer) * 0.5
                self.box.color = [c, c, c, a]
                up_force = self.up_force * (0.9999 * self.timer)
                self.box.worldPosition += up_force
                scale = (1.0 * self.grow) * self.timer

                self.box.localScale = [scale, scale, scale]


class BulletFlash(Particle):
    def __init__(self, level, weapon, delay=0):
        self.weapon = weapon


        self.hook = self.weapon.emitter

        super().__init__(level)

        self.box.setParent(self.hook)

        self.sound = self.weapon.sound
        self.color = [1.0, 1.0, 1.0]
        self.scale = 0.5 + min(6.0, self.weapon.rating * 0.2)
        self.delay = delay
        self.reduction = 0.23

        rapid_fire = ["QUICK", "RAPID"]

        if self.weapon.flag not in rapid_fire:
            self.reduction = 0.05

        self.place_particle()
        SmallSmoke(self.level, self.scale, self.box.worldPosition.copy())

    def play_sound(self):
        if self.sound:
            sound_command = {"label": "SOUND_EFFECT",
                             "content": (self.sound, self.box, 1.0, 1.0)}
            self.level.commands.append(sound_command)
            self.sound = None

    def add_box(self):
        bullet_flash = "gun_flash.{}".format(str(random.randint(1, 4)).zfill(3))
        return self.level.own.scene.addObject(bullet_flash, self.level.own, 0)

    def place_particle(self):
        self.box.worldPosition = self.hook.worldPosition.copy()
        self.box.worldOrientation = self.hook.worldOrientation
        self.box.localScale.y = (random.uniform(1.0, 1.5)) * self.scale
        self.box.localScale.x = self.scale
        self.box.localScale.z = self.scale

    def process(self):
        r, g, b = self.color

        if self.delay > 0:
            self.delay -= 1
            color = 0.0
        else:
            self.play_sound()
            self.timer += self.reduction
            color = 1.0 - self.timer

        self.box.color = [r * color, g * color, b * color, 1.0]

        if self.timer >= 0.5:
            bullet_flash = "after_flash.{}".format(str(random.randint(1, 4)).zfill(3))
            self.box.replaceMesh(bullet_flash)

        if self.timer >= 1.0:
            self.ended = True


class InfantryBullet(Particle):
    def __init__(self, level, target_position, weapon, origin):
        super().__init__(level)

        self.level = level
        self.weapon = weapon
        self.effect = self.weapon.effect

        effect_details = infantry_bullet_dict.get(self.effect)
        if not effect_details:
            self.ended = True
            print("no details for {}".format(self.effect))

        for i in range(effect_details["instances"]):
            InfantryBulletStreak(self.level, origin, target_position, self.effect, delay=8 * i)
            BulletHitGround(self.level, list(target_position), delay=8 * i)

        self.ended = True


class InfantryBulletStreak(Particle):
    def __init__(self, level, position, target, effect, delay=0):
        super().__init__(level)

        self.position = position
        self.target = target
        self.effect = effect
        self.delay = delay
        self.sound = "I_{}".format(self.effect)

        effect_details = infantry_bullet_dict.get(self.effect)
        self.color = effect_details["color"]
        if not self.color:
            self.box.visible = False
        self.place_particle()

    def play_sound(self):
        if self.sound:
            sound_command = {"label": "SOUND_EFFECT",
                             "content": (self.sound, self.box, 0.5, 1.0)}
            self.level.commands.append(sound_command)
            self.sound = None

    def add_box(self):
        return self.level.own.scene.addObject("bullet_streak", self.level.own, 0)

    def place_particle(self):

        position = mathutils.Vector(self.position)
        self.box.worldPosition = position

        if self.color:
            target = mathutils.Vector(self.target)

            target_vector = target - position
            self.box.worldOrientation = target_vector.to_track_quat("Y", "Z").to_matrix().to_3x3()
            self.box.localScale.y = target_vector.length

    def process(self):

        if self.delay > 0:
            self.delay -= 1
            color = 0.0
        else:
            self.play_sound()
            self.timer += 0.4
            color = 1.0 - self.timer

        if self.color:
            r, g, b = self.color
            self.box.color = [r * color, g * color, b * color, 1.0]

        if self.timer >= 1.0:
            self.ended = True


class BulletHitGround(Particle):
    def __init__(self, level, location, delay=0):
        super().__init__(level)

        self.level = level
        self.location = location
        self.delay = delay

        tile = self.level.get_tile(self.location)
        if tile:
            height = tile["height"]
            variance = 0.5
            random_vector = mathutils.Vector(
                [random.uniform(-variance, variance), random.uniform(-variance, variance), 0.0])
            position = mathutils.Vector(self.location).to_3d()
            position.z = height
            position += random_vector
            SmallSmoke(self.level, 0.8, position)

        self.ended = True


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
            position = mathutils.Vector(location).to_3d()

        self.box.worldPosition = position
        sound_command = {"label": "SOUND_EFFECT", "content": ("I_GRENADE", self.box, 0.5, 1.0)}
        self.level.commands.append(sound_command)

    def add_box(self):
        return self.level.own.scene.addObject("dummy_explosion", self.level.own, 0)

    def process(self):

        if self.timer >= 1.0:
            self.ended = True
        else:
            self.expansion = max(0.0001, self.expansion * self.fall_off)

            self.timer += self.expansion
            color = bgeutils.smoothstep(1.0 - self.timer)
            self.box.color = [color, color * color, 0.0, 1.0]

            self.box.localScale = self.start_scale.lerp(self.end_scale, self.timer)
