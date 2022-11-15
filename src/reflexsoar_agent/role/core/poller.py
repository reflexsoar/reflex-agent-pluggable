import datetime

from reflexsoar_agent.core.logging import logger
from reflexsoar_agent.core.management import ManagementConnection
from reflexsoar_agent.role import BaseRole


class Poller(BaseRole):
    """Poller role.

    This class implements the poller role for the agent. It is
    responsible for managing the lifecycle of the elastic indices.
    """

    shortname = 'poller'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.load_inputs()
        self.configured_inputs = {}

    def configure_input(self, alias, input_module, config, credential):
        config = input_module.parse_config(config)
        configured_input = input_module(config=config, credentials=credential)
        self.configured_inputs[alias] = configured_input

    def fetch_inputs(self):
        """Returns inputs the input that has not run in the longest time
        to the top of the list.
        """
        unrun_inputs = [i for i in self.configured_inputs.values()
                        if i.last_run is None]
        if len(unrun_inputs) > 0:
            for _input in unrun_inputs:
                if _input.last_run is None:
                    yield _input
        else:
            inputs_sorted = sorted([i for i in self.configured_inputs.values(
            ) if i.last_run is not None], key=lambda x: x.last_run)
            yield self.configured_inputs[inputs_sorted[0]]

    def main(self):

        conn2 = ManagementConnection('http://127.0.0.1:5000', api_key='', name='test')
        conn = self.get_connection()
        self.event_manager.initialize(conn=conn2)

        if conn:

            # Fetch all the inputs
            inputs = conn.agent_get_inputs()
            if inputs:
                # Load all the inputs that agent is configured to run
                logger.info("Loading and configuring inputs...")
                for _input in inputs:
                    if _input['plugin'].lower() not in self.configured_inputs:
                        input_alias = _input['plugin'].lower()
                        input_uuid = _input['uuid']
                        input_credentials = conn.agent_get_input_credentials(
                            _input['credential'])
                        input_module = self.loaded_inputs.get(input_alias)
                        self.configure_input(input_uuid, input_module,
                                             _input['config'], input_credentials)

                # Check to see if the input has been removed from the agent
                input_uuids = [i['uuid'].lower() for i in inputs]
                for uuid in self.configured_inputs:
                    if uuid not in input_uuids:
                        del self.configured_inputs[uuid]
            else:
                logger.info("No inputs configured for this agent.")
                self.configured_inputs = {}

            # Run the inputs
            # inputs_run = 0
            # running_inputs = []
            for _input in self.fetch_inputs():
                events = _input.run()
                _input.last_run = datetime.datetime.utcnow()
                self.event_manager.prepare_events(*events)

        logger.info(f"{self.configured_inputs}")
