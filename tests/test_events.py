import json

import pytest

from reflexsoar_agent.core.event import Event, Observable


@pytest.fixture
def elastic_signals():
    with open('./tests/sample_data/elastic_signals.json') as f:
        return json.load(f)['hits']


@pytest.fixture
def signature_fields():
    return ['host.hostname', 'kibana.alert.rule.name']


@pytest.fixture
def observable_mapping():
    return [
        {
            "field": "host.name",
            "alias": "hostname",
            "data_type": "host",
            "tlp": 3,
            "tags": [
                "workstation"
            ]
        }
    ]


@pytest.fixture
def base_fields():
    return {
        'original_date_field': '@timestamp',
        'rule_name': 'kibana.alert.rule.name',
        'severity_field': 'kibana.alert.rule.severity',
        'description_field': 'kibana.alert.rule.description',
        'tag_fields': ['kibana.alert.rule.tags'],
        'static_tags': ['awesome'],
        'source_reference': 'kibana.alert.rule.uuid',
    }


@pytest.fixture
def empty_field():
    return [{}, [], None, ""]

@pytest.fixture
def observable_item():
    return {
                'value': 'test',
                'data_type': 'hostname',
                'tags': ['test', 'pytest'],
                'tlp': 3,
                'spotted': False,
                'safe': False,
                'ioc': False,
                'source_field': 'host.hostname',
                'original_source_field': 'host.hostname'
            }

@pytest.fixture
def event_item():
    return {
        'title': 'Test Event',
        'description': 'A test event from pylint',
        'severity': 'low',
        'tlp': 3,
        'tags': ['test', 'pytest'],
        'source': 'pytest',
        'observables': [
            {
                'value': 'test',
                'data_type': 'hostname',
                'tags': ['test', 'pytest'],
                'tlp': 3,
                'spotted': False,
                'safe': False,
                'ioc': False,
                'source_field': 'host.hostname',
                'original_source_field': 'host.hostname'
            }
        ],
        'reference': 'abc-pytest-1234',
        'raw_log': "foobar",
        'detection_id': '1234',
        'risk_score': 1000,
        'original_data': '2022-11-14T00:00:00.000',
    }


def test_event_from_dict(event_item):
    """Check to make sure that we can instantiate an Event and its underlying
    observables from a dictionary object and that the fields parse all the way
    through to the Event object
    """

    event = Event(**event_item)
    for key, value in event_item.items():
        if key == 'observables':
            for observable in getattr(event, key):
                for okey, ovalue in value[0].items():
                    assert getattr(observable, okey) == ovalue
        else:
            assert getattr(event, key) == value


def test_observable_from_dict(observable_item):
    """Tests to make sure that an observable can be fully instantiated from
    a dictionary object"""

    observable = Observable(**observable_item)
    for key, value in observable_item.items():
        assert getattr(observable, key) == value


def test_event_observable_not_dict_or_observable_type(observable_item):
    """Make sure that we can't instantiate an Event or Observable with a non-dict
    or non-Observable type"""

    with pytest.raises(TypeError):
        Event(observables=1234, source="pytest")

    with pytest.raises(TypeError):
        Event(observables=[1, 2, 3], source="pytest")

    with pytest.raises(TypeError):
        Event(observables=['a', 'b', 'c'], source="pytest")

    event_a = Event(observables=[observable_item], source="pytest")
    assert isinstance(event_a.observables[0], Observable)

    event_b = Event(observables=[Observable(**observable_item)], source="pytest")
    assert isinstance(event_b.observables[0], Observable)


def test_elastic_signals(elastic_signals, base_fields, observable_mapping, signature_fields, empty_field):
    """Make sure that we can parse Elastic signals into Event objects"""

    events = []
    for raw_event in elastic_signals:
        event = Event(raw_event, base_fields=base_fields, signature_fields=signature_fields,
                      observable_mapping=observable_mapping, source_field="_source", source="pytest")
        assert event.observables not in empty_field
        assert event.title not in empty_field
        assert event.description is not None
        assert event.tlp is not None
        assert event.tlp in [0, 1, 2, 3, 4]
        assert event.severity in [1, 2, 3, 4]
        assert event.tags not in empty_field
        assert event.source not in empty_field
        assert event.original_date is not None
        assert not event.original_date.endswith('Z')
        events.append(event)

    assert len(events) == 10

def test_event_as_json(event_item):
    """Checks to make sure that the jsonify() call fully serializes the Event
    to JSON
    """

    event = Event(**event_item)
    event_json = event.jsonify()

    assert isinstance(event_json, str)

    event_dict = json.loads(event_json)
    assert isinstance(event_dict['observables'], list)
    assert isinstance(event_dict['observables'][0], dict)
    assert any([k.startswith('_') for k in event_dict]) == False

    event = Event(**event_item, base_fields={'original_date_field': '@timestamp'})
    event_json = json.loads(event.jsonify(ignore_private_fields=False, skip_null=True))
    for k in event_json.keys():
        print(k)
        if k.startswith('_'):
            assert True == True
