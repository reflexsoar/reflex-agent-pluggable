class ConsoleAlreadyPaired(Exception):
    """Raised when the console is already paired with a different agent."""
    pass

class ConsoleNotPaired(Exception):
    """Raised when the console is not paired with an agent."""
    pass