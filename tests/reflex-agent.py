from loguru import logger

from reflexsoar_agent import Agent

agent_config = {
    'name': 'test-agent',
    'roles': ['ilm', 'poller'],
    'role_configs': {
        'ilm_role_config': {
            'rule_refresh_interval': 60
        }
    }
}

logger.info('Starting agent')
agent = Agent()
agent.load_persistent_config()
logger.info(f"Available Agent Roles: {[*agent.loaded_roles.keys()]}")
logger.info(f"Agent configured with roles: {agent.roles}")
logger.warning(f"Agent Role Warnings: {agent.warnings}")
logger.info(f"Available Inputs: {[*agent.loaded_inputs.keys()]}")

#agent.save_persistent_config()