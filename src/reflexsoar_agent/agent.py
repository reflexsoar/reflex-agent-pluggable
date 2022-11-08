"""Defines """
import os
import sys
import json
import inspect
import socket
import argparse
from dotenv import load_dotenv
from platformdirs import user_data_dir
from .role import * # pylint: disable=wildcard-import,unused-wildcard-import
from .input import * # pylint: disable=wildcard-import,unused-wildcard-import
from .core.logging import logger, setup_logging
from .core.errors import ConsoleAlreadyPaired, ConsoleNotPaired
from .core.management import (
    ManagementConnection,
    get_management_connection
)
from .core.version import version_number

class AgentConfig: # pylint: disable=too-many-instance-attributes
    """Defines an AgentConfig object that stores configuration information for
    the Reflex Agent
    """

    def __init__(self, uuid: str = None, roles: list = None, policy: dict = None, **kwargs):
        """Initializes the AgentConfig object."""
        self.uuid = uuid
        self.roles = roles
        self.role_configs = {}
        self.console_info = {}
        setup_logging(init=True)

        # If a policy is provided on initialization, load it
        if policy:
            self.from_policy(policy)
        else:
            self.from_policy(kwargs)

    def json(self):
        """Returns the agent configuration as a JSON string."""
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
        self.health_check_interval = policy.get(
            'health_check_interval', 30)  # Default to 30 seconds
        self.console_info = policy.get('console_info', self.console_info)
        self.name = policy.get('name', socket.gethostname())

    def add_paired_console(self, url: str, access_token: str):
        """Adds a paired console to the agent configuration.

        This method adds a paired console to the agent configuration.
        """

        if self.console_info['url'] != url:
            self.console_info = {
                'access_token': access_token,
                'url': url
            }
        else:
            raise ConsoleAlreadyPaired(
                f"Console {url} is already paired with this agent.")

    def remove_paired_console(self, url: str):
        """Removes a paired console from the agent configuration.

        This method removes a paired console from the agent configuration.
        """
        if 'url' in self.console_info and self.console_info['url'] == url:
            self.console_info = {}
        else:
            raise ConsoleNotPaired(
                f"Console {url} is not paired with this agent.")

    def set_value(self, key: str, value: str) -> None:
        """Sets a configuration value.

        This method sets a configuration value.

        Args:
            key (str): The key to set.
            value (str): The value to set.
        """
        updateable_config_keys = [
            "roles", "event_cache_key", "event_cache_ttl", "health_check_interval"]
        if key in updateable_config_keys:
            if hasattr(self, key):
                if isinstance(getattr(self, key), list):
                    setattr(self, key, value.split(",")
                            if value not in [""] else [])
                if isinstance(getattr(self, key), int):
                    setattr(self, key, int(value))
                if isinstance(getattr(self, key), bool):
                    setattr(self, key, bool(value) if value else False)
                if isinstance(getattr(self, key), str):
                    setattr(self, key, value)
            else:
                raise KeyError(f"Key {key} does not exist in AgentConfig.")
        else:
            raise KeyError(f"Key {key} is not updateable.")


