""" reflexsoar_agent/core/event/base.py

Defines the base Event and Observable classes that are used to create events
and their associated observables.  These classes are used by the event manager
to create events and observables that are sent to the API.
"""


import datetime
import hashlib
import json
from typing import Union, Optional, Dict, Any, List

from reflexsoar_agent.core.event.encoders import JSONSerializable


class Observable(JSONSerializable):  # pylint: disable=too-many-instance-attributes
    """Observable class for handling individual observables. Observables are
    attached to Events for shipping to the Management Console.
    """

    # pylint: disable=too-many-arguments
    def __init__(self, value, data_type: str, tlp: int, tags: list, ioc: bool,
                 spotted: bool, safe: bool, original_source_field: str,
                 source_field: str):
        """Initializes the Observable class."""
        self.value = str(value)
        self.data_type = data_type
        self.tlp = tlp
        self.tags = tags
        self.ioc = ioc
        self.spotted = spotted
        self.safe = safe
        self.source_field = source_field
        self.original_source_field = original_source_field


class Event(JSONSerializable):  # pylint: disable=too-many-instance-attributes
    """Creates a Event class for working with individual events"""

    # pylint: disable=too-many-arguments
    def __init__(self, data: Optional[Dict[Any, Any]] = None,
                 base_fields: Optional[Dict[Any, Any]] = None,
                 signature_fields: Optional[List[str]] = None,
                 observable_mapping: Optional[List[Dict[Any, Any]]] = None,
                 source_field: Optional[str] = None,
                 severity_map: Optional[Dict[Any, Any]] = None,
                 source: Optional[str] = None, **kwargs) -> None:
        """Initializes the Event class

        Args:
            data (dict): The data to use for the event
            base_fields (dict): The base fields to use for the event
            signature_fields (list): The fields to use for the signature
            observable_mapping (list): The mapping of fields to observables
            source_field (str): The field to use for the source
            source (str): The source where this event originated
            severity_map (dict): The mapping of severity values to integers

        Keyword Arguments:
            title (str): The title of the event
            description (str): The description of the event
            severity (int): The severity of the event
            tags (list): A list of tags to add to the event
            tlp (int): The TLP level of the event
            raw_log (str): The raw log of the event
            observables (list): A list of observables to add to the event
            reference (str): The reference of the event
            signature (str): The signature of the event
            detection_id (str): The detection ID of the event
            original_date (str): The original date of the event
            risk_score (int): The risk score of the event
        """

        self.title = None
        self.description = None
        self.reference = None
        self.tags: List[str] = []
        self.tlp = 0
        self.severity = 1
        self.observables: List[Union[Observable, Dict[Any, Any]]] = []
        self.raw_log = None
        self.signature = None
        self.detection_id = None
        self.risk_score = None
        self.original_date = None
        self._base_fields: Dict[Any, Any] = {}
        self._observable_mapping: List[Dict[Any, Any]] = []
        self._custom_severity_map = severity_map

        if source is None:
            raise ValueError('Source must be provided')

        self.source = source

        if kwargs:
            for key, value in kwargs.items():
                if key == 'observables':
                    self._parse_observables_from_init(value)
                elif key == 'severity':
                    value = self._severity_from_map(value)
                    setattr(self, key, value)
                else:
                    setattr(self, key, value)

        self._init_parsing_config(
            data, base_fields, signature_fields, observable_mapping, source_field)

    def _parse_observables_from_init(self, observables: list) -> None:
        """Takes data from __init__ that was passed in the observables param
        and parses it in to a list of Observable objects and adds it to the
        event

        Args:
            observables (list): A list of observables
        """

        if isinstance(observables, list):

            for observable in observables:
                if isinstance(observable, Observable):
                    self.observables.append(observable)
                elif isinstance(observable, dict):
                    self.observables.append(Observable(**observable))
                else:
                    raise TypeError('Invalid observable source data, must Observable or Dict')
        else:
            raise TypeError('Invalid observables source data, must be a list')

    def _init_parsing_config(self, data: Optional[Dict[Any, Any]] = None,
                             base_fields: Optional[Dict[Any, Any]] = None,
                             signature_fields: Optional[List[str]] = None,
                             observable_mapping: Optional[List[Dict[Any, Any]]] = None,
                             source_field: Optional[str] = None) -> None:
        """Initializes the parsing configuration for the Event object so that
        when data is provided to the data variable it parses out the correct
        fields, tags, observables, raw_log, etc.

        Args:
            data (dict): The data to use for the event
            base_fields (dict): The base fields to use for the event
            signature_fields (list): The fields to use for the signature
            observable_mapping (dict): The mapping of fields to observables
            source_field (str): The field to use for the source
        """

        if signature_fields is None:
            self._signature_fields = []
        else:
            self._signature_fields = signature_fields

        if base_fields is None:
            self._base_fields = {}
        else:
            self._base_fields = base_fields

        if observable_mapping is None:
            self._observable_mapping = []
        else:
            self._observable_mapping = observable_mapping

        if data is None:
            self._message = {}
        else:
            if source_field:
                self._message = data[source_field]
            else:
                self._message = data
            self._set_event_base()
            self._generate_signature()
            self._extract_observables()

    def _severity_from_map(self, severity: Union[str, int]):
        """Converts the provided severity string to the appropriate
        integer value

        Args:
            severity (str): The severity string to convert
        """

        if not isinstance(severity, (str, int)):
            raise TypeError('Severity must be a string or int')

        if isinstance(severity, str):
            severity = severity.lower()

        if self._custom_severity_map:
            _severity_map = self._custom_severity_map
        else:
            _severity_map = {
                'low': 1,
                'medium': 2,
                'high': 3,
                'critical': 4,
                1: 1,
                2: 2,
                3: 3,
                4: 4
            }

        if severity is None or severity not in _severity_map:
            return 1

        return _severity_map[severity]

    def _extract_observables(self):
        """Extracts all the observables from the Event based on the
        provided observabal_mapping. If no observable_mapping is supplied, the
        observables list will not be populated
        """

        _observables = []

        for field in self._observable_mapping:

            # Set default flags if they are not present in the mapping
            for flag in ['ioc', 'spotted', 'safe']:
                if flag not in field:
                    field[flag] = False

            tags = []
            if 'tags' in field:
                tags += field['tags']

            value = self._extract_field_value(self._message, field['field'])
            source_field = field['field']
            original_source_field = field['field']

            if 'alias' in field and field['alias']:
                source_field = field['alias']

            if value:
                if isinstance(value, list):
                    for value_item in value:
                        _observables.append(Observable(
                            value=value_item,
                            source_field=source_field,
                            original_source_field=original_source_field,
                            ioc=field['ioc'],
                            spotted=field['spotted'],
                            safe=field['safe'],
                            tlp=field['tlp'],
                            tags=tags,
                            data_type=field['data_type']
                        ))
                else:
                    _observables.append(Observable(
                        value=value,
                        source_field=source_field,
                        original_source_field=original_source_field,
                        ioc=field['ioc'],
                        spotted=field['spotted'],
                        safe=field['safe'],
                        tlp=field['tlp'],
                        tags=tags,
                        data_type=field['data_type']
                    ))

        self.observables = _observables

    def _set_event_base(self):
        """Sets the base event fields based on the raw data"""

        extractable_fields = {
            'rule_name': 'title',
            'description_field': 'description',
            'source_reference': 'reference',
            'original_date_field': 'original_date'
        }

        # For all the fields that are extractable, extract the value and
        # assign it to the associated Event field
        for field in self._base_fields:
            if field in extractable_fields:
                setattr(self, extractable_fields[field], self._extract_field_value(
                    self._message, self._base_fields[field]))

        # Fix the original_date to exclucde the Z
        if hasattr(self, 'original_date') and self.original_date is not None:
            self.original_date = self.original_date.replace('Z', '')

        # Set these fields to the values defined in the _base_fields configuration
        for field in ['tlp', 'type', 'source', 'risk_score']:
            if field in self._base_fields:
                setattr(self, field, self._base_fields[field])

        # Get the event severity field, if None default to Low
        if 'severity_field' in self._base_fields:
            severity = self._extract_field_value(
                self._message, self._base_fields['severity_field'])

            self.severity = self._severity_from_map(severity)
            #else:
            #    self.severity = severity

        if 'static_tags' in self._base_fields:
            self.tags += self._base_fields['static_tags']

        if 'tag_fields' in self._base_fields:
            self._extract_fields_as_tags(self._base_fields['tag_fields'])

        self.raw_log = json.dumps(self._message)

    def _extract_fields_as_tags(self, fields: Optional[List[str]] = None):
        """Extracts all the fields from the Event based on the provided
        fields list. If no fields list is supplied, the tags list will not
        be populated
        """
        tags = []
        if fields is not None:
            for tag_field in fields:
                tags = self._extract_field_value(self._message, tag_field)
                if tags:
                    if isinstance(tags, list):
                        _ = [self.tags.append(f"{tag_field}:{tag}") for tag in tags] # type: ignore
                    else:
                        self.tags += [f"{tag_field}: {tags}"]
        return tags

    # flake8: noqa: C901 # pylint: disable=too-many-branches,inconsistent-return-statements
    def _extract_field_value(self, message: Union[List[Any], Dict[Any, Any]], field: Union[str, List[str]]):
        """Extracts the value of the provided field from the Events raw
        data. If no field is provided, None is returned

        Args:
            field (str): The field to extract the value from
        """

        if isinstance(field, str):
            if message == None:
                return None
            if field in message:
                return message[field] # type: ignore

            args = field.split('.')
        else:
            args = field

        # pylint: disable=too-many-nested-blocks
        if args and message:
            element = args[0]
            if element:
                if isinstance(message, list):
                    values = []
                    value = [m for m in message if m is not None]
                    if any(isinstance(i, list) for i in value):
                        for value_item in value:
                            if isinstance(value_item, list):
                                values += [v for v in value_item if v is not None]
                    else:
                        values += [v for v in value if not isinstance(v, list)]
                    value = values
                else:
                    if isinstance(message, dict):
                        value = message.get(element) # type: ignore
                    else:
                        value = message

                if isinstance(value, list):
                    if len(value) > 0 and isinstance(value[0], dict):
                        if len(args) > 1:
                            value = [self._extract_field_value(
                                item, args[1:]) for item in value]

                return value if len(args) == 1 else self._extract_field_value(value, '.'.join(args[1:]))

    def _generate_signature(self):
        """Generates an event signature based on the provided signature_fields.
        If no signature_fields are supplied, the signature will be populated
        based on the title of the event and the current UTC time
        """

        signature_values = []

        # Set the default to the event title and current UTC time if no
        # signature_fields are provided
        if self._signature_fields == []:
            signature_values += [self.title, datetime.datetime.utcnow()]
        else:
            for field in self._signature_fields:
                field_value = self._extract_field_value(self._message, field)
                if field_value:
                    signature_values.append(field_value)

        event_hasher = hashlib.md5(usedforsecurity=False)
        event_hasher.update(str(signature_values).encode())
        self.signature = event_hasher.hexdigest()
