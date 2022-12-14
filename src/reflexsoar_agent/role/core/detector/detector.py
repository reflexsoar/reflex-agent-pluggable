from reflexsoar_agent.core.logging import logger
from reflexsoar_agent.role import BaseRole


class Detector(BaseRole):
    """Runner role.

    This class implements the detector role for the agent. It is
    responsible for managing the lifecycle of the elastic indices.
    """

    shortname = 'detector'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def main(self):

        # Load all the detections this agent should run
        conn = self.get_connection()
        detections = conn.agent_get_detections()
        rules = []
        if detections:
            rules = detections['detections']
            logger.info(f"Loaded {len(rules)} detections")

        if rules:
            for rule in rules:
                print(rule)

        # Spawn a thread for each detection up to MAX_CONCURRENT_DETECTIONS
        # make anything MAX_CONCURRENT_DETECTIONS+1 wait until one finishes

        # If a detection is finished, spawn a new one from the queue

        # If there are no detections to be run and no detections running,
        # sleep for a bit and then check again
        logger.info('DO SOMETHING DIFFERENT!')
