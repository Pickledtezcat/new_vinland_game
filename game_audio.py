import bge
import aud

device = aud.device()
device.distance_model = aud.AUD_DISTANCE_MODEL_INVERSE_CLAMPED


class SoundEffect(object):
    def __init__(self, manager, sound_name, game_object, volume_scale, attenuation, loop):
        self.manager = manager
        self.sound_name = sound_name
        self.game_object = game_object
        self.volume_scale = volume_scale
        self.attenuation = attenuation
        self.loop = loop

        sound_path = bge.logic.expandPath("//sounds/")
        file_name = "{}{}.wav".format(sound_path, sound_name)

        if sound_name not in self.manager.buffered:
            self.manager.buffered[sound_name] = aud.Factory.buffer(aud.Factory(file_name))

        self.handle = self.play_handle()

    def play_handle(self):
        handle = device.play(self.manager.buffered[self.sound_name])
        handle.relative = False
        handle.loop_count = int(self.loop)
        handle.attenuation = self.attenuation

        return handle

    def stop(self):
        sound_ok = self.handle.status != aud.AUD_STATUS_INVALID
        if sound_ok:
            self.handle.stop()

    def update(self):

        object_ok = not self.game_object.invalid
        sound_ok = self.handle.status != aud.AUD_STATUS_INVALID

        if object_ok and sound_ok:
            try:
                profile = bge.logic.globalDict["profiles"][bge.logic.globalDict["active_profile"]]
                self.handle.volume = profile['volume'] * self.volume_scale
                self.handle.location = self.game_object.worldPosition.copy()
                self.handle.orientation = self.game_object.worldOrientation.copy().to_quaternion()
            except:
                print("problem with {}".format(self.sound_name))

        return sound_ok


class Audio(object):
    def __init__(self, manager):
        self.manager = manager
        self.buffered = {}
        self.sound_effects = []
        self.scene = self.manager.scene
        self.camera = self.manager.listener
        self.music = None

    def sound_effect(self, sound_name, game_object, loop=0, volume_scale=1.0, attenuation=None):
        sound_effect = None
        if isinstance(game_object, bge.types.KX_GameObject):

            if not game_object.invalid:
                sound_effect = SoundEffect(self, sound_name, game_object, volume_scale, attenuation, loop)
                self.sound_effects.append(sound_effect)

        if sound_effect:
            return sound_effect.handle

    def update(self):

        device.listener_location = self.camera.worldPosition.copy()
        device.listener_orientation = self.camera.worldOrientation.copy().to_quaternion()

        next_generation = []

        for sound_effect in self.sound_effects:

            status = sound_effect.update()
            if status:
                next_generation.append(sound_effect)
            else:
                sound_effect.stop()

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
