from multiprocessing import Process, Event


class BaseRole(Process):
    """Base class for all roles.

    This class is the base class for all roles. It provides the basic
    functionality for all roles. It is not intended to be instantiated
    directly.
    """

    shortname = 'base'

    def __init__(self, config, agent=None, log_level='INFO', *args, **kwargs):
        """Initializes the role"""

        
        super().__init__(*args, **kwargs)
       
        if config:
            self.config = config
        else:
            self.config = {}

        self.running = False
        self.should_exit = Event()
        self.agent = agent
        self.log_level = log_level

    def exit(self):
        """Shuts down the role"""
        self.should_exit.set()

    def __repr__(self):
        """Returns a string representation of the role"""
        return f"{self.__class__.__name__}({self.config})"

    def run(self):
        """Runs the role"""
        self.running = True
        self.main()
        self.running = False