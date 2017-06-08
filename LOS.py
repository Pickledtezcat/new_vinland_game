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
            self.brush_dict[i] = bgeutils.create_brush(self.brush_size, inner, [0, 0, 255], outer=outer, smooth=True)

        self.non_brush_dict = {}
        for i in range(3, 8):
            outer = max(19, 6 * i)
            self.non_brush_dict[i] = bgeutils.create_brush(self.brush_size, 0, [0, 0, 255], outer=outer, smooth=True)

        self.player_pixel = bgeutils.create_brush(1, 1, [0, 255, 0])
        self.enemy_pixel = bgeutils.create_brush(1, 1, [255, 0, 0])

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

    def do_paint(self, paint_dict):

        self.reload_canvas()

        for paint_key in paint_dict:
            agent = paint_dict[paint_key]
            enemy = agent["enemy"]
            distance = agent["distance"]
            knocked_out = agent["knocked_out"]
            x, y = agent["location"]

            bx = x - int(self.brush_size * 0.5)
            by = y - int(self.brush_size * 0.5)

            if enemy:
                agent_brush = self.enemy_pixel
            else:
                agent_brush = self.player_pixel

            if distance > 0:
                # TODO can set non visibility for player agents, for example knocked out tanks

                if not knocked_out:
                    vision_brush = self.brush_dict[distance]
                else:
                    vision_brush = self.non_brush_dict[distance]
                self.canvas.source.plot(vision_brush, self.brush_size, self.brush_size, bx, by,
                                        bge.texture.IMB_BLEND_LIGHTEN)
            self.canvas.source.plot(agent_brush, 1, 1, x, y, bge.texture.IMB_BLEND_LIGHTEN)

        self.canvas.refresh(True)
