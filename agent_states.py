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
        self.agent.update_stats()
        self.agent.infantry_update()
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
        if self.agent.dead:
            return AgentDead

        if self.agent.movement.done:

            if not self.agent.destinations:
                return AgentIdle

            if self.agent.waiting:
                return AgentWaiting

    def process(self):
        self.agent.agent_targeter.update()
        self.agent.movement.update()

        if self.agent.movement.done:
            self.agent.navigation.update()



class AgentWaiting(AgentState):
    def __init__(self, agent):
        super().__init__(agent)

    def exit_check(self):

        if self.agent.dead:
            return AgentDead

        if self.count > 60:
            self.agent.waiting = False
            if self.agent.navigation.destination:
                return AgentMovement
            else:
                return AgentIdle

    def process(self):
        self.agent.agent_targeter.update()
        self.agent.movement.update()
        self.count += 1


class AgentIdle(AgentState):
    def __init__(self, agent):
        super().__init__(agent)

    def exit_check(self):

        if self.agent.dead:
            return AgentDead

        if self.agent.movement.done:
            if self.agent.destinations:
                return AgentMovement

            if self.agent.waiting:
                return AgentWaiting

            if self.agent.agent_targeter.set_target_id:
                return AgentCombat

    def process(self):

        self.agent.agent_targeter.update()

        if self.agent.movement.done:
            if self.agent.aim:
                self.agent.movement.set_aim()
                self.agent.aim = None

        self.agent.movement.update()


class AgentCombat(AgentState):
    def __init__(self, agent):
        super().__init__(agent)

    def exit_check(self):

        if self.agent.dead:
            return AgentDead

        if self.agent.movement.done:
            if not self.agent.agent_targeter.set_target_id:
                return AgentIdle

            if self.agent.destinations:
                return AgentMovement

            if self.agent.waiting:
                return AgentWaiting

    def process(self):

        self.agent.agent_targeter.update()

        if self.agent.movement.done:
            if self.agent.agent_targeter.set_target_id:
                self.agent.movement.target_enemy()

        self.agent.movement.update()


class AgentDead(AgentState):
    def __init__(self, agent):
        super().__init__(agent)

        # TODO set up all aspects of dying, remove visibility etc...

        self.agent.dismount_building()
