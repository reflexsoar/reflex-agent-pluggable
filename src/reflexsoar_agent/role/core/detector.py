from reflexsoar_agent.role import BaseRole
from reflexsoar_agent.core.management import build_http_connection

class Detector(BaseRole):
    """Runner role.

    This class implements the detector role for the agent. It is
    responsible for managing the lifecycle of the elastic indices.
    """

    shortname = 'detector'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def main(self):
        self.logger.info('DO SOMETHING DIFFERENT!')
        conn = build_http_connection('http://localhost:9200', 'secret', False, name='es-test')
        self.logger.info(conn)
