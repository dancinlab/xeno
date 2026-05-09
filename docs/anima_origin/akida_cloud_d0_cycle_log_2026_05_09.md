# Akida Cloud D+0 Cycle Log — 2026-05-09

**Reservation**: 2026-05-08 17:00 PDT → 2026-05-09 17:00 PDT (≡ 2026-05-09 09:00 KST → 2026-05-10 09:00 KST, 24h)
**Platform**: BrainChip Akida Cloud (Colfax-hosted)
**Cross-ref**: `akida_cloud_setup_log_2026_05_08.md` (D-1 setup), `akida_cloud_d_minus_1_prep_2026_05_08.md` (D-1 prep)

## Timeline

| Time (KST) | Action | Result |
|------|--------|--------|
| 09:21 | First successful `ssh akida-cloud` | Ubuntu 22.04.5 / 20 cores / 31 GiB / `bc_cloud_examples` staged |
| 09:22 | P1 tarball staged + uploaded (4.3M, 1046 entries) | OK |
| 09:24 | Cloud-side bootstrap via `~/.conda/envs/akida_env` | akida 2.18.2 + cnn2snn + akida_models pre-installed |
| 09:26 | First `runner.py --hardware` fire (10 falsifier) | mixed: 4 PASS (sim) + 6 BLOCKED/STUB |
| 09:34 | Hardware introspect — `device.version` = **`BC.A2.001.000`** | 결정적 발견: **Akida 2 FPGA, NOT AKD1000** |
| 09:38 | bc_cloud_examples power 검토 | RTL estimate vendor-side only (in-band 측정 미제공) |
| 09:42 | xeno generation framework land (`scripts/akida/lib/`) | gen1/gen2/gen3 backends + auto-detect registry |
| 09:45 | `cycle_runner probe` + `measure` on gen2 | 첫 honest evidence emit (gen2_measure_20260509T004512Z.json) |

## 결정적 발견 1: 하드웨어 mismatch

- **D-1 plan 가정**: AKD1000 (Akida 1.x silicon, RPi5 + M.2 dev kit)
- **Cloud 실제**: `BC.A2.001.000` = **Akida 2 FPGA** (다른 architecture, FPGA RTL emulation)
- **mesh**: 24 NPs (Neural Processors) — 3 rows × 4 cols × 2 layers, types CNP1/CNP2/FNP2/FNP3/TNP_B
- **soc**: None (FPGA, not silicon SoC)
- **ip_version**: `IpVersion.v2`

## 결정적 발견 2: in-band power 측정 미제공

`bc_cloud_examples/Eye_Tracking.ipynb §4` (verbatim):

> "Brainchip's Solution Architects have access to up to date calculations for the Akida 2.0 RTL and can perform estimates for your particular model. Contact your BrainChip representative when you have a model ready for estimating."

- `inference_power_events`는 placeholder list (현재 길이 0, populate 메커니즘 미문서화)
- F-L1 (J/op energy) lane은 cloud 환경에서 **vendor estimate 요청 path**로만 가능
- raw#15 fail-loud — cloud-side에서 wattage synthesis 금지

## 1차 fire 결과 (D-1 plan, AKD1000 가정)

| F-id | Verdict | 이유 |
|------|---------|------|
| F-C | ✅ PASS | architectural |
| F-L7 | ✅ PASS | QRNG entropy (200K bits) |
| F-M2 | ⚠️ PLAUSIBLE-PASS | gzip simulator |
| F-M3a | ❌ NO-EVIDENCE | `~/core/.workspace` Mac registry 의존 |
| F-L1 | ⚠️ PARTIAL-SIMULATOR | `--simulator` flag 박힘 |
| F-L1+ | ⚠️ PARTIAL-SIMULATOR | 동일 |
| F-L6 | ❌ STUB | hardware path `NotImplementedError` |
| F-M1 | ⚠️ PLAUSIBLE-PASS | Gödel disagreement (1000 progs) |
| F-A | ❌ MISSING | `cli/blowup/run.hexa` tarball 누락 |
| F-B | ❌ FAIL | anima/hbio/hsscb verify target 미존재 |
| F-M3b | ❌ BLOCKED | cnn2snn convert + .fbz pipeline 미land |
| F-M4 | ❌ MISSING | `~/core/anima/ready/experiments/closed_loop_verify.py` 절대경로 |

