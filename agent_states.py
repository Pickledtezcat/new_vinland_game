import bge


class AgentState(object):

    def __init__(self, agent):
        self.agent = agent
        self.name = type(self).__name__
        self.transition = None
        self.count = 0

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
        pass


class AgentStartUp(AgentState):

    def __init__(self, agent):
        super().__init__(agent)
        self.agent.set_position()

        self.transition = AgentIdle


class AgentMovement(AgentState):

    def __init__(self, agent):
        super().__init__(agent)
        self.agent.navigation.update()

    def exit_check(self):
        if self.agent.movement.done:

            if not self.agent.destinations:
                return AgentIdle

            if self.agent.waiting:
                return AgentWaiting

    def process(self):
        self.agent.agent_targeter.update()
        self.agent.animator.update()
        self.agent.movement.update()

        if self.agent.movement.done:
            self.agent.navigation.update()


class AgentWaiting(AgentState):
    def __init__(self, agent):
        super().__init__(agent)

    def exit_check(self):
        if self.count > 360:
            return AgentIdle

    def process(self):
        self.agent.agent_targeter.update()
        self.agent.animator.update()

        self.agent.movement.update()
        self.count += 1


class AgentIdle(AgentState):
    def __init__(self, agent):
        super().__init__(agent)

    def exit_check(self):

        if self.agent.movement.done:
            if self.agent.destinations:
                return AgentMovement

            if self.agent.waiting:
                return AgentWaiting

    def process(self):

        self.agent.agent_targeter.update()
        self.agent.animator.update()

        if self.agent.movement.done:
            if self.agent.aim:
                self.agent.movement.set_aim()
                self.agent.aim = None
        else:
            self.agent.movement.update()
