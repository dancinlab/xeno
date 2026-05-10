# xeno 🛸

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.20102972.svg)](https://doi.org/10.5281/zenodo.20102972)

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

## Install

`hx install xeno` (hexa package manager — auto-resolves `dancinlab/xeno` via HX_ORGS probe order).

```bash
# 가장 흔한 경로 — registry probe (hexa-pkg → dancinlab → dancinlife)
hx install xeno

# 또는 GitHub shortform
hx install dancinlab/xeno

# 또는 로컬 path (개발 시)
hx install ~/core/xeno

# 또는 git URL
hx install https://github.com/dancinlab/xeno
```

설치 후:
- 실행 shim: `~/.hx/bin/xeno` → `cli/run.hexa` → `bin/xeno` (bash, full logic)
- 패키지 dir: `~/.hx/packages/xeno` (symlink to repo if local install)
- install hook: `install.hexa` 실행 — bin chmod + sister repo (anima/nexus/hive/hexa-brain) reachability probe (informational)

검증:
```bash
xeno --version              # → "xeno 0.1.0"
xeno status                 # → 4 sister repo + 7 substrate inventory
xeno cycle status           # → primary/fallback 자동 detect
```

업데이트 / 제거:
```bash
hx update xeno              # symlink refresh / git pull
hx remove xeno              # shim + symlink 제거
hx info xeno                # 설치 정보
```

## CLI use

`xeno` 단일 entry (8 topics, topic-dispatched).

### 기본 명령

```bash
xeno                                # alias for `xeno status` (default)
xeno --version                      # print version
xeno --help                         # topic list + 예제
xeno status                         # 4 sister repo reachability + 7 substrate inventory
xeno list                           # substrate inventory only (lines + vendor)
xeno fallback                       # degraded mode info (sister repo 없을 때 가용 항목)
```

### Sister repo 연동

```bash
xeno connect anima                  # anima reachability probe (rc=91 if 미달)
xeno connect nexus                  # nexus probe
xeno connect hive                   # hive probe
xeno connect hexa-brain             # hexa-brain probe
xeno connect all                    # 4개 동시 probe (bitmask rc)

xeno invoke anima status            # anima CLI 직접 passthrough
xeno invoke nexus drill --seed "X"  # nexus CLI passthrough
```

### Substrate roadmap

```bash
xeno roadmap                        # === xeno list 와 동일
xeno roadmap akida                  # .roadmap.akida 본문 출력
xeno roadmap loihi3                 # .roadmap.loihi3
xeno roadmap finalspark             # ... 7개 substrate 모두 가능
```

### Falsifier harness (nexus 12-falsifier copy SSOT)

```bash
xeno falsifier list                 # 12 falsifier × hardware 요구 × evidence 파일
xeno falsifier run F-C              # 단일 falsifier dispatch (validate_witness.py 등)
xeno falsifier run F-L7 --bits 200000 # 인자 passthrough
xeno falsifier all                  # eligible falsifier 일괄 (--hardware 옵션은 primary path 시)
xeno falsifier all --hardware       # AKD1000 primary 활성 시 8 post-arrival fire
```

### Akida cycle (own 35: PRIMARY + FALLBACK)

```bash
xeno cycle status                   # path auto-detect + primary/fallback 동시 표시
                                    #   ● PRIMARY active   → AKD1000 chip 활성
                                    #   ○ PRIMARY unavailable / ● FALLBACK active → cloud lane

# PRIMARY (AKD1000 RPi5 dev kit)
xeno cycle primary status           # === probe와 동일
xeno cycle primary probe            # akida.devices() 검증, rc=0=가용 / rc=91=불가
xeno cycle primary register         # nexus host_register.sh fire (host.rpi5-akida 등재)
xeno cycle primary run --hardware   # nexus runner.py --hardware 직접 fire

# FALLBACK (Akida Cloud)
xeno cycle prep                     # D-1 자동 prep (P0b smoke + P1 tarball + P0a generate)
xeno cycle connect                  # ssh akida-cloud (예약 슬롯 활성 시)
xeno cycle upload                   # P1 tarball rsync 업로드
xeno cycle run                      # cloud-side d0_run_all.sh (bootstrap + falsifier + anima N-2/N-3/N-5)
xeno cycle exfil                    # P6 결과 pull (anima + nexus + xeno destinations)
xeno cycle verdict                  # __AKIDA_R__ PASS|FAIL emit (PASS/FAIL count 기반)
```

### Exit codes

| code | 의미 |
|------|------|
| `0` | success |
| `1` | subcommand error (dispatched tool exit) |
| `2` | unknown topic / malformed invocation |
| `91` | connection failed (raw 91 honest C3 fail-loud — silent skip BANNED) |

### Environment

| var | default | 용도 |
|-----|---------|------|
| `XENO_ROOT` | `$HOME/core/xeno` (또는 `$HX_PKG_DIR`) | xeno repo root |
| `ANIMA_ROOT` | `$HOME/core/anima` | sister anima |
| `NEXUS_ROOT` | `$HOME/core/nexus` | sister nexus |
| `HIVE_ROOT` | `$HOME/core/hive` | sister hive |
| `HEXA_BRAIN_ROOT` | `$HOME/core/hexa-brain` | sister hexa-brain |
| `SCRATCH` | `$HOME/scratch` | tarball staging |

### 자주 쓰는 흐름

```bash
# 매 sessio start
xeno status                                  # 환경 sanity check

# D-1 (Akida Cloud cycle 전날)
xeno cycle status                            # 슬롯 + secret 확인
xeno cycle prep                              # P0b/P1/P0a 자동

# D+0 (cycle 시작, Sat 09:00 KST)
xeno cycle connect                           # ssh akida-cloud
xeno cycle upload                            # tarball 업로드
xeno cycle run                               # 8 falsifier + N-2/N-3/N-5

# D+1 (cycle 종료, Sun 08:00 KST 전)
xeno cycle exfil                             # 결과 pull
xeno cycle verdict                           # __AKIDA_R__ PASS|FAIL

# Chip 도착 후 (primary 자동 활성)
xeno cycle primary probe                     # 활성 검증
xeno cycle primary register                  # workspace 등재
xeno cycle primary run --hardware            # 8 falsifier physical fire
```

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

## Path policy (anima own 35)

**AKD1000 PRIMARY + Akida Cloud FALLBACK** — physical chip first, cloud is wait/maintenance backup.

| Path | Hardware | Workspace | When active |
|------|----------|-----------|-------------|
| **🟢 PRIMARY** | AKD1000 RPi5 dev kit ($1,495, 주문 2026-04-29) | `host.rpi5-akida` (`~/core/.workspace`) | chip 도착 + akida package + AKD1000 device probe rc=0 |
| **🟡 FALLBACK** | Akida Cloud (Colfax-hosted, ephemeral wipe-on-start) | `host.akida-cloud-colfax` (post-P0a generate) | chip 미수신 / 고장 / maintenance |

자동 detect: `python3 -c "import akida; akida.devices()"` rc → 0=primary, 비0=fallback.
Path field mandate: verdict.json + state file에 `path = "primary-physical" | "fallback-cloud"` 명시 (own 35 mandate-3).
raw 91 honest C3: fallback 사용 시 silent skip BANNED, 명시 emit ("USING FALLBACK: <reason>").

### Akida Cloud (FALLBACK lane — current state, chip ETA 미확정)

- Reservation: Sat 2026-05-09 09:00 KST → Sun 2026-05-10 09:00 KST (24h, secure wipe on start)
- Connection: `ssh akida-cloud` (config in user `~/.ssh/config`, key `~/.ssh/id_ed25519_akida`)
- Secrets: `secret list | grep akida_cloud` (10 keys in user secret store)
- Plan: `docs/anima_origin/akida_cloud_d_minus_1_prep_2026_05_08.md`
- 본 cycle = **fallback 활성 instance** (own 35 mandate-4) — chip 도착 후 primary 자동 활성, fallback deactivate

### AKD1000 PRIMARY (chip 도착 후 활성)

- Hardware: BrainChip Raspberry Pi 5 - AKD1000 Dev Kit ($1,495)
  - SoC: Broadcom BCM2712 2.4GHz quad-core Arm Cortex-A76 + 800MHz VideoCore VII GPU
  - RAM: 16GB LPDDR4 + AKD1000 M.2 card (B+M Key) on dev kit header
  - Includes Meta TF Software Development Environment
  - shop URL: https://shop.brainchipinc.com/products/akida™-development-kit-raspberry-pi-5-draft
- Workspace: `host.rpi5-akida` registered via nexus `scripts/akida/host_register.sh` (event-driven, F-L1 PASS evidence required)
- Activation trigger: chip 도착 → akida package install → host_register.sh fire → cycle path auto-flip
- CLI: `xeno cycle primary {status | probe | register | run [args]}`

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
