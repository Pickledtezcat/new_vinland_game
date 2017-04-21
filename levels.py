import bge
import user_interface


class Level(object):

    def __init__(self, manager):
        self.manager = manager
        self.user_interface = user_interface.UserInterface(manager)

    def terminate(self):
        self.user_interface.terminate()

    def update(self):
        self.user_interface.update()
