from datetime import datetime, timedelta
import pytest

from reflexsoar_agent.role.core.detector.detection import Detection, DetectionException, MITRETacticTechnique, ObservableField, QueryConfig, SourceConfig
from reflexsoar_agent.role.core.detector.rule import RULE_TYPES, BaseRuleTypeConfig


@pytest.fixture
def rule():
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
        interval=5,
        lookbehind=30,
        catchup_period=1440,
        skip_event_rules=False,
        exceptions=[DetectionException(
            description="Test Exception",
            condition="is",
            values=["test"],
            field="host.name"
        )],
        mute_period=300,
        rule_type_config=BaseRuleTypeConfig(),
        assigned_agent="1234567890",
        last_run=(datetime.utcnow() - timedelta(days=2)).isoformat(),
        last_hit=(datetime.utcnow() - timedelta(days=1)).isoformat()
    )
    return rule


def test_detection_rule(rule):

    # Test that the minutes since last run is more than the catchup period
    assert rule._should_run(1440) is True

    # Test that the minutes since last run is less than the catchup period
    rule.last_run = datetime.utcnow().isoformat()
    assert rule._should_run(1440) is False

    # Test that minutes since is greater than lookbehind
    rule.last_run = (datetime.utcnow() - timedelta(minutes=1570)).isoformat()
    assert rule._should_run(2500) is True

    # Assert that __repr__ is working
    assert str(rule) == "Detection: Test Rule - This is just a test rule - 1234567890"

def test_detection_rule_missing_last_run(rule):

    delattr(rule, 'last_run')
    with pytest.raises(ValueError):
        rule._should_run(1440)
