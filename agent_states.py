import bge


class AgentState(object):

    def __init__(self, agent):
        self.agent = agent
        self.name = type(self).__name__
        self.transition = None

    def end(self):
        pass

    def update(self):
        exit_check = self.exit_check()
        if exit_check:
            self.transition = exit_check
        else:
            self.process()

    def exit_check(self):
        return False

    def process(self):
        self.agent.movement.update()


class VehicleStartUp(AgentState):

    def __init__(self, agent):
        super().__init__(agent)
        self.agent.set_position()

        self.transition = AgentMovement


class AgentMovement(AgentState):

    def __init__(self, agent):
        super().__init__(agent)

    def exit_check(self):
        return False

    def process(self):
        pass



