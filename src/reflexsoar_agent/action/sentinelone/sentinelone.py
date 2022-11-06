from reflexsoar_agent.action import BaseAction

class SentinelOneIsolateHost(BaseAction):
    """SentinelOne Isolate Host action
    """

    def __init__(self):
        self.alias = 'sentinelone_isolate_host'

    def run(self, *args, **kwargs):
        raise NotImplementedError