"""reflexsoar_agent/role/core/detector/rule.py

Defines the Detection class that all other detection items should inherit
from.  This class provides the basic functionality for all detection types.
"""

import math
from typing import List, Optional
from dataclasses import dataclass
from dateutil import parser as date_parser
from datetime import timedelta, datetime

from reflexsoar_agent.role.core.detector.rule import BaseRuleTypeConfig, RULE_TYPES


@dataclass
class QueryConfig:
    """Defines what backend to use for the query and the query itself."""

    query: str
    language: str  # Legacy field, should be removed in the future
    backend: str


@dataclass
class MITRETacticTechnique:
    """Defines a MITRE tactic and technique."""

    mitre_id: str
    external_id: str
    name: str
    shortname: str


@dataclass
class SourceConfig:
    """Defines the source of the detection."""

    language: str
    name: str
    uuid: str


@dataclass
class ObservableField:
    """Defines the observable field."""

    field: str
    alias: str
    data_type: str
    tlp: int
    tags: List[str]


@dataclass
class DetectionExceptionList:
    """Defines the exception list."""

    name: str


class DetectionException:
    """Defines an exception for a detection."""

    def __init__(self, values: List[str], condition: str, description: str, **kwargs):
        self.values = values
        self.condition = condition
        self.description = description
        # type: Optional[List[str]]
        self.value_list = kwargs.get('value_list', []) or []


class Detection:
    """ A detection rule object that makes it easier to interact with
    the rule definition
    """

    def __init__(self, uuid: str, name: str, query: QueryConfig, description: str,
                 active: bool, interval: int, lookbehind: int, source: SourceConfig,
                 signature_fields: List[str], observable_fields: List[ObservableField],
                 exceptions: List[DetectionException], **kwargs):

        self.uuid = uuid
        self.name = name
        self.query = query
        self.active: bool = active
        self.description = description
        self.source: SourceConfig = source
        self.time_taken: int = 0
        self.query_time_taken: float = 0
        self.interval: int = interval
        self.lookbehind: int = lookbehind
        self.exceptions: List[DetectionException] = exceptions
        self.signature_fields: List[str] = signature_fields
        self.observable_fields: List[ObservableField] = observable_fields
        self.next_run: str
        self._optional_values(**kwargs)

    def _optional_values(self, **kwargs):
        """Sets optional values for the detection rule."""

        self.detection_id: str = kwargs.get('detection_id', "") or ""
        self.from_sigma: bool = kwargs.get('from_sigma', False) or False
        self.sigma_rule: str = kwargs.get('sigma_rule', "") or ""
        self.sigma_rule_id: str = kwargs.get('sigma_rule_id', "") or ""
        self.guide: str = kwargs.get('guide', "") or ""
        self.tags: List[str] = kwargs.get('tags', []) or []
        self.tactics: List[MITRETacticTechnique] = kwargs.get('tactics', []) or []
        self.techniques: List[MITRETacticTechnique] = kwargs.get('techniques', []) or []
        self.references: List[str] = kwargs.get('references', []) or []
        self.false_positives: List[str] = kwargs.get('false_positives', []) or []
        self.kill_chain_phase: str = kwargs.get('kill_chain_phase', 'none') or 'none'
        self.rule_type_str: str = kwargs.get('rule_type', 'match') or 'match'
        self.rule_type: int = getattr(RULE_TYPES, self.rule_type_str.upper())
        self.version: int = kwargs.get('version', 1) or 1
        self.catchup_period: int = kwargs.get('catchup_period', 0) or 0
        self.skip_event_rules: bool = kwargs.get('skip_event_rules', False) or False
        self.mute_period: int = kwargs.get('mute_period', 0) or 0
        self.rule_type_config: BaseRuleTypeConfig = kwargs.get(
            'rule_type_config', None) or None
        self.assigned_agent: str = kwargs.get('assigned_agent', "") or ""
        self.warnings: List[str] = kwargs.get('warnings', []) or []
        self.case_template: str = kwargs.get('case_template', "") or ""
        self.risk_score: int = kwargs.get('risk_score', 0) or 0
        self.severity: int = kwargs.get('severity', 0) or 0
        self.total_hits: int = kwargs.get('total_hits', 0) or 0
        self.run_start: str = kwargs.get('run_start', "") or ""
        self.run_finished: str = kwargs.get('run_finished', "") or ""
        self.last_run: str = kwargs.get('last_run', "") or ""
        self.last_hit: str = kwargs.get('last_hit', "") or ""

    def __repr__(self) -> str:
        """Returns the string representation of the detection rule."""

        return f"Detection: {self.name} - {self.description} - {self.uuid}"

    def _should_run(self, catchup_period: int) -> bool:
        """Determines if the detection should run based on the last run time
        and the interval.

        Returns:
            bool: True if the detection should run, False otherwise
        """

        if hasattr(self, 'last_run'):

            # Convert the last run ISO8601 UTC string to a datetime object
            last_run = date_parser.isoparse(self.last_run)

            # Determine the next time the rule should run
            next_run = last_run + timedelta(minutes=self.interval)
            next_run = next_run.replace(tzinfo=None)

            # Determine the current time in UTC
            now = datetime.utcnow()

            # Compute the mute period on the last_hit property
            mute_time = now
            if hasattr(self, 'mute_period') and self.mute_period > 0:
                if hasattr(self, 'last_hit'):
                    last_hit = date_parser.isoparse(self.last_hit)
                    mute_time = last_hit + timedelta(seconds=self.mute_period * 60)
                    mute_time = mute_time.replace(tzinfo=None)

            if now > next_run and now >= mute_time:

                # Compute the delta between the next run and current times
                minutes_since = (now - next_run).total_seconds() / 60

                # If the delta is greater than 24 hours don't go beyond that
                if minutes_since > catchup_period:
                    self.lookbehind = math.ceil(self.lookbehind + catchup_period)
                elif minutes_since > self.lookbehind:
                    self.lookbehind = math.ceil(self.lookbehind + minutes_since)

                return True
        else:
            raise ValueError("Detection rule missing the last_run property")
        return False


