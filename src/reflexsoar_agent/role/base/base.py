import time
from ...core.logging import logger
from multiprocessing import Process, Event, Queue, Manager


class BaseRole(Process):
    """Base class for all roles.

    This class is the base class for all roles. It provides the basic
    functionality for all roles. It is not intended to be instantiated
    directly.
    """

    shortname = 'base'

    def __init__(self, config, agent=None, *args, **kwargs):
        """Initializes the role"""

        manager = Manager()
        self._running = manager.Value(bool, False)
        self.wait_interval = manager.Value(int, 5)
        self.config = manager.Value(dict, {})

        super().__init__(*args, **kwargs)

        if config:
            self.config = config

        self.agent = agent
        self._should_stop = Event()
        self.logger = logger

    def __repr__(self):
        """Returns a string representation of the role"""
        return f"{self.__class__.__name__}({self.config})"

    def set_config(self, config):
        self.config = config

    def main(self):
        """The main method for the role. This function performs all the work
        of the role when triggered to do so by the run method.  It should 
        periodically check the should_exit event to determine if it should
        exit if running in a forever loop.
        """
        self.logger.info(
            f"Hello World from {self.shortname}! Sleeping for {self.config['wait_interval']}")
        #self.logger.warning(f"Warning from {self.shortname}!")
        #self.logger.error(f"Error from {self.shortname}!")
        #self.logger.debug(f"Debug from {self.shortname}!")

    def run(self):
        """Runs the role"""
        try:
            self.logger.info(f"Starting {self.shortname} role")
            while self._running:

                # Force the role to break out of the running loop
                if self._should_stop.is_set():
                    break

                self.main()
                time.sleep(self.config['wait_interval'])
        except KeyboardInterrupt:
            pass

    def stop(self, from_self=False):
        self.logger.info(f"Stop of {self.shortname} requested")
        self._running.value = False
        self._should_stop.set()
        if not from_self:
            self.join()
