from .encoders import JSONSerializable


class Observable(JSONSerializable):
    """Observable class for handling individual observables. Observables are
    attached to Events for shipping to the Management Console.
    """


class Event(JSONSerializable):
    """Creates a Event class for working with individual events"""

    def __init__(self):
        pass
