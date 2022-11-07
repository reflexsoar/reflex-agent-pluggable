"""Defines all the functions that are used to manage the agent and have 
the agent communicate with the ReflexSOAR management server
"""

from requests import Session, Request

class ManagementConnection:

    def __init__(self, mgmt_url: str, api_key: str, name: str = 'default') -> None:
        """Initializes the management connection
        
        Args:
            mgmt_url (str): The URL of the management server
            api_key (str): The API key to use for authentication
            name (str): The name of the connection. Defaults to 'default'.
        """

        self.name = name
        self._session = Session()
        self.api_key = api_key
        self._mgmt_url = mgmt_url
        self.set_default_headers()
        self._mgmt_api_version = "v2.0"
        self.VERSION_NUMBER = '0.0.1'

    
    def set_default_headers(self):
        self._session.headers.update({'Authorization': f'Bearer {self.api_key}'})
        self._session.headers.update({'Content-Type': 'application/json'})
        self._session.headers.update({'User-Agent': 'reflexsoar-agent/{self.VERSION_NUMBER}'})


    def call_api(self, method: str, endpoint: str, data: dict, **kwargs) -> dict:
        """Calls the management API
        
        Args:
            method (str): The HTTP method to use
            endpoint (str): The endpoint to call
            data (dict): The data to send to the endpoint
            **kwargs: Additional arguments to pass to the request
        
        Returns:
            dict: The response from the server
        """

        try:# Establish a base request dict
            request_data = {
                'url': f'{self._mgmt_url}/api/{self._mgmt_api_version}/{endpoint}'
            }

            # If passing data, add it to the request as the json parameter
            if data:
                request_data['json'] = data

            # Prepare the HTTP request
            request = Request(method, **request_data)
            prepared_request = request.prepare()

            # Send the HTTP request
            response = self._session.send(prepared_request)
            return response
        except Exception as e:
            print(e)
            return None

connections = {}

def add_management_connection(conn: ManagementConnection) -> None:
    """Adds a management connection to the agent

    This method adds a management connection to the agent. The connection
    is used to communicate with the ReflexSOAR management server.
    """
    if conn.name in connections:
        raise ValueError(f"Connection with name \"{conn.name}\" already exists")
    connections.update({conn.name: conn})

def remove_management_connection(conn: ManagementConnection) -> None:
    """Removes a management connection from the agent

    This method removes a management connection from the agent. The connection
    is used to communicate with the ReflexSOAR management server.
    """
    if conn.name not in connections:
        raise ValueError(f"Connection with name \"{conn.name}\" does not exist")
    connections.pop(conn.name)

def get_management_connection(name: str = 'default') -> ManagementConnection:
    """Returns a management connection from the agent

    This method returns a management connection from the agent. The connection
    is used to communicate with the ReflexSOAR management server.
    """
    if name not in connections:
        raise ValueError(f"Connection with name \"{name}\" does not exist")
    return connections.get(name)

