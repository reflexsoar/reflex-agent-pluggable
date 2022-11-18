import json

import pytest

from reflexsoar_agent.core.event.encoders import (CustomJsonEncoder,
                                                  JSONSerializable)


def test_custom_json_encoder():
    class TestClass(JSONSerializable):
        def __init__(self, test):
            self.test = test

        def to_json(self):
            return {'test': self.test}

    test = TestClass('test')
    encoder = CustomJsonEncoder()
    assert encoder.default(test) == {'test': 'test'}

    with pytest.raises(TypeError):
        assert encoder.default("test") == "test"

def test_json_serializable():
    class TestClass(JSONSerializable):
        def __init__(self, test):
            self.test = test

        def to_json(self):
            return {'test': self.test}

    test = TestClass('test')
    assert test.to_json() == {'test': 'test'}

    json_data = test.jsonify()
    assert json.loads(json_data) == {"test": "test"}

    assert test.attr({'test2':'test2'}, 'test2', 'foo') == 'test2'
    with pytest.raises(ValueError):
        test.attr({'test2':'test2'}, None, 'foo', 'Something something required.')
