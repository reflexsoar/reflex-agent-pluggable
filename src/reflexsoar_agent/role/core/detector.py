from reflexsoar_agent.role import BaseRole

class Detector(BaseRole):
    """Runner role.

    This class implements the detector role for the agent. It is
    responsible for managing the lifecycle of the elastic indices.
    """

    shortname = 'detector'

    def __init__(self, config):
        super().__init__(config)

    def main(self):
        self.logger.info('DO SOMETHING DIFFERENT!')
