from reflexsoar_agent.role import BaseRole

class Poller(BaseRole):
    """Poller role.

    This class implements the poller role for the agent. It is
    responsible for managing the lifecycle of the elastic indices.
    """

    shortname = 'poller'

    def __init__(self, config):
        super().__init__(config)
