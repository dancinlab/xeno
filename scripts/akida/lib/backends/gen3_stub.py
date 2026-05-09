"""Gen 3 — placeholder for next-generation Akida silicon (BC.A3.*).

No public hardware/SDK as of 2026-05. Backend exists so that:
  (1) `xeno cycle run --akida-gen 3` produces a clear 'not yet released'
      error rather than 'unknown gen' confusion.
  (2) When BC.A3.x SDK ships, only this file changes — no edits to
      registry/base.

Same skeleton applies for gen 4, 5, ... — duplicate this file, bump
constants, register.
"""
from __future__ import annotations
from typing import Any
from ..gen_base import Backend, NotAvailable
from ..gen_registry import register_backend


class Gen3StubBackend(Backend):
    generation = 3
    version_pattern = r"^BC\.A3\."
    marketing_name = "Akida 3 (unreleased)"

    def device_present(self) -> bool:
        return False

    def device_info(self) -> dict[str, Any]:
        return {
            "version":        None,
            "marketing_name": self.marketing_name,
            "generation":     3,
            "available":      False,
            "note":           "BC.A3.* SDK not released; backend is registered as forward-compat stub",
        }

    def mesh_summary(self) -> dict[str, Any]:
        raise NotAvailable("gen3 unreleased — stub only")

    def run_inference(self, model_path, n_events):
        raise NotAvailable("gen3 unreleased — stub only")

    def measure_power(self, n_events):
        return {
            "available":                False,
            "method":                   "unreleased",
            "vendor_estimate_required": False,
            "watts_idle":               None,
            "watts_inference":          None,
            "joules_per_event":         None,
            "note":                     "BC.A3.* not yet shipped",
        }

    def capture_spike_trace(self, n_steps, rate_hz):
        raise NotAvailable("gen3 unreleased — stub only")

    def capabilities(self) -> dict[str, bool]:
        return {k: False for k in super().capabilities()}


register_backend(3, Gen3StubBackend)
