"""Small generic adapters useful to hosts and interface-level tests."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping

from .interfaces import AdapterRegistry, GateAdapter, StageAdapter


@dataclass
class DictAdapterRegistry(AdapterRegistry):
    stages: Mapping[str, StageAdapter] = field(default_factory=dict)
    gates: Mapping[str, GateAdapter] = field(default_factory=dict)

    def stage(self, name: str) -> StageAdapter:
        try:
            return self.stages[name]
        except KeyError as error:
            raise KeyError(f"unknown stage adapter: {name}") from error

    def gate(self, name: str) -> GateAdapter:
        try:
            return self.gates[name]
        except KeyError as error:
            raise KeyError(f"unknown gate adapter: {name}") from error
