class BaseRole(object):
    """Base class for all roles.

    This class is the base class for all roles. It provides the basic
    functionality for all roles. It is not intended to be instantiated
    directly.
    """

    shortname = 'base'

    def __init__(self, config):
        self.config = config

    def __repr__(self):
        return f"{self.__class__.__name__}({self.config})"

    def start(self):
        """Start the role.

        This method starts the role.
        """
        pass