import sys
import inspect
import socket
from loguru import logger
from .role import *
from .input import *


class AgentConfig:

    def __init__(self, name: str, roles: list, policy: dict = {}, *args, **kwargs):
        self.name = name
        self.roles = roles
        self.role_configs = {}

        # If a policy is provided on initialization, load it
        if policy:
            self.from_policy(policy)
        else:
            self.from_policy({})

    def from_policy(self, policy):
        """Loads the agent configuration from a policy obtained from
        the management server.

        Args:
            policy (dict): The policy to load
        """
        self.policy_revision = policy.get('revision', 0)
        self.policy_uuid = policy.get('uuid', '')
        self.role_configs = policy.get('role_configs', {})
        self.event_cache_key = policy.get(
            'event_cache_key', 'signature')  # Default to signature
        self.event_cache_ttl = policy.get(
            'event_cache_ttl', 30)*60  # Default to 30 minutes
        self.disable_event_cache_check = policy.get(
            'disable_event_cache_check', False)
        self.organization = policy.get('organization', '')
        self.health_check_interval = policy.get(
            'health_check_interval', 30)  # Default to 30 seconds
            

class Agent:

    def __init__(self, config):

        if config:
            self.config = AgentConfig(**config)
        else:
            self.config = AgentConfig(name='default', roles=[], policy={})

        self.event_cache = {}
        self.event_cache_key = 'signature'
        self.event_cache_ttl = 30  # Number of minutes an item should be in the event cache
        self.loaded_roles = {}
        self.loaded_inputs = {}
        self.warnings = []
        self.load_inputs()
        self.load_roles()
        self.health = {}


    @property
    def roles(self):
        return self.config.roles

    def host_ip(self):
        """Returns the host IP address.

        This method returns the host IP address.
        """
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            # doesn't even have to be reachable
            s.connect(('10.255.255.255', 1))
            IP = s.getsockname()[0]
        except Exception:
            IP = '127.0.0.1'
        finally:
            s.close()
        return IP

    def clear_event_cache(self):
        """Clears the event cache."""
        self.event_cache = {}

    def _load_classes(self, base_class):
        """Loads all classes from a module.

        This method loads all classes from a module.
        """

        # Load all classes from a module.
        return [r for r in
                inspect.getmembers(sys.modules[__name__], inspect.isclass)
                if issubclass(r[1], base_class) and r[1] != base_class
                ]

    def pair_agent(self):
        """Pairs the agent with the management server.

        This method pairs the agent with the management server.
        """
        # TODO: Implement pairing
        pass

    def heartbeat(self):
        """Sends a heartbeat to the management server.

        This method sends a heartbeat to the management server.
        """
        # TODO: Implement heartbeat
        pass

    def load_inputs(self):
        """Automatically loads all the inputs installed in to the agent library
        and instantiates them.  Configurations for each agent are loaded from
        the agent configuration file.
        """
        # Find all the inputs in the agent input library that have been subclassed
        inputs = self._load_classes(BaseInput)

        for name, _class in inputs:
            _shortname = name.lower()
            self.loaded_inputs[_shortname] = _class(_shortname, 'base', {})

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
            role_config = self.config.role_configs.get(
                f"{_class.shortname}_role_config", {})
            role_config={'test': 'test'}
            self.loaded_roles[_class.shortname] = _class(config=role_config)

        for name in self.config.roles:
            if name not in self.loaded_roles:
                self.warnings.append(
                    f"Role \"{name}\" not installed in agent library")

    def start_roles(self):
        """Starts all roles.

        This method starts all roles.
        """

        # Start all roles.
        for role in self.config.roles:
            pass

    def start_role(self, role):
        """Starts the specified role.

        This method starts the specified role.
        """

        # Start the role.
        pass
