"""Log every message from BeyondATC's toolbar socket (ws://127.0.0.1:41716) with timestamps. Stdlib only.

    python tools/sniff_batc.py                 log until Ctrl+C to batc-<date>.jsonl in the logs folder
                                               (%LOCALAPPDATA%\\paul-batc-pill\\logs) and the console
    python tools/sniff_batc.py --seconds 90 --quiet-snapshot

Read-only: it sends no messages (only the protocol's pong replies to pings); BeyondATC pushes its
state on connect.
"""
import argparse
import json
import socket
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import inspect_ui  # noqa: E402  (reuses its minimal WebSocket client)
import pill_log  # noqa: E402  (the logs folder all tools share)

NOISY = ("DATIS", "Settings", "Actions", "InfoBoxes", "Progress", "FrameSync", "Pong", "Frequencies")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seconds", type=float, default=0, help="stop after N seconds (0 = until Ctrl+C)")
    ap.add_argument("--quiet-snapshot", action="store_true", help="hide noisy message types on the console")
    args = ap.parse_args()

    inspect_ui.HOST, inspect_ui.PORT = "127.0.0.1", 41716
    ws = inspect_ui.WS("/")
    ws.sock.settimeout(None)  # quiet stretches are normal; only --seconds sets a deadline
    logs = pill_log.log_dir()
    logs.mkdir(parents=True, exist_ok=True)
    out = logs / f"batc-{time.strftime('%Y%m%d-%H%M%S')}.jsonl"
    t0 = time.monotonic()
    print(f"sniff: logging to {out}")
    with out.open("w", encoding="utf-8") as f:
        try:
            while not args.seconds or time.monotonic() - t0 < args.seconds:
                if args.seconds:
                    ws.sock.settimeout(max(0.01, args.seconds - (time.monotonic() - t0)))
                try:
                    msg = ws.recv()
                except socket.timeout:
                    break
                except ConnectionError as e:
                    print(f"sniff: BeyondATC closed the socket ({e})")
                    break
                t = time.monotonic() - t0
                f.write(json.dumps({"t": round(t, 3), "msg": msg}, ensure_ascii=False) + "\n")
                f.flush()
                if not (args.quiet_snapshot and msg.startswith(NOISY)):
                    print(f"{t:7.2f} {msg[:200]}")
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
