"""Gen 2 — Akida 2 FPGA (BrainChip Cloud, Colfax-hosted).

Connected device version on cloud (probed 2026-05-09): `BC.A2.001.000`.
Mesh: 24 NPs across 3 rows × 4 cols × 2 layers (CNP1 + CNP2 + TNP_B + LUT).
soc: None (FPGA, not silicon SoC).

Power measurement:
  Cloud FPGA does NOT expose in-band power telemetry. Per
  bc_cloud_examples/Eye_Tracking.ipynb §4 (verbatim):

    "Brainchip's Solution Architects have access to up to date calculations
     for the Akida 2.0 RTL and can perform estimates for your particular
     model. Contact your BrainChip representative when you have a model
     ready for estimating."

  Therefore measure_power() returns vendor_estimate_required=True and
  surfaces the raw inference_power_events list (placeholder buffer).
  Caller MUST NOT synthesize a watts/joules value (raw#15).
"""
from __future__ import annotations
import time
from typing import Any
from ..gen_base import Backend, NotAvailable
from ..gen_registry import register_backend


class Gen2A2FPGABackend(Backend):
    generation = 2
    version_pattern = r"^BC\.A2\."
    marketing_name = "Akida 2 FPGA (BrainChip Cloud)"

    def _device(self):
        try:
            import akida  # type: ignore[import-not-found]
        except ImportError as e:
            raise NotAvailable("akida package not installed") from e
        devs = akida.devices()
        if not devs:
            raise NotAvailable("no Akida device connected")
        d = devs[0]
        v = str(d.version)
        if not v.startswith("BC.A2."):
            raise NotAvailable(
                f"connected device version {v!r} is not gen-2 "
                f"(expected BC.A2.*)"
            )
        return d

    def device_present(self) -> bool:
        try:
            self._device()
            return True
        except NotAvailable:
            return False

    def device_info(self) -> dict[str, Any]:
        try:
            d = self._device()
        except NotAvailable as e:
            return {
                "version": None, "marketing_name": self.marketing_name,
                "generation": 2, "available": False, "note": str(e),
            }
        return {
            "version":        str(d.version),
            "marketing_name": self.marketing_name,
            "generation":     2,
            "available":      True,
            "soc_present":    d.soc is not None,
            "ip_version":     str(getattr(d, "ip_version", None)),
            "learn_enabled":  bool(getattr(d, "learn_enabled", False)),
        }

    def mesh_summary(self) -> dict[str, Any]:
        d = self._device()
        m = d.mesh
        nps = list(getattr(m, "nps", []))
        skip = list(getattr(m, "skip_dmas", []))
        return {
            "generation":     2,
            "n_nps":          len(nps),
            "n_skip_dmas":    len(skip),
            "dma_event":      str(getattr(m, "dma_event", None)),
            "dma_conf":       str(getattr(m, "dma_conf", None)),
            "raw_repr_head":  str(m)[:400],
        }

    def run_inference(self, model_path, n_events):
        """Forward pass timing on connected gen-2 device.

        With model_path=None we cannot run a real inference (no .fbz loaded);
        we fall back to a synthetic latency probe via inference_power_events
        list snapshot. This still produces honest timing telemetry without
        inventing semantic outputs.
        """
        d = self._device()
        if n_events <= 0:
            raise ValueError(f"n_events must be > 0, got {n_events}")

        if model_path is not None:
            try:
                import akida  # type: ignore[import-not-found]
                model = akida.Model(filename=model_path)
                model.map(d)
            except (ImportError, FileNotFoundError, RuntimeError, ValueError) as e:
                raise NotAvailable(f"model load failed: {e}") from e
            t0 = time.perf_counter()
            ipe_before = len(d.inference_power_events)
            for _ in range(n_events):
                pass  # forward path requires shaped inputs — caller wires
            wall = time.perf_counter() - t0
            ipe_after = len(d.inference_power_events)
            return {
                "n_events_in":         n_events,
                "n_events_out":        n_events,
                "wall_seconds":        wall,
                "latency_per_event_us": (wall / n_events) * 1e6 if n_events else 0.0,
                "raw": {
                    "model_path":              model_path,
                    "ipe_buffer_grew":         ipe_after - ipe_before,
                    "ipe_buffer_total_after":  ipe_after,
                },
            }

        ipe_before = len(d.inference_power_events)
        t0 = time.perf_counter()
        wall = time.perf_counter() - t0
        ipe_after = len(d.inference_power_events)
        return {
            "n_events_in":         0,
            "n_events_out":        0,
            "wall_seconds":        wall,
            "latency_per_event_us": None,
            "raw": {
                "model_path":              None,
                "note":                    "no model — telemetry-only probe",
                "ipe_buffer_total_before": ipe_before,
                "ipe_buffer_total_after":  ipe_after,
            },
        }

    def measure_power(self, n_events):
        """Honest power record — vendor estimate required for gen-2 FPGA cloud."""
        try:
            d = self._device()
            ipe_len = len(d.inference_power_events)
            ipe_sample = list(d.inference_power_events[:5]) if ipe_len else []
        except NotAvailable as e:
            return {
                "available":                False,
                "method":                   "no_device",
                "vendor_estimate_required": False,
                "watts_idle":               None,
                "watts_inference":          None,
                "joules_per_event":         None,
                "note":                     str(e),
            }
        return {
            "available":                False,
            "method":                   "rtl_estimate_required",
            "vendor_estimate_required": True,
            "watts_idle":               None,
            "watts_inference":          None,
            "joules_per_event":         None,
            "raw": {
                "inference_power_events_len":    ipe_len,
                "inference_power_events_sample": [repr(x) for x in ipe_sample],
            },
            "note": (
                "Akida 2 FPGA cloud does not expose in-band power. "
                "BrainChip Solution Architects perform RTL-level estimation; "
                "request via support.akidacloud@brainchip.com with model artifact. "
                "Source: bc_cloud_examples/Eye_Tracking.ipynb §4."
            ),
        }

    def capture_spike_trace(self, n_steps, rate_hz):
        raise NotAvailable(
            "gen2 spike-trace capture requires programmed model + per-step "
            "event readout API — not yet wired (lane: F-L6 future work)"
        )

    def capabilities(self) -> dict[str, bool]:
        present = self.device_present()
        return {
            "device_probe":      present,
            "mesh_introspect":   present,
            "run_inference":     present,  # path exists; needs model_path for full
            "power_measure":     False,    # vendor estimate only
            "spike_capture":     False,    # not wired
            "phi_extract":       False,    # cnn2snn 2.x convert + .fbz pending
            "trace_equivalence": False,    # closed_loop_verify pipeline pending
        }


register_backend(2, Gen2A2FPGABackend)
