import bge
import mathutils
import bgeutils
import random


class BaseMapGen(object):
    def __init__(self, level):
        self.level = level
        self.canvas_size = self.level.map_size
        self.ground = bgeutils.get_ob("map_object", self.level.scene.objects)
        self.canvas = None

        self.canvas = self.create_canvas()
        self.generate_noise()

    def create_canvas(self):
        canvas_size = self.canvas_size

        tex = bge.texture.Texture(self.ground, 0, 0)
        tex.source = bge.texture.ImageBuff(color=0)

        tex.source.load(b'\x00\x00\x00' * (canvas_size * canvas_size), canvas_size, canvas_size)

        return tex

    def generate_noise(self):

        def grayscale(lowest, highest, color_value):
            color = (color_value - lowest) / (highest - lowest)
            color_int = int(255 * color)

            return color_int

        mathutils.noise.seed_set(0)
        offset = random.randint(0, 255)

        highest =  -1000.0
        lowest = 1000.0

        map = {}

        for x in range(self.canvas_size):
            for y in range(self.canvas_size):
                ## eggbox
                scale = 0.2
                position = mathutils.Vector([x * scale + offset, y * scale + offset, 0.0])
                value = mathutils.noise.noise(position, mathutils.noise.types.VORONOI_F1)

                if value < lowest:
                    lowest = value

                if value > highest:
                    highest = value

                map[(x, y)] = value

        for map_key in map:
            value = map[map_key]
            x, y = map_key

            v = grayscale(lowest, highest, value)
            pixel_brush = bgeutils.create_pixel([v, v, v, 255])
            self.canvas.source.plot(pixel_brush, 1, 1, x, y, bge.texture.IMB_BLEND_LIGHTEN)

        self.canvas.refresh(True)