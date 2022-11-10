class InputTypes:

    BASE = "base"
    POLL = "poll"
    STREAM = "stream"
    LISTENER = "listener"
    INTEL = "intel"


input_types = InputTypes()


class BaseInput:

    def __init__(self, alias: str, input_type: str, config: dict):
        self.alias = alias
        self.type = input_type
        self.config = config

    def __repr__(self):
        return f"{self.__class__.__name__}"

    def start(self):
        """Start the input.
        This method starts the input.
        """
        pass