if __name__ == "__main__":

    rule = Detection(
        name='Test Rule',
        description="This is just a test rule",
        uuid='1234567890',
        query=QueryConfig(
            query="event.code: 1",
            language="lucene",
            backend="elasticsearch"
        ),
        detection_id="1234567890",
        from_sigma=False,
        sigma_rule=None,
        sigma_rule_id=None,
        guide="Do something awesome",
        tags=["test", "rule"],
        tactics=[MITRETacticTechnique(
            mitre_id="1234567890",
            external_id="1234567890",
            name="Test Tactic",
            shortname="test_tactic"
        )],
        techniques=[MITRETacticTechnique(
            mitre_id="1234567890",
            external_id="1234567890",
            name="Test Technique",
            shortname="test_technique"
        )],
        references=["https://www.google.com"],
        false_positives=["https://www.google.com"],
        kill_chain_phase="test",
        rule_type_str="match",
        rule_type=RULE_TYPES.MATCH,
        version=1,
        active=True,
        warnings=[],
        source=SourceConfig(
            language="lucene",
            name="Test Source",
            uuid="1234567890"
        ),
        case_template="1234567890",
        risk_score=1,
        severity=1,
        signature_fields=["event.code"],
        observable_fields=[ObservableField(
            field="host.name",
            alias="host.name",
            data_type="host",
            tlp=1,
            tags=["test", "rule"]
        )],
        interval=30,
        lookbehind=30,
        catchup_period=1440,
        skip_event_rules=False,
        exceptions=[DetectionException(
            description="Test Exception",
            condition="is",
            values=["test"],
            field="host.name"
        )],
        mute_period=0,
        rule_type_config=BaseRuleTypeConfig(),
        assigned_agent="1234567890",
        last_run=(datetime.utcnow() - timedelta(days=2)).isoformat(),
    )

    print(rule)
    print(f"Last Run: {rule.last_run} | Should Run? {rule._should_run(1440)}")
    rule.last_run = datetime.utcnow().isoformat()
    print(f"Last Run: {rule.last_run} | Should Run? {rule._should_run(1440)}")
