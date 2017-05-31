import bgeutils
import bge
import mathutils
import math

class VisionPaint(object):
    def __init__(self, level):
        self.level = level
        self.scene = self.level.scene
        self.ground = [ob for ob in self.scene.objects if ob.get("vision_object")][0]
        self.canvas_size = self.level.map_size
        self.brush_size = 64

        self.brush_dict = {}
        for i in range(3, 8):
            inner = 18
            outer = max(19, 6 * i)
            self.brush_dict[i] = self.create_brush(self.brush_size, inner, [0, 0, 255], outer=outer, smooth=True)

        self.player_pixel = self.create_brush(1, 1, [0, 255, 0])
        self.enemy_pixel = self.create_brush(1, 1, [255, 0, 0])

        self.canvas = self.create_canvas()
        self.set_infantry_texture()

    def set_infantry_texture(self):
        for texture_set in self.level.infantry_textures:
            texture_object = texture_set["owner"]
            texture_name = texture_set["name"]

            material_id = bge.texture.materialID(texture_object, "MA{}_mat".format(texture_name))
            object_texture = bge.texture.Texture(texture_object, material_id, textureObj=self.canvas)
            texture_set["saved"] = object_texture
            texture_set["saved"].refresh(False)

    def create_canvas(self):
        canvas_size = self.canvas_size

        tex = bge.texture.Texture(self.ground, 0, 0)
        tex.source = bge.texture.ImageBuff(color=0)

        tex.source.load(b'\x00\x00\x00' * (canvas_size * canvas_size), canvas_size, canvas_size)

        return tex

    def reload_canvas(self):
        canvas_size = self.canvas_size
        self.canvas.source.load(b'\x00\x00\x00' * (canvas_size * canvas_size), canvas_size, canvas_size)


    def create_brush(self, brush_size, radius, RGB, outer=0, smooth=False):

        brush_size = brush_size
        brush = bytearray(brush_size * brush_size * 4)
        center = mathutils.Vector([brush_size * 0.5, brush_size * 0.5])
        rgb = RGB
        half_rgb = [int(color * 0.5) for color in rgb]

        for x in range(brush_size):
            for y in range(brush_size):
                i = y * (brush_size * 4) + x * 4
                location = mathutils.Vector([x, y])
                target_vector = location - center
                length = target_vector.length

                if length == radius and smooth:
                    pixel = half_rgb
                elif length > radius:
                    if outer > 0 and length < outer:
                        pixel = half_rgb
                    else:
                        pixel = [0, 0, 0]
                else:
                    pixel = rgb

                brush[i] = pixel[0]
                brush[i + 1] = pixel[1]
                brush[i + 2] = pixel[2]
                brush[i + 3] = 255

        return brush

    def create_spy_brushes(self):

        directions_dict = {(-1, -1): None,
                           (-1, 0): None,
                           (-1, 1): None,
                           (0, 1): None,
                           (1, 1): None,
                           (1, 0): None,
                           (1, -1): None,
                           (0, -1): None}

        radius = 4
        spy = 12
        brush_size = self.brush_size
        rgb = [0, 0, 255]
        half_rgb = [int(color * 0.5) for color in rgb]
        center = mathutils.Vector([brush_size * 0.5, brush_size * 0.5])

        for key in directions_dict:

            brush = bytearray(brush_size * brush_size * 4)
            direction = mathutils.Vector(key)

            for x in range(brush_size):
                for y in range(brush_size):
                    i = y * (brush_size * 4) + x * 4
                    location = mathutils.Vector([x, y])
                    target_vector = location - center
                    length = target_vector.length

                    if length > 0.0:
                        angle = math.degrees(direction.angle(target_vector))
                    else:
                        angle = 0.0

                    if length > radius:
                        if length > spy:
                            pixel = [0, 0, 0]
                        else:
                            if angle < 30.0:
                                pixel = rgb
                            elif angle < 45:
                                pixel = half_rgb
                            else:
                                if length < radius + 2:
                                    pixel = half_rgb
                                else:
                                    pixel = [0, 0, 0]

                    else:
                        pixel = rgb

                    brush[i] = pixel[0]
                    brush[i + 1] = pixel[1]
                    brush[i + 2] = pixel[2]
                    brush[i + 3] = 255

            directions_dict[key] = brush

        return directions_dict

    def do_paint(self, paint_dict):

        self.reload_canvas()

        for paint_key in paint_dict:
            agent = paint_dict[paint_key]
            enemy = agent["enemy"]
            distance = agent["distance"]
            x, y = agent["location"]

            bx = x - int(self.brush_size * 0.5)
            by = y - int(self.brush_size * 0.5)

            if enemy:
                agent_brush = self.enemy_pixel
            else:
                agent_brush = self.player_pixel

            if distance > 0:
                vision_brush = self.brush_dict[distance]
                self.canvas.source.plot(vision_brush, self.brush_size, self.brush_size, bx, by,
                                        bge.texture.IMB_BLEND_LIGHTEN)
            self.canvas.source.plot(agent_brush, 1, 1, x, y, bge.texture.IMB_BLEND_LIGHTEN)

        self.canvas.refresh(True)
