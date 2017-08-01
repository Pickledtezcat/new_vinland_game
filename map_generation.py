import bge
import mathutils
import bgeutils
import random


class BaseMapGen(object):
    def __init__(self, level, loaded=False):
        self.level = level
        self.canvas_size = self.level.map_size
        self.ground = bgeutils.get_ob("map_object", self.level.scene.objects)
        self.normal_object = bgeutils.get_ob("normal_object", self.level.scene.objects)
        self.canvas = self.create_canvas(self.ground)
        self.normal = self.create_canvas(self.normal_object)

        if not loaded:
            self.generate_map()

    def create_canvas(self, game_object):
        canvas_size = self.canvas_size

        tex = bge.texture.Texture(game_object, 0, 0)
        tex.source = bge.texture.ImageBuff(color=0)

        tex.source.load(b'\x00\x00\x00' * (canvas_size * canvas_size), canvas_size, canvas_size)

        return tex

    def generate_map(self):

        def grayscale(lowest_value, highest_value, color_value):
            color = (color_value - lowest_value) / (highest_value - lowest_value)
            color_int = int(255 * color)

            return color_int

        mathutils.noise.seed_set(0)
        offset = random.randint(0, 255)

        highest = -1000.0
        lowest = 1000.0

        new_map = {}

        for x in range(self.canvas_size):
            for y in range(self.canvas_size):
                ## eggbox
                scale = 0.01
                position = mathutils.Vector([x * scale + offset, y * scale + offset, 0.0])

                #value = mathutils.noise.noise(position, mathutils.noise.types.VORONOI_F1)
                h = mathutils.noise.multi_fractal(position, 1.01, 120.0, 12, 1)
                #h1 = mathutils.noise.turbulence(position,12, 0, 1, 1.5, 0.5)
                #value = (h1 * h)

                h3 = mathutils.noise.hetero_terrain(position, 1.0, 1.0, 2, 1.0, 4)

                s4 = 0.1
                h4p = mathutils.Vector([x * s4 + offset, y * s4 + offset, 0.0])

                h4 = mathutils.noise.noise(h4p, mathutils.noise.types.VORONOI_F2F1) * -1.0

                s5 = 1.3
                h5p = mathutils.Vector([x * s5 + offset, y * s5 + offset, 0.0])
                h5 = mathutils.noise.noise(h5p, mathutils.noise.types.VORONOI_F1)

                h7 = h5 * (h * -1)

                h6 = h4 * h3

                ## craters
                value = h6 - (h * 5.0) - (h7 * 3.0)

                if value < lowest:
                    lowest = value
                if value > highest:
                    highest = value

                new_map[(x, y)] = value

        for map_key in new_map:
            value = int((grayscale(lowest, highest, new_map[map_key])) * 0.75)
            self.level.set_tile(map_key, "terrain", value)

    def paint_map(self):

        z_vector = mathutils.Vector([0.0, 0.0, 1.0])

        for map_key in self.level.map:
            tile = self.level.map[map_key]
            map_key = bgeutils.get_loc(map_key)
            x, y = map_key

            z1 = self.level.get_tile((x + 1, y), fallback=tile)["terrain"] - self.level.get_tile((x - 1, y), fallback=tile)["terrain"]
            z2 = self.level.get_tile((x, y + 1), fallback=tile)["terrain"] - self.level.get_tile((x, y - 1), fallback=tile)["terrain"]

            a = mathutils.Vector((1, 0, z1))
            b = mathutils.Vector((0, 1, z2))

            normal = b.cross(a)
            normal = normal.lerp(z_vector, 0.995)
            normal.normalize()

            r, g, b = [int(((n + 1.0) / 2.0) * 255.0) for n in list(normal)]
            pixel_brush = bgeutils.create_pixel([r, g, b, 255])
            self.normal.source.plot(pixel_brush, 1, 1, x, y, bge.texture.IMB_BLEND_MIX)

        for map_key in self.level.map:
            value = self.level.map[map_key]["terrain"]
            map_key = bgeutils.get_loc(map_key)
            x, y = map_key

            pixel_brush = bgeutils.create_pixel([value, value, value, 255])
            self.canvas.source.plot(pixel_brush, 1, 1, x, y, bge.texture.IMB_BLEND_LIGHTEN)

        self.normal.refresh(True)
        self.canvas.refresh(True)


