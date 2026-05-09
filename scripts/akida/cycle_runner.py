"""xeno generation-aware Akida cycle runner.

Subcommands:
  probe          device version + auto-detected gen + capabilities table
  capabilities   per-gen capability matrix (works without device)
  measure        run minimal inference + emit honest measurement record

Flag:
  --akida-gen {auto, 1, 2, 3, ...}    default: auto

Exit codes:
  0   success
  1   usage / arg error
  2   no device / unknown gen (fallback path taken)
  91  honest fail-loud (capability gap surfaced — raw#15)
"""
from __future__ import annotations
import argparse, json, os, sys, time

# cycle_runner.py lives at xeno/scripts/akida/, lib package is sibling.
_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

from lib import (  # noqa: E402
    Backend, BackendError, NotAvailable,
    detect_generation, get_backend, list_generations, REGISTRY,
)


def _emit(obj) -> None:
    print(json.dumps(obj, indent=2, default=str))


def cmd_probe(args) -> int:
    detected = detect_generation()
    backend = get_backend(args.akida_gen)
    out = {
        "ts":                time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "requested_gen":     args.akida_gen,
        "detected_gen":      detected,
        "backend_class":     type(backend).__name__,
        "backend_gen":       backend.generation,
        "marketing_name":    backend.marketing_name,
        "device_info":       backend.device_info(),
        "capabilities":      backend.capabilities(),
        "registered_gens":   list_generations(),
    }
    _emit(out)
    return 0 if backend.device_present() else 2


def cmd_capabilities(args) -> int:
    table = {}
    for gen in list_generations():
        b = REGISTRY[gen]()  # instantiate without device probe
        table[gen] = {
            "marketing_name":  b.marketing_name,
            "version_pattern": b.version_pattern,
            "capabilities":    b.capabilities(),
        }
    _emit({"registered_generations": table})
    return 0


def cmd_measure(args) -> int:
    backend = get_backend(args.akida_gen)
    info = backend.device_info()
    if not info.get("available"):
        _emit({
            "verdict":    "BLOCKED-NO-DEVICE",
            "device_info": info,
            "note":       "no device for requested gen; honest stop (raw#15 fail-loud)",
        })
        return 91

    record = {
        "ts":           time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "backend":      type(backend).__name__,
        "generation":   backend.generation,
        "device_info":  info,
        "mesh_summary": _safe_call(backend.mesh_summary),
        "inference":    _safe_call(lambda: backend.run_inference(args.model, args.n_events)),
        "power":        _safe_call(lambda: backend.measure_power(args.n_events)),
        "capabilities": backend.capabilities(),
    }
    _emit(record)

    if args.out_dir:
        os.makedirs(args.out_dir, exist_ok=True)
        ts = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
        path = os.path.join(args.out_dir, f"gen{backend.generation}_measure_{ts}.json")
        with open(path, "w") as f:
            json.dump(record, f, indent=2, default=str)
        print(f"[written] {path}", file=sys.stderr)
    return 0


def _safe_call(thunk):
    try:
        return thunk()
    except NotAvailable as e:
        return {"available": False, "reason": "NotAvailable", "detail": str(e)}
    except BackendError as e:
        return {"available": False, "reason": "BackendError", "detail": str(e)}


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(prog="xeno-akida-cycle")
    p.add_argument(
        "--akida-gen", default="auto",
        help="generation: 'auto' (detect from device.version) or int (1, 2, 3, ...). "
             f"registered: {list_generations()}",
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("probe", help="detect device + show capabilities")
    sp.set_defaults(func=cmd_probe)

    sp = sub.add_parser("capabilities", help="capability matrix across all registered gens")
    sp.set_defaults(func=cmd_capabilities)

    sp = sub.add_parser("measure", help="run minimal inference + emit honest record")
    sp.add_argument("--model", default=None, help=".fbz model path (optional)")
    sp.add_argument("--n-events", type=int, default=1000)
    sp.add_argument("--out-dir", default=None)
    sp.set_defaults(func=cmd_measure)

    args = p.parse_args(argv[1:])
    try:
        return args.func(args)
    except BackendError as e:
        _emit({"error": "BackendError", "detail": str(e)})
        return 91


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
