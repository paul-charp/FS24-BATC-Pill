"""Evaluate JS in a live sim UI view via the Coherent inspector (Devmode, localhost:19999). Stdlib only.

    python tools/inspect_ui.py "document.title"
    python tools/inspect_ui.py --page 2 --reload        reload the view (picks up edited CSS/JS)
    python tools/inspect_ui.py --list
    python tools/inspect_ui.py --push                   hot-reload pill.css + pill.js into the live view
"""
import argparse
import base64
import json
import os
import socket
import struct
import sys
import urllib.error
import urllib.request

HOST, PORT = "localhost", 19999


def pages():
    with urllib.request.urlopen(f"http://{HOST}:{PORT}/pagelist.json", timeout=3) as r:
        return json.load(r)


class WS:
    def __init__(self, path):
        self.sock = socket.create_connection((HOST, PORT), timeout=5)
        key = base64.b64encode(os.urandom(16)).decode()
        self.sock.sendall((f"GET {path} HTTP/1.1\r\nHost: {HOST}:{PORT}\r\nUpgrade: websocket\r\n"
                           f"Connection: Upgrade\r\nSec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n\r\n").encode())
        head = b""
        while b"\r\n\r\n" not in head:
            chunk = self.sock.recv(4096)
            if not chunk:
                break
            head += chunk
        if b" 101 " not in head.split(b"\r\n", 1)[0]:
            raise ConnectionError(head.split(b"\r\n", 1)[0].decode(errors="replace"))
        self.buf = head.split(b"\r\n\r\n", 1)[1]
        self.sock.settimeout(30)  # a big --push evaluation can take a while to answer

    def send(self, text, opcode=0x1):
        data = text.encode() if isinstance(text, str) else text
        mask = os.urandom(4)
        n = len(data)
        hdr = struct.pack("!B", 0x80 | opcode) + (struct.pack("!B", 0x80 | n) if n < 126 else
                                          struct.pack("!BH", 0x80 | 126, n) if n < 65536 else
                                          struct.pack("!BQ", 0x80 | 127, n))
        self.sock.sendall(hdr + mask + bytes(b ^ mask[i % 4] for i, b in enumerate(data)))

    def _read(self, n):
        while len(self.buf) < n:
            chunk = self.sock.recv(65536)
            if not chunk:
                raise ConnectionError("socket closed")
            self.buf += chunk
        out, self.buf = self.buf[:n], self.buf[n:]
        return out

    def recv(self):
        msg = b""
        while True:
            b0, b1 = self._read(2)
            n = b1 & 0x7F
            if n == 126:
                n = struct.unpack("!H", self._read(2))[0]
            elif n == 127:
                n = struct.unpack("!Q", self._read(8))[0]
            payload = self._read(n)
            opcode = b0 & 0x0F
            if opcode == 0x9:  # ping: answer it, or the server drops the connection
                self.send(payload, 0xA)
                continue
            if opcode == 0xA:  # pong
                continue
            if opcode == 0x8:
                raise ConnectionError("closed by server")
            msg += payload
            if b0 & 0x80:
                return msg.decode(errors="replace")


def call(ws, msg_id, method, params=None):
    ws.send(json.dumps({"id": msg_id, "method": method, "params": params or {}}))
    while True:
        reply = json.loads(ws.recv())
        if reply.get("id") == msg_id:
            return reply


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("expr", nargs="?")
    ap.add_argument("--page", type=int, default=2, help="pagelist id (2 = mainUi)")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--reload", action="store_true")
    ap.add_argument("--push", action="store_true", help="hot-reload src/ pill.css + pill.js into the live view")
    ap.add_argument("--file", help="evaluate a JS file instead of an inline expression")
    ap.add_argument("--path", default="/devtools/page/{page}", help="websocket path template")
    args = ap.parse_args()

    if args.list:
        for p in pages():
            print(p["id"], p["title"], p["url"])
        return
    ws = WS(args.path.format(page=args.page))
    if args.reload:
        print(json.dumps(call(ws, 1, "Page.reload", {"ignoreCache": True}), indent=2))
    if args.file:
        args.expr = open(args.file, encoding="utf-8").read()
    if args.push:
        # Tear down the running pill, then evaluate the current src/ files. Works without a sim
        # restart, even for edits the VFS hasn't picked up yet.
        src = os.path.join(os.path.dirname(__file__), "..", "src", "html_ui", "paul-batc-pill")
        css = open(os.path.join(src, "pill.css"), encoding="utf-8").read()
        js = open(os.path.join(src, "pill.js"), encoding="utf-8").read()
        js = js.replace("    devLog: false,", "    devLog: true,", 1)  # a dev build: streams to tools/pill_log.py
        args.expr = ("(function (css, js) {"
                     " if (window.batcPill) window.batcPill.destroy();"
                     " window.batcPillInlineCss = css; (0, eval)(js);"
                     " return !!document.getElementById('batc-pill'); })(" + json.dumps(css) + ", " + json.dumps(js) + ")")
    if args.expr:
        r = call(ws, 2, "Runtime.evaluate", {"expression": args.expr, "returnByValue": True})
        res = r.get("result", {})
        if "result" in res:
            print(json.dumps(res["result"].get("value", res["result"]), indent=2, ensure_ascii=False))
        else:
            print(json.dumps(r, indent=2))
            sys.exit(1)


if __name__ == "__main__":
    try:
        try:
            main()
        except urllib.error.URLError as e:  # urlopen wraps socket errors
            raise e.reason if isinstance(e.reason, (ConnectionRefusedError, TimeoutError, socket.timeout)) else e
    except ConnectionRefusedError:
        sys.exit(f"inspect_ui: nothing listens on {HOST}:{PORT}. Is the sim running, with Developer Mode on?")
    except (TimeoutError, socket.timeout, urllib.error.URLError) as e:
        sys.exit(f"inspect_ui: the sim's UI debugger ({HOST}:{PORT}) isn't answering ({e}).\n"
                 "A sim that froze or quit can leave the port held by a program it started (seen: SimAppPro2.exe).\n"
                 "Check: netstat -ano | findstr 19999  (more than one LISTENING PID: end the one that isn't the sim,\n"
                 "or the child of a dead one: Get-CimInstance Win32_Process -Filter \"ParentProcessId=<pid>\")")
