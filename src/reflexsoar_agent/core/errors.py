class ConsoleAlreadyPaired(Exception):
    """Raised when the console is already paired with a different agent."""
    pass

class ConsoleNotPaired(Exception):
    """Raised when the console is not paired with an agent."""
    pass

class ConsoleInternalServerError(Exception):
    """Raised when the console returns a 500 error."""
    pass

class AgentHeartbeatFailed(Exception):
    """Raised when the agent fails to send a heartbeat to the management server."""
    pass

class AgentNotAuthorized(Exception):
    """Raised when the agent is not authorized to connect to the management server."""
    pass

class DuplicateConnectionName(Exception):
    """Raised when a connection with the same name already exists."""
    pass

class ConnectionNotExist(Exception):
    """Raised when a connection with the specified name does not exist."""
    pass

class ForbiddenConnectionName(Exception):
    """Raised when a connection with the name 'default' is added by a process other than
    the Agent process."""
    pass