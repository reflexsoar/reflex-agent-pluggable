class ConsoleAlreadyPaired(Exception):
    """Raised when the console is already paired with a different agent."""


class ConsoleNotPaired(Exception):
    """Raised when the console is not paired with an agent."""


class ConsoleInternalServerError(Exception):
    """Raised when the console returns a 500 error."""


class AgentHeartbeatFailed(Exception):
    """Raised when the agent fails to send a heartbeat to the management server."""


class AgentNotAuthorized(Exception):
    """Raised when the agent is not authorized to connect to the management server."""


class DuplicateConnectionName(Exception):
    """Raised when a connection with the same name already exists."""


class ConnectionNotExist(Exception):
    """Raised when a connection with the specified name does not exist."""


class ForbiddenConnectionName(Exception):
    """Raised when a connection with the name 'default' is added by a process other than
    the Agent process."""
