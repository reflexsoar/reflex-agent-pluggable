import pytest

from reflexsoar_agent.core.config import AgentPolicy

def test_agent_policy():
	policy_dict = {
		"agent.heartbeat_interval": 30,
		"agent.logging.level": "INFO",
		"agent.logging.remote.enabled": True,
		"agent.logging.remote.rate_limit": 1000,
		"agent.logging.local.max_files": 10,
		"agent.logging.local.max_size": 5,
		"agent.logging.local.path": "/var/log/reflexsoar/",
		"agent.logging.local.compress": True,
		"agent.logging.local.compression_level": 6,
		"agent.managers.intel.max_db_size": "30",
		"agent.managers.event.signature_cache_ttl": 3600,
		"agent.roles.enabled": ['poller','guardicore'],
		"agent.roles.core.poller.max_concurrent_inputs": 5,
		"agent.roles.core.poller.max_input_attempts": 3,
		"agent.roles.core.poller.wait_interval": 10,
		"agent.roles.core.detector.max_concurrent_rules": 25,
		"agent.roles.core.detector.wait_interval": 10,
		"agent.roles.core.detector.max_catchup_peroid": 60,
		"agent.roles.core.detector.max_threshold_events": 1000,
		"agent.roles.core.runner.max_concurrent_actions": 10,
		"agent.roles.core.runner.wait_interval": 10,
		"agent.roles.custom.guardicore.wait_interval": 60,
	}

	policy = AgentPolicy(policy_dict)
	assert policy.agent.heartbeat_interval == 30
	assert policy.agent.logging.level == "INFO"
	assert policy.policy['agent']['heartbeat_interval'] == 30
	assert policy.setting('agent.heartbeat_interval') == 30

	with pytest.raises(KeyError):
		assert policy.setting('i.do.not.exist') == None
