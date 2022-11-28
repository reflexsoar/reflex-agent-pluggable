""" reflexsoar_agent/role/core/detector/detection.py

Defines the BaseDetection class that all other detection types should inherit
from.  This class provides the basic functionality for all detection types.
"""

from dataclasses import dataclass


@dataclass
class BaseDetection:
    pass
