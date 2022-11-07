"""Defines """
import os
import sys
import json
import inspect
import socket
from platformdirs import user_data_dir
from loguru import logger
from .role import *
from .input import *
from .core.errors import ConsoleAlreadyPaired


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
        self.paired_consoles = policy.get('paired_consoles', {})

    def add_paired_console(self, url: str, access_token: str):
        """Adds a paired console to the agent configuration.

        This method adds a paired console to the agent configuration.
        """
        if url not in self.config.paired_consoles:
            self.config.paired_consoles[url] = {'access_token': access_token}
        else:
            raise ConsoleAlreadyPaired(
                f"Console {url} is already paired with this agent.")


class Agent:

    def __init__(self, config: dict = {}, peristent_config_path: str = None):

        
        # If the agent is told to load the persistent configuration from a 
        # different path, load it, otherwise load the default persistent from
        # the users home directory.
        if peristent_config_path:
            self.peristent_config_path = peristent_config_path
        else:
            self.peristent_config_path = user_data_dir('reflexsoar-agent', 'reflexsoar')

        # Load the provided configuration or the persistent configuration.
        if config:
            self.config = AgentConfig(**config)
        else:
            if not self.load_persistent_config():
                self.config = AgentConfig(name='default', roles=[], policy={})

        self.loaded_roles = {}
        self.loaded_inputs = {}
        self.health = {}
        self.warnings = []

        # Load all available inputs and roles
        self.load_inputs()
        self.load_roles()

    def set_config(self, config: dict) -> None:
        """Sets the agent configuration.

        This method sets the agent configuration.

        Args:
            config (dict): The agent configuration.
        """
        self.config = AgentConfig(**config)

    @property
    def roles(self) -> list:
        return self.config.roles

    def host_ip(self) -> str:
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

    def load_persistent_config(self) -> bool:
        """Loads the persistent configuration.

        This method loads the persistent configuration.

        Returns:
            bool: True if the persistent configuration was loaded, False otherwise.
        """
        try:
            name = 'perisistent-config.json'
            _file = os.path.join(self.peristent_config_path, name)
            if os.path.exists(_file):
                with open(_file, 'r', encoding="utf-8") as f:
                    self.set_config(json.load(f))
                    return True
        except Exception as e:
            logger.error(f'Failed to load persistent config: {e}')
            return False

    def save_persistent_config(self) -> bool:
        """Saves the persistent configuration.

        This method saves the persistent configuration.

        Returns:
            bool: True if the persistent configuration was saved, False otherwise.
        """
        # Set the name of the persistent configuration file.
        name = 'perisistent-config.json'

        try:
            # Create the directory if it doesn't exist.
            if not os.path.exists(self.peristent_config_path):
                os.makedirs(self.peristent_config_path)

            # Write the persistent configuration file.
            _file = os.path.join(self.peristent_config_path, name)
            with open(_file, 'w', encoding="utf-8") as f:
                json.dump(self.config.__dict__, f)
            return True
        except Exception as e:
            logger.error(f'Failed to save persistent config: {e}')
            return False

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

    def pair_agent(self, console_url: str, access_token: str) -> bool:
        """Pairs the agent with the management server.

        This method pairs the agent with the management server.
        """
        # TODO: Implement pairing
        self.config.add_paired_console(console_url, access_token)
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
            role_config = {'test': 'test'}
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


def cli():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--pair', action='store_true',
                        help='Pair the agent with the management server')
    args = parser.parse_args()
    if args.pair:
        print("PAIRING")
