import datetime


class InputTypes:

    BASE = "base"
    POLL = "poll"
    STREAM = "stream"
    LISTENER = "listener"
    INTEL = "intel"


input_types = InputTypes()


class BaseInput:

    alias = "base"
    config_fields = []

    def __init__(self, input_type: str, config: dict):
        self.type = input_type
        self.config = config
        self.last_run = None

    @classmethod
    def parse_config(self, config: dict):
        """Parse the input configuration.
        This method parses the input configuration and only returns the
        fields in the dict that are involved with configuring the input
        """
        return {k: v for k, v in config.items() if k in self.config_fields}

    def main(self):
        """Main loop.
        This method is the main loop for the input.
        """
        pass

    def run(self):
        """Start the input.
        This method starts the input.
        """
        self._running = True
        data = self.main()
        self.last_run = datetime.datetime.utcnow()
        self._running = False
        return data
