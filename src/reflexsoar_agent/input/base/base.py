import datetime

from typing import List, Dict, Any


class InputTypes:

    BASE = "base"
    POLL = "poll"
    STREAM = "stream"
    LISTENER = "listener"
    INTEL = "intel"


input_types = InputTypes()


class BaseInput:

    alias = "base"
    config_fields: List[str] = []

    def __init__(self, input_type: str, config: Dict[Any, Any]) -> None:

        self.config: Dict[Any, Any]
        self.type = input_type
        self.parse_config(config)
        self.last_run = None
        self.organization: str
        self.observable_mapping: List[Dict[Any, Any]] = []
        self.signature_fields: List[str] = []
        self.source_field: str
        self.base_fields: Dict[Any, Any] = {}

    @classmethod
    def parse_config(self, config: dict):
        """Parse the input configuration.
        This method parses the input configuration and only returns the
        fields in the dict that are involved with configuring the input
        """

        self.organization = config.get('organization', None)

        # Extract the observable mapping
        self.observable_mapping = config.get('field_mapping', {}).get('fields', [])

        # The entire input config is passed in here but has its own
        # config sub-key so it has to be pulled upwards
        _actual_config = config.get('config', {})

        # Grab the signature fields
        self.signature_fields = _actual_config.get('signature_fields', [])

        # Grab the source field
        self.source_field = _actual_config.get('source_field', '_source')

        # Get the Event base fields
        self.base_fields = {k: _actual_config.get(k, None) for k, v in _actual_config.items()
                            if k in ['rule_name', 'description_field',
                                     'severity_field', 'source_reference',
                                     'original_date_field', 'tag_fields', 'static_tags']
                            }

        # Return configs for the actual input
        self.config = {k: v for k, v in _actual_config.items()
                       if k in self.config_fields}

    def main(self):
        """Main loop.
        This method is the main loop for the input.
        """
        pass

    def run(self):
        """Start the input.
        This method starts the input.
        """
        self._running = True
        data = self.main()
        self.last_run = datetime.datetime.utcnow()
        self._running = False
        return data
