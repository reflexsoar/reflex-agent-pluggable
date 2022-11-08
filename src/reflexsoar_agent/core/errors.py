class ConsoleAlreadyPaired(Exception):
    """Raised when the console is already paired with a different agent."""
    pass

class ConsoleNotPaired(Exception):
    """Raised when the console is not paired with an agent."""
    pass

class AgentHeartbeatFailed(Exception):
    """Raised when the agent fails to send a heartbeat to the management server."""
    pass

class AgentNotAuthorized(Exception):
    """Raised when the agent is not authorized to connect to the management server."""
    pass