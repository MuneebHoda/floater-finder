#!/usr/bin/env python3
"""Run after installing the project into its environment."""
import json
from floater_finder.cli import inspect_environment

print(json.dumps(inspect_environment(), indent=2))