class Agent: # pylint: disable=too-many-instance-attributes
    """The Reflex Agent class. This class is the main entry point for the
    Reflex Agent. It is responsible for loading the configuration, loading
    roles and inputs, and starting the management connection."""

    def __init__(self, config: dict = None, persistent_config_path: str = None):
        """Initializes the agent."""

        # If the agent is told to load the persistent configuration from a
        # different path, load it, otherwise load the default persistent from
        # the users home directory.
        if persistent_config_path:
            self.persistent_config_path = persistent_config_path
        else:
            self.persistent_config_path = user_data_dir(
                'reflexsoar-agent', 'reflexsoar')

        # Load the provided configuration or the persistent configuration.
        if config:
            logger.info('Loading provided configuration.')
            self.set_config(config)
            self.save_persistent_config()
        else:
            logger.info('Loading persistent configuration.')
            if not self.load_persistent_config():
                logger.warning(
                    "Failed to load persistent configuration. Using default configuration.")
                self.set_config({})

        self.loaded_roles = {}
        self.loaded_inputs = {}
        self.event_cache = {}
        self.health = {}
        self.healthy = True
        self.warnings = []
        self.version_number = version_number

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
    def ip_address(self) -> str:
        """Returns the host ip_address address.

        This method returns the host ip_address address.
        """
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            # doesn't even have to be reachable
            sock.connect(('10.255.255.255', 1))
            ip_address = sock.getsockname()[0]
        except socket.error:
            ip_address = '127.0.0.1'
        finally:
            sock.close()
        return ip_address

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
                with open(_file, 'r', encoding="utf-8") as file_handle:
                    config = json.load(file_handle)
                    self.set_config(config)
                    return True
            else:
                raise FileNotFoundError(
                    f"Persistent configuration file {name} not found.")
        except (FileNotFoundError) as error:
            logger.error(f'Failed to load persistent config: {error}')
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
            with open(_file, 'w', encoding="utf-8") as file_handle:
                json.dump(self.config.__dict__, file_handle)
            return True
        except (FileNotFoundError) as error:
            logger.error(f'Failed to save persistent config: {error}')
            return False

    def clear_persistent_config(self) -> bool:
        """Clears the persistent configuration"""

        name = 'persistent-config.json'
        _file = os.path.join(self.persistent_config_path, name)
        print(_file)
        if os.path.exists(_file):
            os.remove(_file)
            return True
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

    def pair(self, console_url: str, access_token: str, ignore_tls: bool = False, **kwargs) -> bool:
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
            "name": self.config.name,
            "ip_address_address": self.ip_address,
            "groups": kwargs.get('groups', []),
        }

        # Check to see if the local config says this agent is already paired with the console
        # if it is throw an error
        if 'url' in self.config.console_info and self.config.console_info['url'] == console_url:
            raise ConsoleAlreadyPaired(
                f"Agent is already paired with {console_url}.")

        # Build a management connection to the pair the agent with
        mgmt_connection = ManagementConnection(
            console_url, access_token, ignore_tls=ignore_tls)

        # Call the pairing endpoint
        response = mgmt_connection.call_api('POST', 'agent', agent_data)
        if response.status_code == 200:

            # Parse the json respone data into a dictionary
            response_data = response.json()

            # Update the authorization header on the management connection
            mgmt_connection.update_header(
                'Authorization', f"Bearer {response_data['token']}")
            self.config.uuid = response_data['uuid']
            mgmt_connection.api_key = response_data['token']
            self.config.console_info = mgmt_connection.config
            self.save_persistent_config()
            self.heartbeat()
        else:
            raise ConsoleAlreadyPaired(
                f"Failed to pair agent: {response.text}")

    def heartbeat(self):
        """Sends a heartbeat to the management server.

        This method sends a heartbeat to the management server.
        """

        recoved = False

        data = {'healthy': self.healthy, 'health_issues': self.warnings,
                'recovered': recoved, 'version': self.version_number}

        # Check to see if a management connection has been established
        mgmt_connection = get_management_connection()

        if mgmt_connection is None:
            mgmt_connection = ManagementConnection(**self.config.console_info)

        if mgmt_connection:
            response = mgmt_connection.call_api(
                'POST', f'agent/heartbeat/{self.config.uuid}', data)
            if response.status_code == 200:
                logger.success(f"Sent heartbeat to {mgmt_connection.config['url']}")
            else:
                logger.error(f"Failed to send heartbeat to {mgmt_connection.config['url']}")

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
        for role in self.loaded_roles:
            self.loaded_roles[role].start()

    def start_role(self, role):
        """Starts the specified role.

        This method starts the specified role.
        """
        if role in self.loaded_roles:
            self.loaded_roles[role].start()
        

    def stop_role(self, role):
        """Stops the specified role.

        This method stops the specified role.
        """
        if role in self.loaded_roles:
            self.loaded_roles[role].stop()

    def stop_roles(self):
        """Stops all roles.

        This method stops all roles.
        """
        for role in self.loaded_roles:
            self.loaded_roles[role].stop()

# pylint disable=too-many-statements
def cli():
    """Defines a command line entry point for the agent script"""

    parser = argparse.ArgumentParser()
    parser.add_argument('--pair', action='store_true',
                        help='Pair the agent with the management server')
    parser.add_argument('--start', action='store_true', help='Start the agent')
    parser.add_argument('--console', type=str,
                        help='The management server URL')
    parser.add_argument('--token', type=str,
                        help='The management server access token')
    parser.add_argument(
        '--groups', type=str, help='Groups this agent should be automatically added to when paired')
    parser.add_argument('--clear-persistent-config', action='store_true')
    parser.add_argument('--reset-console-pairing', type=str,
                        help="""Will reset the pairing for the agent with the
                                supplied  console address""")
    parser.add_argument('--view-config', action='store_true',
                        help="View the agent configuration")
    parser.add_argument('--set-config-value', type=str,
                        help="""Set a configuration value.
                                Format: <key>:<value>.  If the target setting is
                                 a list provide each value separated
                                 by a comma""")
    parser.add_argument('--env-file', type=str,
                        help="The path to the .env file to load", default=None)
    parser.add_argument('--heartbeat', action="store_true",
                        help="Send a heartbeat to the management server")
    args = parser.parse_args()

    # Load the .env file if it exists
    load_dotenv(args.env_file)

    # Environmental variables can override command line arguments
    args.pair = args.pair or os.getenv('REFLEX_AGENT_PAIR_MODE')
    args.console = args.console or os.getenv('REFLEX_API_HOST')
    args.token = args.token or os.getenv('REFLEX_AGENT_PAIR_TOKEN')

    agent = Agent()

    if args.set_config_value:
        key, value = args.set_config_value.split(':')
        agent.config.set_value(key, value)
        agent.save_persistent_config()

    if args.view_config:
        logger.info("Configuration Preview:")
        print(json.dumps(agent.config.__dict__, indent=4))
        sys.exit()

    if args.clear_persistent_config:
        agent.clear_persistent_config()
        sys.exit()

    if args.reset_console_pairing:
        try:
            logger.info(
                f"Resetting console pairing for {args.reset_console_pairing}")
            agent.config.remove_paired_console(args.reset_console_pairing)
            agent.save_persistent_config()
        except (ConsoleNotPaired) as error:
            logger.error(
                f"Failed to reset console pairing for {args.reset_console_pairing}. {error}")
        sys.exit()

    if args.heartbeat:

        agent.heartbeat()
        sys.exit(1)

    if args.pair:

        try:
            agent.pair(args.console, args.token, groups=args.groups)
        except (ConsoleAlreadyPaired, ConsoleNotPaired) as error:
            logger.error(f"Error during pairing process. {error}")
            sys.exit(1)

    if args.start:
        logger.info("Agent starting...")
        agent.start_roles()
        #agent.start_role('detector')
        import time
        time.sleep(10)
        agent.stop_roles()