→ 8개 hardware-required falsifier 중 0개가 Akida 2 FPGA에서 fire 가능.

## 대응: xeno generation-aware framework land

**구조** (own 34 mandate-4 정합 — anima/nexus 직접 미터치):

```
xeno/scripts/akida/
├── cycle_runner.py            # CLI: probe / capabilities / measure
└── lib/
    ├── __init__.py
    ├── gen_base.py            # Backend abstract interface
    ├── gen_registry.py        # auto-detect (regex BC.A(N).* → gen N)
    └── backends/
        ├── _unknown.py        # fallback (no device or unrecognized version)
        ├── gen1_akd1000.py    # AKD1000 (NotAvailable until dev kit lands)
        ├── gen2_a2_fpga.py    # Akida 2 FPGA (live on cloud)
        └── gen3_stub.py       # forward-compat for BC.A3.* (unreleased)
```

**CLI flag**: `--akida-gen {auto, 1, 2, 3, ...}` — default `auto`.

**미래 호환**: `register_backend(N, GenNBackendCls)` 한 줄 추가로 새 세대 land. 예: BC.A4.x 출시 시 `gen4_*.py` 한 파일만 작성.

**honest fail-loud**: 미지원 capability는 `NotAvailable` raise → `BLOCKED-CAPABILITY-GAP` verdict. Wattage 등 측정 불가능 항목은 `available: false`, `vendor_estimate_required: true`로 명시 — synthesis 금지.

## 첫 valid Akida 2 evidence (cycle_runner measure)

`state/akida_cloud_d0_2026_05_09/gen2_measure_20260509T004512Z.json`:

```json
{
  "device_info": {
    "version": "BC.A2.001.000",
    "marketing_name": "Akida 2 FPGA (BrainChip Cloud)",
    "ip_version": "IpVersion.v2",
    "learn_enabled": false
  },
  "mesh_summary": {
    "n_nps": 24,
    "n_skip_dmas": 1,
    "dma_event": "(1, 1, 0)",
    "dma_conf": "(1, 1, 1)"
  },
  "power": {
    "available": false,
    "method": "rtl_estimate_required",
    "vendor_estimate_required": true,
    "note": "Akida 2 FPGA cloud does not expose in-band power..."
  },
  "capabilities": {
    "device_probe": true,
    "mesh_introspect": true,
    "run_inference": true,
    "power_measure": false,
    "spike_capture": false,
    "phi_extract": false,
    "trace_equivalence": false
  }
}
```

## 학술적 결과 vs framework 결과

- **학술적 (8 falsifier hardware fire)**: 0개 fire 가능 — Akida 1↔2 architecture gap + cloud RTL estimate 정책
- **Framework**: gen-registry + auto-detect + honest capability gating land (xeno/scripts/akida/lib)
- **첫 valid Akida 2 evidence**: device_info + mesh_summary 측정 OK; power/spike/phi/trace는 honest BLOCKED

## D+0 잔여 작업

- [ ] vendor estimate 요청 (support.akidacloud@brainchip.com) — F-L1 lane 진행 path
- [ ] gen2_a2_fpga.run_inference 실모델 path: bc_cloud_examples 중 1개 (Eye_Tracking 등) .fbz를 mount해 latency 측정
- [ ] cnn2snn convert pipeline: anima 측 phi_extractor + Akida 2 deploy (D+1 후 anima repo 작업)
- [ ] D+1 close 전 exfil (P6) — `state/akida_cloud_d0_2026_05_09/` Mac side rsync

## Cross-link

- `akida_cloud_setup_log_2026_05_08.md` — D-1 setup (SSH config, secrets)
- `akida_cloud_d_minus_1_prep_2026_05_08.md` — D-1 prep checklist
- `xeno/scripts/akida/cycle_runner.py` — generation-aware CLI entry
- `xeno/scripts/akida/lib/` — backend SSOT (own 34 mandate-4 정합)
- `state/akida_cloud_d0_2026_05_09/` — D+0 evidence emit dir
- BrainChip support: `support.akidacloud@brainchip.com` (RTL estimate 요청 endpoint)
