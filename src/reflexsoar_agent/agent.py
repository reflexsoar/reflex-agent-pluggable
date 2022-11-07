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
from .core.errors import ConsoleAlreadyPaired, ConsoleNotPaired


class AgentConfig:

    def __init__(self, name: str = "", roles: list = [], policy: dict = {}, *args, **kwargs):
        self.name = name
        self.roles = roles
        self.role_configs = {}

        # If a policy is provided on initialization, load it
        if policy:
            self.from_policy(policy)
        else:
            self.from_policy(kwargs)

    def json(self):
        return json.dumps(self.__dict__)

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
            'event_cache_ttl', 30)  # Default to 30 minutes
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
        
        if url not in self.paired_consoles:
            self.paired_consoles[url] = {
                'access_token': access_token
            }
        else:
            raise ConsoleAlreadyPaired(
                f"Console {url} is already paired with this agent.")

    def remove_paired_console(self, url: str):
        """Removes a paired console from the agent configuration.

        This method removes a paired console from the agent configuration.
        """
        if url in self.paired_consoles:
            del self.paired_consoles[url]
        else:
            raise ConsoleNotPaired(
                f"Console {url} is not paired with this agent.")
        

class Agent:

    def __init__(self, config: dict = {}, persistent_config_path: str = None):
        """Initializes the agent."""
       
        # If the agent is told to load the persistent configuration from a 
        # different path, load it, otherwise load the default persistent from
        # the users home directory.
        if persistent_config_path:
            self.persistent_config_path = persistent_config_path
        else:
            self.persistent_config_path = user_data_dir('reflexsoar-agent', 'reflexsoar')

        # Load the provided configuration or the persistent configuration.
        if config:
            logger.info('Loading provided configuration.')
            self.set_config(config)
            self.save_persistent_config()
        else:
            logger.info('Loading persistent configuration.')
            if not self.load_persistent_config():
                logger.warning(f"Failed to load persistent configuration. Using default configuration.")
                self.set_config({'name': 'default', 'roles': [], 'policy': {}})


        self.loaded_roles = {}
        self.loaded_inputs = {}
        self.health = {}
        self.warnings = []
        self.hostname = socket.gethostname()

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
        self.save_persistent_config()

    @property
    def roles(self) -> list:
        """Returns a list of roles assigned to this agent"""
        return self.config.roles

    @property
    def ip(self) -> str:
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
            name = 'persistent-config.json'
            _file = os.path.join(self.persistent_config_path, name)
            if os.path.exists(_file):
                with open(_file, 'r', encoding="utf-8") as f:
                    config = json.load(f)
                    self.set_config(config)
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
        name = 'persistent-config.json'

        try:
            # Create the directory if it doesn't exist.
            if not os.path.exists(self.persistent_config_path):
                os.makedirs(self.persistent_config_path)

            # Write the persistent configuration file.
            _file = os.path.join(self.persistent_config_path, name)
            with open(_file, 'w', encoding="utf-8") as f:
                json.dump(self.config.__dict__, f)
            return True
        except Exception as e:
            logger.error(f'Failed to save persistent config: {e}')
            return False

    def clear_persistent_config(self) -> bool:
        """Clears the persistent configuration"""

        name = 'persistent-config.json'
        _file = os.path.join(self.persistent_config_path, name)
        print(_file)
        if os.path.exists(_file):
            os.remove(_file)
            return True
        else:
            return False

    def fetch_config_from_console(self):
        """Fetches the agent configuration from the management server.

        This method fetches the agent configuration from the management server.
        """
        raise NotImplementedError

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

    def pair(self, console_url: str, access_token: str, **kwargs) -> bool:
        """Pairs the agent with the management server.

        This method pairs the agent with the management server.

        Args:
            console_url (str): The management server URL.
            access_token (str): The management server access token.
            kwargs (dict): Additional keyword arguments.

        Returns:
            bool: True if the agent was paired, False otherwise.
        """
        if not console_url:
            raise ValueError("Console URL is required.")
        if not access_token:
            raise ValueError("Access token is required.")

        agent_data = {
            "name": self.hostname,
            "ip_address": self.ip,
            "groups": kwargs.get('groups', []),
        }

        # TODO: Make call to API to pair agent

        self.config.add_paired_console(console_url, access_token)
        self.save_persistent_config()


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
    parser.add_argument('--start', action='store_true', help='Start the agent')
    parser.add_argument('--console', type=str, help='The management server URL')
    parser.add_argument('--token', type=str, help='The management server access token')
    parser.add_argument('--groups', type=str, help='Groups this agent should be automatically added to when paired')
    parser.add_argument('--clear-persistent-config', action='store_true')
    parser.add_argument('--reset-console-pairing', type=str, help="Will reset the pairing for the agent with the supplied console address")
    parser.add_argument('--view-config', action='store_true', help="View the agent configuration")
    args = parser.parse_args()

    agent = Agent()

    if args.view_config:
        logger.info(f"Configuration Preview: {agent.config.json()}")
        exit    

    if args.clear_persistent_config:
        agent.clear_persistent_config()
        exit()

    if args.reset_console_pairing:
        logger.info(f"Resetting console pairing for {args.reset_console_pairing}")
        logger.info(f"Config Before Reset: {agent.config.json()}")
        agent.config.remove_paired_console(args.reset_console_pairing)
        agent.save_persistent_config()
        exit()

    if args.pair:
        try:
            agent.pair(args.console, args.token, groups=args.groups)
        except Exception as e:
            logger.error(f"Error during pairing process. {e}")
            exit(1)
        print("PAIRING")

    if args.start:
        logger.info(f"On-Start Config: {agent.config.json()}")
