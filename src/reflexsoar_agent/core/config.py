import json
import socket
from typing import Any, Dict, List, Optional

from .errors import ConsoleAlreadyPaired, ConsoleNotPaired
from .logging import setup_logging


class AgentPolicy:
    """Defines an AgentPolicy object that stores policy based configuration
    items provided by the management console"""

    def __init__(self, policy: dict):
        """Initializes the AgentPolicy object"""
        self._flat_policy = policy
        self._parse_policy(policy)

    @property
    def policy(self):
        """Returns the policy dictionary"""
        return self._policy

    @property
    def flat_policy(self):
        """Returns the flat policy dictionary"""
        return self._flat_policy

    def _parse_policy(self, policy: dict):
        """Parses the policy dictionary and adds each key as an
        attribute to the AgentPolicy object"""

        def combine(data: dict, combined: dict) -> None:
            for key, value in data.items():
                if isinstance(value, dict):
                    combine(value, combined.setdefault(key, {}))
                else:
                    combined[key] = value

        self._policy = {}
        for key, value in policy.items():
            parts = key.split('.')
            parts.reverse()
            policy_item = {}
            for part in parts:
                if parts.index(part) == 0:
                    policy_item[part] = value
                else:
                    policy_item = {part: policy_item}
            combine(policy_item, self._policy)
        print(json.dumps(self._policy, indent=2))


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

    def set_value(self, key: str, value: Any) -> bool:  # noqa: C901
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
                    if isinstance(value, str):
                        value = json.loads(value)
                    setattr(self, key, value)
                    return True
            else:
                raise KeyError(f"Key {key} does not exist in AgentConfig.")
        else:
            raise KeyError(f"Key {key} is not updateable.")
        return False
