from reflexsoar_agent.role import BaseRole


class Runner(BaseRole):
    """Runner role.

    This class implements the runner role for the agent. It is
    responsible for managing the lifecycle of the elastic indices.
    """

    shortname = 'runner'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
