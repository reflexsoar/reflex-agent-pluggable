"""Defines all the functions that are used to manage the agent and have
the agent communicate with the ReflexSOAR management server
"""

from typing import Any

from requests import Request, Session
from requests.exceptions import ConnectionError, HTTPError

from .errors import (AgentHeartbeatFailed, ConnectionNotExist,
                     ConsoleAlreadyPaired, ConsoleInternalServerError,
                     DuplicateConnectionName)
from .logging import logger
from .version import version_number

_USER_AGENT = f'reflexsoar-agent/{version_number}'


class HTTPConnection:

    def __init__(self, url: str, api_key: str, ignore_tls: bool = False,
                 name: str = 'default', register_globally=False,
                 user_agent: str = None) -> None:
        """Initializes the management connection

        Args:
            url (str): The URL of the management server
            api_key (str): The API key to use for authentication
            name (str): The name of the connection. Defaults to 'default'.
            register_globally (bool, optional): Share with all roles.
        """
        self.name = name
        self.user_agent = user_agent or _USER_AGENT
        self._session = Session()
        self.api_key = api_key
        self.url = url
        self.ignore_tls = ignore_tls
        self.set_default_headers()
        if register_globally:
            add_management_connection(self)

    @property
    def config(self):
        return {
            k: self.__dict__[k] for k in self.__dict__
            if k in ['name', 'url', 'api_key', 'ignore_tls']
        }

    def set_default_headers(self):
        self._session.headers.update(
            {'Authorization': f'Bearer {self.api_key}'})
        self._session.headers.update({'Content-Type': 'application/json'})
        self._session.headers.update(
            {'User-Agent': self.user_agent})

    def update_header(self, key: str, value: str) -> None:
        """Updates the header for the management connection

        Args:
            key (str): The key to update
            value (str): The value to set
        """

        self._session.headers[key] = value

    def call_api(self, method: str, endpoint: str, data: dict, **kwargs) -> Any:
        """Calls the management API

        Args:
            method (str): The HTTP method to use
            endpoint (str): The endpoint to call
            data (dict): The data to send to the endpoint
            **kwargs: Additional arguments to pass to the request

        Returns:
            Response: The response from the server
        """

        # Fix up the endpoint it shouldn't start or end with a /
        if endpoint.startswith('/'):
            endpoint = endpoint[1:]
        if endpoint.endswith('/'):
            endpoint = endpoint[:-1]

        try:  # Establish a base request dict
            request_data = {
                'url': f'{self.url}/{endpoint}'
            }

            # If passing data, add it to the request as the json parameter
            if data:
                request_data['json'] = data

            # Prepare the HTTP request
            request = Request(method, **request_data,
                              headers=self._session.headers)
            prepared_request = request.prepare()

            # Send the HTTP request
            response = self._session.send(prepared_request)
            return response
        except ConnectionError as e:
            logger.error(f"Failed to connect to {self.url}. {e}")
        except HTTPError as e:
            logger.error(f"Failed to connect to {self.url}. {e}")
        return None


class ManagementConnection(HTTPConnection):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def agent_heartbeat(self, agent_id: str, data: dict) -> dict:
        """Sends a heartbeat to the management server"""
        if (response := self.call_api(
                'POST', f'/api/v2.0/agent/heartbeat/{agent_id}', data)):
            if response.status_code == 200:
                response = response.json()
            else:
                raise AgentHeartbeatFailed(
                    f"Failed to send heartbeat: {response.text}")
        return response

    def agent_pair(self, data: dict) -> dict:
        """Pairs the agent with the management server"""
        response = self.call_api('POST', '/api/v2.0/agent', data=data)
        if response and response.status_code == 200:
            response = response.json()
            # Update this connection with the new access token
            self.update_header('Authorization', f"Bearer {response['token']}")
            self.api_key = response['token']
        elif response and response.status_code == 409:
            raise ConsoleAlreadyPaired(
                f"Failed to pair agent: {response.text}")
        elif response and response.status_code == 500:
            raise ConsoleInternalServerError(
                f"Failed to pair agent: {response.text}")

        return response

    def agent_get_policy(self, agent_id: str) -> dict:
        """Gets the policy for the agent"""
        response = self.call_api(
            'GET', f'/api/v2.0/agent/{agent_id}', None)
        if response and response.status_code == 200:
            response = response.json()['policy']
        return response

    def agent_get_inputs(self) -> dict:
        """Gets the inputs for the agent"""
        response = self.call_api(
            'GET', '/api/v2.0/agent/inputs', None)
        if response and response.status_code == 200:
            response = response.json()['inputs']
        return response


# Globally registered connections dictionary that can be imported
# not useful across multiprocess boundaries so the agent manages an additional
# list of connections to share with Agent sub-processes
connections = {}


def build_http_connection(url: str, api_key: str, ignore_tls: bool = False,
                          name: str = 'default'):
    """Wrapper function for creating a basic HTTP connection"""
    if name not in connections:
        conn = HTTPConnection(url, api_key, ignore_tls, name)
        return conn


def build_connection(url: str, api_key: str, ignore_tls: bool = False,
                     name: str = 'default', register_globally=False):
    """Wrapper function for creating a management connection"""
    if name not in connections:
        conn = ManagementConnection(url, api_key, ignore_tls,
                                    name, register_globally=register_globally)
        return conn


def add_management_connection(conn: ManagementConnection) -> None:
    """Adds a management connection to the agent

    This method adds a management connection to the agent. The connection
    is used to communicate with the ReflexSOAR management server.
    """
    if conn.name in connections:
        raise DuplicateConnectionName(
            f"Connection with name \"{conn.name}\" already exists")
    connections.update({conn.name: conn})


def remove_management_connection(conn: ManagementConnection) -> None:
    """Removes a management connection from the agent

    This method removes a management connection from the agent. The connection
    is used to communicate with the ReflexSOAR management server.
    """
    if conn.name not in connections:
        raise ConnectionNotExist(
            f"Connection with name \"{conn.name}\" does not exist")
    connections.pop(conn.name)


def get_management_connection(name: str = 'default') -> ManagementConnection:
    """Returns a management connection from the agent

    This method returns a management connection from the agent. The connection
    is used to communicate with the ReflexSOAR management server.
    """
    if name in connections:
        return connections[name]
    return None
