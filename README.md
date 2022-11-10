# reflex-agent-pluggable

![Tests Status](./.badges/tests-badge.svg) ![Coverage](./.badges/coverage-badge.svg) ![Flake8](./.badges/flake8-badge.svg)

## Quick Start

```bash
pip install reflexsoar-agent
reflexsoar-agent --pair --console https://reflex.myconsole.com --token
```

## Recommended Start

1. Create a `.env` file with the following values

```bash
set REFLEX_AGENT_API_URL=https://reflex.myconsole.com
set REFLEX_API_KEY=keyhere
```

2. Run the following commands

```bash
pip install reflexsoar-agent
reflexsoar-agent --pair
```

## Command Line Usage

```
usage: reflexsoar-agent [-h] [--pair] [--start] [--console CONSOLE] [--token TOKEN] [--groups GROUPS] [--clear-persistent-config] [--reset-console-pairing RESET_CONSOLE_PAIRING] [--view-config] [--set-config-value SET_CONFIG_VALUE]
                        [--env-file ENV_FILE] [--heartbeat] [--offline]

options:
  -h, --help            show this help message and exit
  --pair                Pair the agent with the management server
  --start               Start the agent
  --console CONSOLE     The management server URL
  --token TOKEN         The management server access token
  --groups GROUPS       Groups this agent should be added to
  --clear-persistent-config
  --reset-console-pairing RESET_CONSOLE_PAIRING
                        Will reset the pairing for the agent with the supplied console address
  --view-config         View the agent configuration
  --set-config-value SET_CONFIG_VALUE
                        Set a configuration value. Format: <key>:<value>. If the target setting is a list provide each value separated by a comma
  --env-file ENV_FILE   The path to the .env file to load
  --heartbeat           Send a heartbeat to the management server
  --offline             Run the agent in offline mode
```

## Installing extensions

The ReflexSOAR Agent supports extending it's functionality by installing extensions via `pip` or `poetry` or your package manager of choice.

```bash
# Install the base reflexsoar-agent and an additional extension called hello
pip install reflexsoar-agent
pip install reflexsoar-agent-role-hello

# Assuming the agent is already paired
reflexsoar-agent --set-config-value roles:poller,detector,hello
reflexsoar-agent --start
```
