import time
from ...core.logging import logger
from multiprocessing import Process, Event, Manager


class RoleGuard(type):

    __SENTINEL = object()

    def __new__(mcs, name, bases, class_dict):
        private = {key for base in bases for key, value in vars(base).items() if callable(value) and mcs.__is_final(value)}
        if any(key in private for key in class_dict):
            raise TypeError('Cannot override final method')
        return super().__new__(mcs, name, bases, class_dict)

    @classmethod
    def __is_final(mcs, method):
        try:
            return method.__final is mcs.__SENTINEL
        except AttributeError:
            return False
    
    @classmethod
    def final(mcs, method):
        """Marks a method as final, preventing it from being overridden in subclasses"""
        method.__final = mcs.__SENTINEL
        return method


class BaseRole(Process,metaclass=RoleGuard):
    """Base class for all roles.

    This class is the base class for all roles. It provides the basic
    functionality for all roles. It is not intended to be instantiated
    directly.
    """

    shortname = 'base'

    def __init__(self, config, connections, agent=None, *args, **kwargs):
        """Initializes the role"""

        manager = Manager()
        
        self._running = manager.Value(bool, False)
        self.config = config
        self.connections = connections

        super().__init__(*args, **kwargs)

        if config:
            self.set_config(config)

        self.agent = agent
        self._should_stop = Event()
        self.logger = logger
        self.disable_run_loop = False

    def __repr__(self):
        """Returns a string representation of the role"""
        return f"{self.__class__.__name__}({self.config})"

    @RoleGuard.final
    def set_config(self, config):
        """
        Sets the configuration for the role. 
        """
        self.config = config
        if 'wait_interval' not in self.config:
            self.config['wait_interval'] = 5

    @RoleGuard.final
    def get_connection(self, name: str = 'default'):
        return self.connections.get(name)

    @RoleGuard.final
    def share_connection(self, connection):
        """Shares a connection to the managed connections for this role and other
        roles that share this BaseRole instance.

        Args:
            connection (Connection): The connection to add.
        """
        if connection.name not in self.connections and connection.name != "default":
            self.connections[connection.name] = connection

    @RoleGuard.final
    def unshare_connection(self, name):
        """Removes a connection from the managed connections for this role and other
        roles that share this BaseRole instance.

        Args:
            connection (Connection): The connection to remove.
        """
        if name in self.connections and name != "default":
            del self.connections[name]

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
            if self.disable_run_loop:
                self.main()
            else:
                while self._running:
                    # Force the role to break out of the running loop
                    if self._should_stop.is_set():
                        break

                    self.main()
                    time.sleep(self.config['wait_interval'])
        except KeyboardInterrupt:
            pass

    @RoleGuard.final
    def stop(self, from_self=False):
        self.logger.info(f"Stop of {self.shortname} requested")
        self._running.value = False
        self._should_stop.set()
        if not from_self:
            self.join()
