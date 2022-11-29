"""reflexsoar_agent/role/core/detector/rule.py"""

from dataclasses import dataclass


class RuleTypes:

    MATCH = 0
    THRESHOLD = 1
    METRIC = 2
    MISMATCH = 3
    NEW_TERM = 4


@dataclass
class BaseRuleTypeConfig:
    """A base class for definining different configuration parameters
    for all detection rule types
    """

    pass


@dataclass
class BaseRuleType:
    """Base class for all detection types.

    This class provides the basic functionality for all detection types.
    """

    rule_type: str
    description: str
    backend: str


RULE_TYPES = RuleTypes()
