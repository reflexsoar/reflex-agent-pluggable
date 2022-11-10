from reflexsoar_agent.role import BaseRole


class ILM(BaseRole):
    """ILM role.

    This class implements the ILM role for the agent. It is
    responsible for managing the lifecycle of the elastic indices.
    """

    shortname = 'ilm'

    def __init__(self, config):
        super().__init__(config)
