import bge
import aud

device = aud.device()
device.distance_model = aud.AUD_DISTANCE_MODEL_INVERSE_CLAMPED


class SoundEffect(object):
    def __init__(self, manager, handle, game_object, volume_scale):
        self.manager = manager
        self.handle = handle
        self.game_object = game_object
        self.volume_scale = volume_scale

    def update(self):
        try:
            profile = bge.logic.globalDict["profiles"][bge.logic.globalDict["active_profile"]]
            self.handle.volume = profile['volume'] * self.volume_scale
            self.handle.location = self.game_object.worldPosition.copy()
            self.handle.orientation = self.game_object.worldOrientation.copy().to_quaternion()
        except:
            print("sound problem with {} object".format(self.game_object.name))


class Audio(object):
    def __init__(self, manager):
        self.manager = manager
        self.buffered = {}
        self.sound_effects = []
        self.scene = self.manager.scene
        self.camera = self.manager.listener
        self.music = None

    def sound_effect(self, sound_name, game_object, loop=0, volume_scale=1.0, attenuation=None):

        sound_path = bge.logic.expandPath("//sounds/")
        file_name = "{}{}.wav".format(sound_path, sound_name)

        if sound_name not in self.buffered:
            self.buffered[sound_name] = aud.Factory.buffer(aud.Factory(file_name))

        if isinstance(game_object, bge.types.KX_GameObject):
            handle = device.play(self.buffered[sound_name])
            handle.relative = False
            handle.loop_count = int(loop)

            if not game_object.invalid:
                sound_effect = SoundEffect(self.manager, handle, game_object, volume_scale)
                self.sound_effects.append(sound_effect)

                if attenuation:
                    handle.attenuation = attenuation

            return handle

        return None

    def update(self):

        device.listener_location = self.camera.worldPosition.copy()
        device.listener_orientation = self.camera.worldOrientation.copy().to_quaternion()

        next_generation = []

        for sound_effect in self.sound_effects:
            if sound_effect.handle.status != aud.AUD_STATUS_INVALID:
                if sound_effect.game_object.invalid:
                    sound_effect.handle.stop()
                else:
                    sound_effect.update()
                    next_generation.append(sound_effect)

        self.sound_effects = next_generation

    def play_music(self, sound_name, vol=1.0):
        if self.music:
            self.music.stop()

        sound_path = bge.logic.expandPath("//music/")
        file_name = "{}{}.mp3".format(sound_path, sound_name)

        handle = device.play(aud.Factory(file_name))
        profile = bge.logic.globalDict["profiles"][bge.logic.globalDict["active_profile"]]
        handle.volume = profile['volume'] * vol
        handle.loop_count = -1
        self.music = handle
