class BaseAction:

    def __init__(self):
        self.alias = "base_action"

    def run(self, *args, **kwargs):
        raise NotImplementedError
