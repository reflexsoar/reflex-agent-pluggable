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

        #self._manager = Manager()
        self._running = Manager().Value(bool, False)

        super().__init__(*args, **kwargs)

        if config:
            self.config = config
        else:
            self.config = {}

        self.agent = agent
        self._should_stop = Event()
        self.logger = logger

    def __repr__(self):
        """Returns a string representation of the role"""
        return f"{self.__class__.__name__}({self.config})"

    def main(self):
        """The main method for the role. This function performs all the work
        of the role when triggered to do so by the run method.  It should 
        periodically check the should_exit event to determine if it should
        exit if running in a forever loop.
        """
        self.logger.info(f"Hello World from {self.shortname}!")
        #self.logger.warning(f"Warning from {self.shortname}!")
        #self.logger.error(f"Error from {self.shortname}!")
        #self.logger.debug(f"Debug from {self.shortname}!")

    def run(self):
        """Runs the role"""
        self.logger.info(f"Starting {self.shortname} role")
        while self._running:

            # Force the role to break out of the running loop
            if self._should_stop.is_set():
                break

            self.main()
            time.sleep(5)

    def stop(self):
        self.logger.info(f"Stop of {self.shortname} requested")
        self._running.value = False
        self._should_stop.set()
        self.join()
