"""Defines """
import argparse
import inspect
import json
import os
import socket
import sys
import time
from multiprocessing import Manager, Queue
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from platformdirs import user_data_dir

from .core.errors import (AgentHeartbeatFailed, ConsoleAlreadyPaired,
                          ConsoleNotPaired)
from .core.event.manager import EventManager, EventSpooler
from .core.logging import logger, setup_logging
from .core.management import (ManagementConnection, connections,
                              get_management_connection)
from .core.version import version_number
from .role import *  # pylint: disable=wildcard-import,unused-wildcard-import # noqa: F403


class AgentConfig:  # pylint: disable=too-many-instance-attributes
    """Defines an AgentConfig object that stores configuration information for
    the Reflex Agent
    """

    def __init__(self, uuid: Optional[str] = None, roles: Optional[List[str]] = None,
                 policy: Optional[Dict[Any, Any]] = None, **kwargs):
        """Initializes the AgentConfig object."""
        if roles is None:
            roles = []

        self.uuid = uuid
        self.roles = roles if roles else []
        self.role_configs: Dict[Any, Any] = {}
        self.console_info: Dict[Any, Any] = {}
        self.name = socket.gethostname()
        setup_logging(init=True)

        # If a policy is provided on initialization, load it
        if policy:
            self.from_policy(policy)
        else:
            self.from_policy(kwargs)

    def json(self, indent=None):
        """Returns the agent configuration as a JSON string."""
        return json.dumps(self.__dict__, indent=indent)

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
        if 'console_info' in policy:
            self.console_info = policy['console_info']
        self.roles = policy.get('roles', self.roles)

    def add_paired_console(self, url: str, api_key: str):
        """Adds a paired console to the agent configuration.

        This method adds a paired console to the agent configuration.
        """

        if self.console_info['url'] != url:
            self.console_info = {
                'api_key': api_key,
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

    def set_value(self, key: str, value: Any) -> bool:
        """Sets a configuration value.

        This method sets a configuration value.

        Args:
            key (str): The key to set.
            value (str): The value to set.
        """
        updateable_config_keys = [
            "roles", "event_cache_key", "event_cache_ttl",
            "health_check_interval", "role_configs", "disable_event_cache_check"
        ]

        if isinstance(value, str):
            if value.lower in ['true', 'false']:
                value = value.lower() == 'true'

        if key in updateable_config_keys:
            if hasattr(self, key):
                if isinstance(getattr(self, key), list):
                    setattr(self, key, value.split(",")
                            if value not in [""] else [])
                    return True
                if isinstance(getattr(self, key), bool):
                    setattr(self, key, bool(value) if value else False)
                    return True
                if isinstance(getattr(self, key), int):
                    setattr(self, key, int(value))
                    return True
                if isinstance(getattr(self, key), str):
                    setattr(self, key, value)
                    return True
                if isinstance(getattr(self, key), dict):
                    setattr(self, key, json.loads(value))
                    return True
            else:
                raise KeyError(f"Key {key} does not exist in AgentConfig.")
        else:
            raise KeyError(f"Key {key} is not updateable.")


class Agent:  # pylint: disable=too-many-instance-attributes
    """The Reflex Agent class. This class is the main entry point for the
    Reflex Agent. It is responsible for loading the configuration, loading
    roles and inputs, and starting the management connection."""

    def __init__(self, config: Optional[Dict[Any, Any]] = None,
                 persistent_config_path: Optional[str] = None,
                 offline: bool = False):
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
            self._set_config(config)
            self.save_persistent_config()
        else:
            logger.info('Loading persistent configuration.')
            if not self.load_persistent_config():
                logger.warning(
                    "Failed to load persistent configuration. Using default configuration.")
                self._set_config({}, from_failed_load=True)

        self.offline = offline
        self.loaded_roles: Dict[Any, Any] = {}
        self.loaded_inputs: Dict[Any, Any] = {}
        self.running_roles: Dict[Any, Any] = {}
        self.event_cache: Dict[Any, Any] = {}
        self.health: Dict[Any, Any] = {}
        self.healthy = True
        self.warnings: List[str] = []
        self.version_number = version_number
        self._role_manager = Manager()
        self._event_manager = None
        self._event_spooler = None
        self._event_queue: Queue = Queue()
        self._managed_connections = self._role_manager.dict(connections)
        self._managed_configs: Dict[Any, Any] = {}

        # Load all available inputs and roles
        self.load_roles()

    def _set_config(self, config: dict, from_failed_load=False) -> None:
        """Sets the agent configuration.

        This method sets the agent configuration.

        Args:
            config (dict): The agent configuration.
        """
        self.config = AgentConfig(**config)
        if not from_failed_load:
            self.save_persistent_config()

    def set_config_value(self, key: str, value: Any, save=True) -> None:
        """Sets a configuration value and saves the configuration"""
        success = self.config.set_value(key, value)
        if save and success:
            self.save_persistent_config()

    @property
    def roles(self) -> list:
        """Returns a list of roles assigned to this agent"""
        return self.config.roles

    @property
    def _ip_address(self) -> str:
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
                    self._set_config(config)
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
        if os.path.exists(_file):
            os.remove(_file)
            return True
        return False

    def fetch_config_from_console(self):
        """Fetches the agent configuration from the management server.

        This method fetches the agent configuration from the management server.
        """
        raise NotImplementedError

    def _get_role_configs(self, policy: dict) -> dict:
        """Gets the role configurations from a passed policy

        This method gets the role configurations.
        """
        role_configs = {}
        for role in self.loaded_roles:
            config_name = f"{role}_config"
            role_config = policy.get(config_name, None)
            if role_config:
                role_configs[config_name] = role_config
                if role in self.running_roles:
                    config = self._managed_configs[config_name]
                    for key, value in role_config.items():
                        config[key] = value
        return role_configs

    def check_policy(self):
        """Checks the agent policy.

        This method checks the agent policy.
        """
        conn = get_management_connection()

        policy = None
        if conn:
            policy = conn.agent_get_policy(self.config.uuid)

        if policy:
            policy_revision = self.config.policy_revision
            if (
                policy['revision'] > policy_revision and policy['uuid'] == policy_revision
            ) or (
                policy['uuid'] != self.config.policy_uuid
            ):
                self.config.from_policy(policy)

                # Update the configuration of all the running roles
                role_configs = self._get_role_configs(policy)

                if role_configs:
                    self.config.set_value('role_configs', role_configs)

                if self.config.roles:
                    self.stop_roles(self.config.roles)
                    self.start_roles()
                else:
                    self.stop_roles()
                self.save_persistent_config()

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

    def add_managed_connection(self, connection):
        """Adds a managed connection to the agent.

        This method adds a managed connection to the agent and available to all roles.

        Args:
            connection (Conection): The connection to add.
        """
        self._managed_connections[connection.name] = connection

    def remove_managed_connection(self, name):
        """Removes a managed connection from the agent.

        This method removes a managed connection from the agent making it
        unavailable to all roles.

        Args:
            connection (Conection): The connection to remove.
        """
        del self._managed_connections[name]

    def pair(self, console_url: str, api_key: str,
             ignore_tls: bool = False, **kwargs) -> bool:
        """Pairs the agent with the management server.

        This method pairs the agent with the management server.

        Args:
            console_url (str): The management server URL.
            api_key (str): The management server access token.
            kwargs (dict): Additional keyword arguments.

        Returns:
            bool: True if the agent was paired, False otherwise.
        """
        if not console_url:
            raise ValueError("Console URL is required.")
        if not api_key:
            raise ValueError("Access token is required.")

        agent_data = {
            "name": self.config.name,
            "ip_address_address": self._ip_address,
            "groups": kwargs.get('groups', []),
        }

        # Check to see if the local config says this agent is already paired with the console
        # if it is throw an error
        if 'url' in self.config.console_info and self.config.console_info['url'] == console_url:
            raise ConsoleAlreadyPaired(
                f"Agent is already paired with {console_url}.")
        # Build a management connection to the pair the agent with
        conn = ManagementConnection(
            console_url, api_key, ignore_tls=ignore_tls, register_globally=True)

        # Call the pairing endpoint
        response = conn.agent_pair(agent_data)
        # response = conn.call_api('POST', '/api/v2.0/agent', agent_data)
        if response:
            self.config.uuid = response['uuid']
            self._managed_connections[conn.name] = conn
            self.config.console_info = conn.config
            self.save_persistent_config()
            return True
        return False

    def heartbeat(self, skip_run=False) -> bool:
        """Sends a heartbeat to the management server.

        This method sends a heartbeat to the management server.
        """

        # Skip heartbeats if running in offline mode.
        if self.offline:
            return True

        recoved = False

        data = {'healthy': self.healthy, 'health_issues': self.warnings,
                'recovered': recoved, 'version': self.version_number}

        conn = get_management_connection()

        if not conn:
            if self.config.console_info:
                conn = ManagementConnection(
                    **self.config.console_info, register_globally=True)
        if conn:
            self.add_managed_connection(conn)
            try:
                if conn.agent_heartbeat(self.config.uuid, data):  # type: ignore
                    logger.success(f"Heartbeat sent to {conn.config['url']}")
                    if not skip_run:
                        self.check_policy()
                    return True
                else:
                    logger.error("No management connection established.")
            except AgentHeartbeatFailed as e:
                logger.error(e)
                return False

        return True

    def load_roles(self):
        """Automatically loads all the roles installed in to the agent library
        and instantiates them.  Configurations for each agent are loaded from
        the agent configuration file.
        """

        # Find all the roles in the agent role library that have been subclassed
        # from the BaseRole class.
        roles = self._load_classes(BaseRole)  # noqa: F405

        # Instantiate each role and add it to the agent roles list.
        for _name, _class in roles:
            self.loaded_roles[_class.shortname] = _class

        for name in self.config.roles:
            if name not in self.loaded_roles:
                self.warnings.append(
                    f"Role \"{name}\" not installed in agent library")

    def initialize_role(self, name):
        """Returns the role object for the given role name.

        This method returns the role object for the given role name.

        Args:
            name (str): The name of the role.

        Returns:
            BaseRole: The role object.
        """
        _class = self.loaded_roles[name]
        config_name = f"{_class.shortname}_config"
        role_config = self.config.role_configs.get(config_name, {'wait_interval': 5})
        self._managed_configs[config_name] = self._role_manager.dict(role_config)

        config = self._managed_configs[config_name]

        return _class(config=config,
                      connections=self._managed_connections,
                      event_manager=self._event_manager
                      )

    def start_roles(self):
        """Starts all roles.

        This method starts all roles.
        """
        for name in self.loaded_roles:
            if name in self.config.roles:
                if name not in self.running_roles:
                    self.running_roles[name] = self.initialize_role(name)
                    self.running_roles[name].start()
            else:
                logger.info(f"Agent not configured for role {name}")

    def start_role(self, name):
        """Starts the specified role.

        This method starts the specified role.
        """
        if name in self.running_roles:
            self.running_roles[name].start()
        else:
            role = self.initialize_role(name)
            self.running_roles[name] = role
            self.running_roles[name].start()

    def stop_role(self, role):
        """Stops the specified role.

        This method stops the specified role.
        """
        if role in self.running_roles:
            self.running_roles[role].stop()
            self.running_roles[role] = None

    def stop_roles(self, roles: Optional[List[str]] = None):
        """Stops all roles.

        This method stops all roles.
        """

        # If a list of assigned roles is passed in, stop the roles that are
        # not in the list
        if roles:
            for role_name, role_class in self.running_roles.items():
                if role_name not in roles:
                    role_class.stop()
                    self.running_roles[role_name] = None
        else:
            for role_name, role_class in self.running_roles.items():
                role_class.stop()
                self.running_roles[role_name] = None

    def reload_role(self, name):
        """
        Reloads the specified role.
        """
        if name in self.running_roles:
            self.stop_role(name)
            self.running_roles[name] = self.initialize_role(name)
            self.running_roles[name].start()

    def start_event_pipeline(self):
        conn = get_management_connection()
        self._event_manager = EventManager(conn=conn, event_queue=self._event_queue)
        self._event_spooler = EventSpooler(conn=conn, event_queue=self._event_queue)
        self._event_spooler.start()

    def run(self):
        """Runs the agent.

        This method runs the agent.
        """
        logger.info(f"Agent starting. Version {self.version_number}.")
        if self.offline:
            logger.warning(
                'Running in offline mode. Some roles may not work.')
        if self.heartbeat(skip_run=True):
            self.start_event_pipeline()
            self.start_roles()
            try:
                while True:
                    seconds = self.config.health_check_interval
                    logger.info(
                        f"Agent sleeping for {seconds} seconds.")
                    time.sleep(self.config.health_check_interval)
                    if not self.heartbeat():
                        self.stop_roles()
                        sys.exit(1)
            except KeyboardInterrupt:
                self.stop_roles()
                sys.exit(0)
        else:
            logger.error("Failed to send heartbeat.")
            sys.exit(1)


def cli_start(agent, console, token, groups, no_start=False):
    """Starts the agent."""
    try:
        agent.pair(console, token, groups=groups)
        if not no_start:
            agent.run()
    except (ConsoleAlreadyPaired, ConsoleNotPaired) as error:
        logger.error(f"Error during pairing process. {error}")
        sys.exit(1)


def cli_reset_console_pairing(agent, console):
    """Resets the pairing with the console. It does not delete the agent on
    the Management Console."""
    try:
        logger.info(
            f"Resetting console pairing for {console}")
        agent.config.remove_paired_console(console)
        agent.save_persistent_config()
    except (ConsoleNotPaired) as error:
        logger.error(
            f"Failed to reset console pairing for {console}. {error}")


def cli_view_config(agent):
    """Displays the agent configuration."""
    logger.info("Configuration Preview:")
    agent.config.json(indent=4)

# pylint disable=too-many-statements


def cli(argv=None):
    """Defines a command line entry point for the agent script"""

    parser = argparse.ArgumentParser()
    parser.add_argument('--pair', action='store_true',
                        help='Pair the agent with the management server')
    parser.add_argument('--pair-skip-start', action='store_true',
                        default=False, help="Skip starting the agent after pairing")
    parser.add_argument('--start', action='store_true', help='Start the agent')
    parser.add_argument('--console', type=str,
                        help='The management server URL')
    parser.add_argument('--token', type=str,
                        help='The management server access token')
    parser.add_argument(
        '--groups', type=str, help='Groups this agent should be added to')
    parser.add_argument('--clear-persistent-config', action='store_true')
    parser.add_argument('--reset-console-pairing', type=str,
                        metavar='CONSOLE_URL',
                        help="""Will reset the pairing for the agent with the
                                supplied  console address""")
    parser.add_argument('--view-config', action='store_true',
                        help="View the agent configuration")
    parser.add_argument('--set-config-value', type=str,
                        metavar="KEY:VALUE1,VALUE2",
                        help="""Set a configuration value.
                                If the target setting is a list provide each value
                                separated by a comma""")
    parser.add_argument('--env-file', type=str,
                        help="The path to the .env file to load", default=None)
    parser.add_argument('--heartbeat', action="store_true",
                        help="Send a heartbeat to the management server")
    parser.add_argument('--offline', action="store_true",
                        help="Run the agent in offline mode", default=False)
    parser.add_argument('--config-path', type=str,
                        help="The path to the agent configuration file", default=None)
    args = parser.parse_args(argv)

    # Load the .env file if it exists
    load_dotenv(args.env_file)

    # Environmental variables can override command line arguments
    args.pair = args.pair or os.getenv('REFLEX_AGENT_PAIR_MODE')
    args.console = args.console or os.getenv('REFLEX_API_HOST')
    args.token = args.token or os.getenv('REFLEX_AGENT_PAIR_TOKEN')

    agent = Agent(offline=args.offline, persistent_config_path=args.config_path)

    if args.set_config_value:
        key, value = args.set_config_value.split(':', 1)
        agent.set_config_value(key, value)
        agent.save_persistent_config()

    if args.view_config:
        cli_view_config(agent)

    if args.clear_persistent_config:
        agent.clear_persistent_config()

    if args.reset_console_pairing:
        cli_reset_console_pairing(agent, args.reset_console_pairing)

    if args.heartbeat:
        agent.heartbeat(skip_run=True)

    if args.pair:
        cli_start(agent, args.console, args.token,
                  groups=args.groups, no_start=args.pair_skip_start)

    if args.start:
        agent.run()
