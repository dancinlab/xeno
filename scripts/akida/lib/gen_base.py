"""Backend abstract interface — every Akida generation impl satisfies this."""
from __future__ import annotations
from typing import Any


class BackendError(Exception):
    """Backend method genuinely failed (hardware/runtime error)."""


class NotAvailable(BackendError):
    """Capability not provided by this generation (honest fail-loud).

    Distinct from BackendError: caller should treat as 'capability gap',
    not 'measurement error'. Falsifier verdict path: BLOCKED-CAPABILITY-GAP.
    """


class Backend:
    """Per-generation Akida substrate adapter.

    Subclass contract:
      * generation        : int    (1, 2, 3, ...)
      * version_pattern   : str    (regex on device.version, group(1) = gen num)
      * marketing_name    : str    ("AKD1000", "Akida 2 FPGA", ...)

    Methods raise NotAvailable when the underlying hardware/SDK does not
    expose the capability. Falsifier scripts catch NotAvailable and emit
    honest BLOCKED-* verdicts rather than synthesizing fake values.
    """

    generation: int = 0
    version_pattern: str = r"^BC\.A0\."
    marketing_name: str = "unknown"

    def device_present(self) -> bool:
        raise NotImplementedError

    def device_info(self) -> dict[str, Any]:
        """Return {version, marketing_name, generation, mesh_summary}."""
        raise NotImplementedError

    def mesh_summary(self) -> dict[str, Any]:
        """NP count, layer types available, dma config — capability snapshot."""
        raise NotImplementedError

    def run_inference(self, model_path: str | None, n_events: int) -> dict[str, Any]:
        """Deploy model (or empty/synthetic) + run n_events forward passes.

        Returns:
            {
              "n_events_in":  int,
              "n_events_out": int,
              "wall_seconds": float,
              "latency_per_event_us": float,
              "raw": {...gen-specific telemetry...},
            }
        """
        raise NotImplementedError

    def measure_power(self, n_events: int) -> dict[str, Any]:
        """Return power measurement OR honest 'not-available' record.

        Schema:
            {
              "available":               bool,
              "method":                  str,   # "rapl" | "rtl_estimate_required" | ...
              "vendor_estimate_required": bool,
              "watts_idle":               float | None,
              "watts_inference":          float | None,
              "joules_per_event":         float | None,
              "note":                     str,
            }

        gen2 (Akida 2 FPGA) returns vendor_estimate_required=True per
        bc_cloud_examples notebook directive. Caller must NOT synthesize
        a value when available=False (raw#15 fail-loud).
        """
        raise NotImplementedError

    def capture_spike_trace(self, n_steps: int, rate_hz: float) -> dict[str, Any]:
        """Spike-trace capture. Used by F-L6 (Lyapunov sweep) + F-L7 (entropy)."""
        raise NotImplementedError

    def capabilities(self) -> dict[str, bool]:
        """Boolean snapshot of which falsifier lanes this backend supports."""
        return {
            "device_probe":      False,
            "mesh_introspect":   False,
            "run_inference":     False,
            "power_measure":     False,
            "spike_capture":     False,
            "phi_extract":       False,
            "trace_equivalence": False,
        }
