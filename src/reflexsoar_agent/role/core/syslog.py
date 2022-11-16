from socketserver import BaseRequestHandler  # , UDPServer

from reflexsoar_agent.core.logging import logger
from reflexsoar_agent.role import BaseRole


class SyslogUDPHandler(BaseRequestHandler):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def handle(self):
        data = bytes.decode(self.request[0].strip(), encoding="utf-8")
        socket = self.request[1]  # noqa: F841
        if data:
            with open('syslog.log', 'a', encoding="utf-8") as f:
                f.write(data + '\n')
        logger.info(f"{self.client_address[0]} : {str(data)}")


class SyslogServer(BaseRole):
    """Runner role.

    This class implements the detector role for the agent. It is
    responsible for managing the lifecycle of the elastic indices.
    """

    shortname = 'syslog_server'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.disable_run_loop = True

    def main(self):
        logger.info('Syslog hit different tho!')
        # try:
        #     server = UDPServer(("0.0.0.0", 514), SyslogUDPHandler)
        #     server.serve_forever(poll_interval=0.5)
        # except (IOError, SystemExit):
        #     raise
        # except KeyboardInterrupt:
        #     pass
