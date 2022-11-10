from reflexsoar_agent.input import BaseInput


class Elasticsearch(BaseInput):

    def __init__(self, alias: str, input_type: str, config: dict):
        super().__init__(alias, input_type, config)

    def run(self):
        raise NotImplementedError
