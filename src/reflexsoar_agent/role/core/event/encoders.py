import json


class CustomJsonEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, JSONSerializable):
            return o.__dict__
        return json.JSONEncoder.default(self, o)


class JSONSerializable(object):
    ''' Allows for an object to be represented in JSON format '''

    def jsonify(self):
        ''' Returns a json string of the object '''
        
        return json.dumps(self, sort_keys=True, indent=4, cls=CustomJsonEncoder)

    def attr(self, attributes, name, default, error=None):
        ''' Fetches an attribute from the passed dictionary '''
        
        is_required = error is not None

        if is_required and name not in attributes:
            raise ValueError(error)
        else:
            return attributes.get(name, default)


