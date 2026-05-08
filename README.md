# xeno 🛸

**Standalone repo for non-GPU exotic compute substrate research.**

Tier C scope — silicon neuromorphic + biological organoid + quantum + random:

| Substrate | Vendor / Source | Roadmap |
|-----------|----------------|---------|
| AKIDA AKD1000 | BrainChip | `roadmaps/.roadmap.akida` |
| Loihi3 | Intel | `roadmaps/.roadmap.loihi3` |
| Northpole | IBM | `roadmaps/.roadmap.northpole` |
| FinalSpark | FinalSpark organoid | `roadmaps/.roadmap.finalspark` |
| Cortical Labs DishBrain | Cortical Labs | `roadmaps/.roadmap.cortical_labs` |
| IonQ | Quantum gate | `roadmaps/.roadmap.ionq` |
| QRNG | Quantum random number | `roadmaps/.roadmap.qrng` |

## Origin

Extracted 2026-05-08 from 4 source repos (`~/core/anima`, `~/core/nexus`, `~/core/hive`, `~/core/hexa-brain`) per anima `.own` own 34 (xeno standalone SSOT).

Source repo files **copied** (not yet moved) — original files retained until D+0/D+1 Akida Cloud cycle (Sat 2026-05-09 09:00 KST → Sun 2026-05-10 09:00 KST) completes. Post-cycle stubification + cross-link cleanup will land in source repos as Phase 1.5.

## Layout

```
roadmaps/             7 .roadmap.* — substrate-specific SSOT
scripts/akida/
  anima_origin/       8 files (Phi/trace + runner)
  nexus_origin/       19 files (12 falsifier harness + utilities)
  hive_origin/
    tool/             24 .hexa modules (alpha/delta/theta layers + neuromorphic)
    tests/            3 integration tests
    docs/             1 omega cycle integration doc
  hexa_brain_origin/  2 EEG cross-substrate spec (N-2 spike pipeline)
scripts/loihi3/       (placeholder, Phase 1.5)
scripts/northpole/    (placeholder, Phase 1.5)
scripts/finalspark/   (placeholder, Phase 1.5)
scripts/cortical_labs/ (placeholder, Phase 1.5)
scripts/ionq/         (placeholder, Phase 1.5)
scripts/qrng/         (placeholder, Phase 1.5)
state/                evidence + state dirs from anima + nexus
design/kick/          14 omega cycle witness files
n6/                   10 atlas append files (nexus origin)
docs/                 5 docs (anima cloud setup + nexus dev kit eval + N-substrate roadmap)
```

## Akida Cloud — D+0/D+1 cycle (active)

- Reservation: Sat 2026-05-09 09:00 KST → Sun 2026-05-10 09:00 KST (24h, secure wipe on start)
- Connection: `ssh akida-cloud` (config in user `~/.ssh/config`, key `~/.ssh/id_ed25519_akida`)
- Secrets: `secret list | grep akida_cloud` (10 keys in user secret store)
- Plan: `docs/anima_origin/akida_cloud_d_minus_1_prep_2026_05_08.md`

## Trinity compliance (anima own 33)

xeno repo는 anima trinity (.roadmap.philosophy + .roadmap.law + .roadmap.hypothesis) 3 도메인 외 별도 lane. 본 repo의 행위는 anima trinity 정합 cross-check 후 emit.

- A 철학: D3 substrate-coupled paradigm — 본 repo의 모든 substrate가 D3 substrate-coupled 검증 lane
- B 법칙: own 16 cost watchdog + own 30 checkpoint preservation + own 32/33/34 trinity bundle + standalone authority
- C 가설: H1 raw#12 cycle (4-stage hypothesis) — 본 repo 각 substrate별 falsifier가 H lane fire 인스턴스

## Cross-link

- anima `.own` own 34 — xeno standalone SSOT 선언
- anima `.roadmap.akida` — 원본 (xeno로 copy 완료, Phase 1.5에서 stub로 전환)
- anima `docs/akida_cloud_*_2026_05_08.md` — Akida Cloud setup + D-1 prep
- nexus `scripts/akida/README.md` — 12-falsifier harness 인덱스 (xeno로 copy 완료)
- hive `tool/akida_*.hexa` — alpha/delta/theta layer 모듈 (xeno로 copy 완료)
- hexa-brain `eeg/doc/cross_substrate/*akida*` — N-2 EEG→AKIDA spike pipeline spec (xeno로 copy 완료)
