import sys, inspect
from loguru import logger
from .role import *
from .input import *

class Agent:

    def __init__(self, config):
        self.config = config

        if self.config:
            self.__dict__.update({k: v for k, v in self.config.items()})

        self.loaded_roles = {}
        self.loaded_inputs = {}
        self.warnings = []
        self.load_inputs()
        self.load_roles()
        

    def _load_classes(self, base_class):
        """Loads all classes from a module.

        This method loads all classes from a module.
        """

        # Load all classes from a module.
        return [r for r in 
            inspect.getmembers(sys.modules[__name__], inspect.isclass)
            if issubclass(r[1], base_class) and r[1] != base_class
        ]

    def load_inputs(self):
        """Automatically loads all the inputs installed in to the agent library
        and instantiates them.  Configurations for each agent are loaded from
        the agent configuration file.
        """
        # Find all the inputs in the agent input library that have been subclassed
        inputs = self._load_classes(BaseInput)

        for name, _class in inputs:
            self.loaded_inputs[name] = _class(name.lower(), 'base', {})

    def load_roles(self):
        """Automatically loads all the roles installed in to the agent library
        and instantiates them.  Configurations for each agent are loaded from
        the agent configuration file.
        """

        # Find all the roles in the agent role library that have been subclassed
        # from the BaseRole class.
        roles = self._load_classes(BaseRole)

        # Instantiate each role and add it to the agent roles list.
        for name, _class in roles:
            _class.shortname
            role_config = self.config['role_configs'].get(f"{_class.shortname}_role_config", {})
            self.loaded_roles[_class.shortname] = _class(role_config)

        for name in self.roles:
            if name not in self.loaded_roles:
                self.warnings.append(f"Role \"{name}\" not installed in agent library")


    def start_roles(self):
        """Starts all roles.

        This method starts all roles.
        """

        # Start all roles.
        for role in self.roles:
            pass

    def start_role(self, role):
        """Starts the specified role.

        This method starts the specified role.
        """

        # Start the role.
        pass
