"""Render the README and flightsim.to images from docs/render/*.html with headless Edge (or Chrome/Chromium).
Needs Pillow.

    python docs/render_images.py

Writes docs/images/states.png, settings.png, comms.png, panel.png and splash.png. If .local/shots/splash-bg.png exists
(a 16:9 sim screenshot), the splash uses it as its backdrop.
"""
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
RENDER = ROOT / "docs" / "render"
OUT = ROOT / "docs" / "images"
EDGE = [
    Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"),
    Path(r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"),
]


def edge():
    for p in EDGE:
        if p.exists():
            return str(p)
    for name in ("msedge", "chrome", "google-chrome", "chromium", "chromium-browser"):
        found = shutil.which(name)
        if found:
            return found
    sys.exit("render: no Edge, Chrome or Chromium found")


def shoot(page, size, scale, query=""):
    """Screenshot page at size (CSS px) and device scale; returns a PIL image.

    The window is made taller than needed, then cropped: headless Chromium keeps part of the window
    height for itself, so a window of exactly `size` cuts the bottom off."""
    with tempfile.TemporaryDirectory() as tmp:
        png = Path(tmp) / "shot.png"
        url = (RENDER / page).as_uri() + query
        subprocess.run([
            edge(), "--headless=new", "--disable-gpu", "--hide-scrollbars", "--allow-file-access-from-files",
            *(["--no-sandbox"] if sys.platform != "win32" else []),  # containers run as root
            f"--user-data-dir={Path(tmp) / 'profile'}",  # fresh profile: no saved pill settings
            f"--window-size={size[0]},{size[1] + 200}", f"--force-device-scale-factor={scale}",
            "--virtual-time-budget=4000", f"--screenshot={png}", url,
        ], check=True, capture_output=True)
        return Image.open(png).crop((0, 0, size[0] * scale, size[1] * scale))


def main():
    OUT.mkdir(parents=True, exist_ok=True)

    img = shoot("states.html", (1200, 910), 2)  # 6 rows of 150 px tiles
    img.save(OUT / "states.png", optimize=True)
    print(f"render: states.png {img.size}")

    # pill + open card in the top-right corner of a 1080p screen
    img = shoot("settings.html", (1920, 1080), 2).crop((1600 * 2, 50 * 2, 1920 * 2, 640 * 2))
    img.save(OUT / "settings.png", optimize=True)
    print(f"render: settings.png {img.size}")

    # the comms around the pill: ATC's message with its answers (hovered), and the Frequencies panel
    img = shoot("comms.html", (1920, 1080), 2).crop((1300 * 2, 50 * 2, 1920 * 2, 330 * 2))
    img.save(OUT / "comms.png", optimize=True)
    print(f"render: comms.png {img.size}")
    img = shoot("comms.html", (1920, 1080), 2, "?panel").crop((1540 * 2, 50 * 2, 1920 * 2, 470 * 2))
    img.save(OUT / "panel.png", optimize=True)
    print(f"render: panel.png {img.size}")

    bg = ROOT / ".local" / "shots" / "splash-bg.png"
    query = "?bg=" + bg.as_uri() if bg.exists() else ""
    img = shoot("splash.html", (1920, 1080), 1, query)
    img.save(OUT / "splash.png", optimize=True)
    print(f"render: splash.png {img.size}{' (sim backdrop)' if query else ''}")


if __name__ == "__main__":
    main()
