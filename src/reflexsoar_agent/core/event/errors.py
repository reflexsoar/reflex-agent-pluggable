class MaxEventsError(Exception):
    """Raised when the maximum number of events is reached"""


class EventManagedInitializedError(Exception):
    """Raised when the EventManager is already initialized"""
