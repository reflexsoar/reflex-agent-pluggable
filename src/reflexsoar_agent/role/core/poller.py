from reflexsoar_agent.role import BaseRole


class Poller(BaseRole):
    """Poller role.

    This class implements the poller role for the agent. It is
    responsible for managing the lifecycle of the elastic indices.
    """

    shortname = 'poller'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def main(self):
        conn = self.get_connection()
        if conn:
            inputs = conn.agent_get_inputs()
            if inputs:
                self.logger.info(
                    f"Starting pollers for {len(inputs)} inputs. "
                    f"Max Concurrent Inputs: {self.config['concurrent_inputs']}")
