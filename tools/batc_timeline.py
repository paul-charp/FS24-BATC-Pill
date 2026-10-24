"""Print a readable timeline from a sniff_batc.py log, to see how BeyondATC's state messages move
around an exchange (e.g. which pilot responses `Actions` offers while ATC waits for a readback). Stdlib only.

    python tools/batc_timeline.py                  the latest log in %LOCALAPPDATA%\\paul-batc-pill\\logs (sniff or pill)
    python tools/batc_timeline.py path\\to\\batc-X.jsonl --types Actions,InfoBoxes

Speech (ATC:, Player:, ...), CommsState, Facility and QueuedAction lines are printed as they come, and so are
the pill's own lines in a tools/pill_log.py log (PILL: what it showed, --: what you did).
For the state types (--types), only changes are printed, as added (+) and removed (-) items, so a
response appearing in the toolbar menu after a clearance stands out. The payload format doesn't need
to be known: JSON is flattened to `path = value` items, anything else is compared whole.
"""
import argparse
import json
import sys
from pathlib import Path

EVENTS = ("CommsState", "ATC", "ATCTraffic", "Player", "Traffic", "Facility", "Com2", "QueuedAction",
          "AppError", "RadioMute", "LoadState")


def flatten(value, path=""):
    if isinstance(value, dict):
        for k, v in value.items():
            yield from flatten(v, f"{path}.{k}" if path else str(k))
    elif isinstance(value, list):
        for i, v in enumerate(value):
            yield from flatten(v, f"{path}[{i}]")
    else:
        yield f"{path} = {json.dumps(value, ensure_ascii=False)}" if path else json.dumps(value, ensure_ascii=False)


def items(payload):
    if payload.startswith("[") and "\u00ac" in payload:  # Actions: [Readback IFR Clearance¬Say Again¬]
        return set(s for s in payload[1:-1].split("\u00ac") if s)
    try:
        return set(flatten(json.loads(payload)))
    except ValueError:
        return {payload}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("log", nargs="?", help="log file (default: the latest in the logs folder)")
    ap.add_argument("--types", default="Actions,InfoBoxes", help="state types to diff (comma-separated)")
    ap.add_argument("--all", action="store_true", help="also print every other message type once per change")
    args = ap.parse_args()

    if args.log:
        path = Path(args.log)
    else:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        import pill_log  # the logs folder all tools share
        d = pill_log.log_dir()
        logs = sorted(d.glob("*.jsonl"), key=lambda p: p.stat().st_mtime) if d.exists() else []
        if not logs:
            sys.exit(f"timeline: no log in {d}: run tools/sniff_batc.py or tools/pill_log.py first")
        path = logs[-1]
    diffed = set(t for t in args.types.split(",") if t)
    seen = {}
    print(f"timeline: {path}")
    for line in path.open(encoding="utf-8"):
        rec = json.loads(line)
        t = rec["t"]
        if "msg" not in rec:  # a pill_log.py line
            if "pill" in rec:
                print(f"{t:8.2f}  {'PILL':<12} {rec['pill'][:160]}")
            elif "event" in rec:
                print(f"{t:8.2f}  {'--':<12} {rec['event'][:160]}")
            continue
        msg = rec["msg"]
        typ, _, payload = msg.partition(":")
        payload = payload.strip()
        if typ in EVENTS:
            print(f"{t:8.2f}  {typ:<12} {payload[:160]}")
        elif typ in diffed or args.all:
            new = items(payload)
            old = seen.get(typ)
            seen[typ] = new
            if old is None:
                print(f"{t:8.2f}  {typ:<12} (first, {len(new)} items)")
                for s in sorted(new):
                    print(f"{'':10}{'':13}  {s[:160]}")
            elif new != old:
                for s in sorted(old - new):
                    print(f"{t:8.2f}  {typ:<12} - {s[:160]}")
                for s in sorted(new - old):
                    print(f"{t:8.2f}  {typ:<12} + {s[:160]}")


if __name__ == "__main__":
    main()
