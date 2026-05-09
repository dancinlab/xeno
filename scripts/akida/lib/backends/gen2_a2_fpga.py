"""Gen 2 — Akida 2 FPGA (BrainChip Cloud, Colfax-hosted).

Connected device version on cloud (probed 2026-05-09): `BC.A2.001.000`.
Mesh: 24 NPs, ip_version=v2, soc=None (FPGA emulation, not silicon).

Power measurement:
  Cloud FPGA does NOT expose in-band power telemetry. Per
  bc_cloud_examples/Eye_Tracking.ipynb §4 (verbatim):

    "Brainchip's Solution Architects have access to up to date calculations
     for the Akida 2.0 RTL and can perform estimates for your particular
     model. Contact your BrainChip representative when you have a model
     ready for estimating."

  measure_power() therefore returns vendor_estimate_required=True with
  available=False — callers must NOT synthesize a watts/joules value (raw#15).

Forward pass: int8 inputs required (`m.forward()` rejects uint8).
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

    # ---- device-level ----

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
                f"connected device version {v!r} is not gen-2 (expected BC.A2.*)"
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
            "generation":    2,
            "n_nps":         len(nps),
            "n_skip_dmas":   len(skip),
            "dma_event":     str(getattr(m, "dma_event", None)),
            "dma_conf":      str(getattr(m, "dma_conf", None)),
            "raw_repr_head": str(m)[:400],
        }

    # ---- model-level ----

    def _load_and_map(self, model_path: str):
        try:
            import akida  # type: ignore[import-not-found]
        except ImportError as e:
            raise NotAvailable("akida package not installed") from e
        d = self._device()
        try:
            model = akida.Model(filename=model_path)
            model.map(d)
        except (FileNotFoundError, RuntimeError, ValueError, OSError) as e:
            raise NotAvailable(f"model load/map failed: {e}") from e
        return d, model

    def forward(self, model_path: str, inputs) -> dict[str, Any]:
        try:
            import numpy as np  # type: ignore[import-not-found]
        except ImportError as e:
            raise NotAvailable("numpy not installed") from e
        if not isinstance(model_path, str) or not model_path:
            raise ValueError("forward() requires model_path")

        d, model = self._load_and_map(model_path)

        if inputs.dtype != np.int8:
            raise ValueError(
                f"Akida 2 forward() requires int8 inputs; got {inputs.dtype}"
            )

        ipe_before = len(d.inference_power_events)
        t0 = time.perf_counter()
        outputs = model.forward(inputs)
        wall = time.perf_counter() - t0
        ipe_after = len(d.inference_power_events)

        n_events = int(inputs.shape[0]) if inputs.ndim >= 1 else 1
        return {
            "outputs":             outputs,
            "wall_seconds":        wall,
            "n_events":            n_events,
            "latency_per_event_us": (wall / n_events) * 1e6 if n_events else 0.0,
            "input_shape":         tuple(inputs.shape),
            "output_shape":        tuple(outputs.shape),
            "input_dtype":         str(inputs.dtype),
            "output_dtype":        str(outputs.dtype),
            "raw": {
                "model_path":         model_path,
                "ipe_buffer_growth":  ipe_after - ipe_before,
                "ipe_buffer_total":   ipe_after,
                "model_input_shape":  tuple(model.input_shape),
                "model_output_shape": tuple(model.output_shape),
            },
        }

    def run_inference(self, model_path, n_events):
        try:
            import numpy as np  # type: ignore[import-not-found]
        except ImportError as e:
            raise NotAvailable("numpy not installed") from e
        if n_events <= 0:
            raise ValueError(f"n_events must be > 0, got {n_events}")

        if model_path is None:
            d = self._device()
            return {
                "outputs":             None,
                "n_events":            0,
                "wall_seconds":        0.0,
                "latency_per_event_us": None,
                "raw": {
                    "model_path": None,
                    "note":       "no model — telemetry-only probe",
                    "ipe_total":  len(d.inference_power_events),
                },
            }

        d, model = self._load_and_map(model_path)
        in_shape = tuple(model.input_shape)
        rng = np.random.default_rng(seed=42)
        X = rng.integers(-128, 127, size=(n_events, *in_shape), dtype=np.int8)

        ipe_before = len(d.inference_power_events)
        t0 = time.perf_counter()
        outputs = model.forward(X)
        wall = time.perf_counter() - t0
        ipe_after = len(d.inference_power_events)

        return {
            "outputs":             None,
            "n_events":            n_events,
            "wall_seconds":        wall,
            "latency_per_event_us": (wall / n_events) * 1e6,
            "input_shape":         tuple(X.shape),
            "output_shape":        tuple(outputs.shape),
            "raw": {
                "model_path":        model_path,
                "ipe_buffer_growth": ipe_after - ipe_before,
                "ipe_buffer_total":  ipe_after,
                "outputs_summary": {
                    "min":  float(outputs.min()),
                    "max":  float(outputs.max()),
                    "mean": float(outputs.mean()),
                    "std":  float(outputs.std()),
                },
                "input_seed": 42,
            },
        }

    def measure_power(self, n_events):
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

    def capture_spike_trace(self, model_path, n_steps, batch_size=1):
        try:
            import numpy as np  # type: ignore[import-not-found]
        except ImportError as e:
            raise NotAvailable("numpy not installed") from e
        if not isinstance(model_path, str) or not model_path:
            raise NotAvailable("spike_trace requires model_path (no synthetic dynamics)")
        if n_steps <= 0:
            raise ValueError(f"n_steps must be > 0, got {n_steps}")

        d, model = self._load_and_map(model_path)
        in_shape = tuple(model.input_shape)
        rng = np.random.default_rng(seed=7)

        trace = []
        ipe_before = len(d.inference_power_events)
        for step in range(n_steps):
            x = rng.integers(-128, 127, size=(batch_size, *in_shape), dtype=np.int8)
            t0 = time.perf_counter()
            y = model.forward(x)
            dt = time.perf_counter() - t0
            trace.append({
                "step":          step,
                "latency_us":    dt * 1e6,
                "out_norm_l2":   float(np.linalg.norm(y.astype(np.float32))),
                "out_mean_abs":  float(np.abs(y).mean()),
                "out_min":       float(y.min()),
                "out_max":       float(y.max()),
            })
        ipe_after = len(d.inference_power_events)

        return {
            "n_steps":     n_steps,
            "batch_size":  batch_size,
            "model_path":  model_path,
            "trace":       trace,
            "raw": {
                "ipe_buffer_growth": ipe_after - ipe_before,
                "ipe_buffer_total":  ipe_after,
                "input_seed":        7,
            },
        }

    # ---- capability matrix ----

    def capabilities(self) -> dict[str, bool]:
        present = self.device_present()
        return {
            "device_probe":    present,
            "mesh_introspect": present,
            "forward":         present,
            "run_inference":   present,
            "power_measure":   False,
            "spike_capture":   present,
        }


register_backend(2, Gen2A2FPGABackend)
