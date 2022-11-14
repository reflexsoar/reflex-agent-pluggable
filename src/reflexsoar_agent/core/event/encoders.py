import json


class CustomJsonEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, JSONSerializable):
            return o.__dict__
        return json.JSONEncoder.default(self, o)


class JSONSerializable(object):
    ''' Allows for an object to be represented in JSON format '''

    def jsonify(self, ignore_private_fields=True, skip_null=True):
        ''' Returns a json string of the object '''

        sanitized_results = self.__dict__

        # Remove any fields that are None, or [] or {}
        if skip_null:
            sanitized_results = {k: v for k, v in sanitized_results.items()
                                 if v not in [[], {}, None]
                                 }

        # Ignore any fields that are private to the class
        if ignore_private_fields:
            sanitized_results = {k: v for k, v in sanitized_results.items()
                                 if not k.startswith("_")
                                 }

        return json.dumps(sanitized_results, sort_keys=True, indent=4, cls=CustomJsonEncoder)

    def attr(self, attributes, name, default, error=None):
        ''' Fetches an attribute from the passed dictionary '''

        is_required = error is not None

        if is_required and name not in attributes:
            raise ValueError(error)
        else:
            return attributes.get(name, default)
