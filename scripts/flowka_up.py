"""Flowka installer / launcher with an animated braille progress bar.

Wraps ``docker compose`` so bringing the whole stack up shows a smooth
two-ended braille fill animation while images build, dependencies download and
services start.

Usage::

    python scripts/flowka_up.py          # build + start the full stack
    python scripts/flowka_up.py --down   # stop and remove the stack

Only the standard library and the Docker CLI are required.
"""

from __future__ import annotations

import math
import shutil
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
from collections import deque
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from braille_loader import _RESET, enable_ansi, frame, write_frame  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
FPS = 20
CREEP_CEILING = 0.92  # indeterminate progress asymptote before completion
HEALTH_URL = "http://localhost:8000/api/health"

_MINT = "\x1b[38;2;45;212;191m"
_GOLD = "\x1b[38;2;250;204;21m"
_RED = "\x1b[38;2;248;113;113m"
_DIM = "\x1b[2m"
_BOLD = "\x1b[1m"


def _compose_cmd() -> list[str]:
    """Return the docker compose invocation available on this machine."""
    if shutil.which("docker") is None:
        raise SystemExit(
            f"{_RED}Docker CLI not found on PATH. Install Docker Desktop first.{_RESET}"
        )
    return ["docker", "compose"]


def _short(text: str, limit: int = 46) -> str:
    text = text.strip()
    return text if len(text) <= limit else text[: limit - 1] + "…"


def _finish(label: str, spin: int, start_progress: float) -> None:
    """Animate the bar from its current creep value up to a solid 100%."""
    steps = 10
    for step in range(1, steps + 1):
        progress = start_progress + (1.0 - start_progress) * (step / steps)
        write_frame(frame(progress, label, spin + step))
        time.sleep(0.018)
    write_frame(frame(1.0, label, spin + steps, done=True))
    sys.stdout.write("\n")
    sys.stdout.flush()


def run_step(cmd: list[str], label: str, *, tau: float = 9.0) -> None:
    """Run ``cmd``, animating an indeterminate braille bar until it exits."""
    proc = subprocess.Popen(
        cmd,
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    tail: deque[str] = deque(maxlen=12)
    status = {"line": ""}

    def drain() -> None:
        assert proc.stdout is not None
        for raw in proc.stdout:
            line = raw.rstrip()
            if line:
                tail.append(line)
                status["line"] = line

    reader = threading.Thread(target=drain, daemon=True)
    reader.start()

    start = time.monotonic()
    spin = 0
    progress = 0.0
    try:
        while proc.poll() is None:
            elapsed = time.monotonic() - start
            progress = CREEP_CEILING * (1 - math.exp(-elapsed / tau))
            detail = _short(status["line"]) if status["line"] else "working…"
            write_frame(frame(progress, f"{label}  {_DIM}{detail}{_RESET}", spin))
            spin += 1
            time.sleep(1 / FPS)
    except KeyboardInterrupt:
        proc.terminate()
        sys.stdout.write("\n")
        raise SystemExit(f"{_RED}Interrupted.{_RESET}")

    reader.join(timeout=1.0)
    if proc.returncode != 0:
        sys.stdout.write("\n")
        sys.stdout.write(f"{_RED}✗ {label} failed (exit {proc.returncode}){_RESET}\n")
        for line in tail:
            sys.stdout.write(f"  {_DIM}{line}{_RESET}\n")
        raise SystemExit(proc.returncode)

    _finish(label, spin, progress)


def wait_for_health(url: str, label: str, *, timeout: float = 120.0) -> None:
    """Poll ``url`` until it returns HTTP 200, animating meanwhile."""
    start = time.monotonic()
    spin = 0
    progress = 0.0

    def healthy() -> bool:
        try:
            with urllib.request.urlopen(url, timeout=2) as response:
                return 200 <= response.status < 300
        except (urllib.error.URLError, ConnectionError, OSError):
            return False

    last_check = 0.0
    ok = False
    while time.monotonic() - start < timeout:
        elapsed = time.monotonic() - start
        progress = CREEP_CEILING * (1 - math.exp(-elapsed / 12.0))
        write_frame(frame(progress, f"{label}  {_DIM}{url}{_RESET}", spin))
        spin += 1
        # Probe roughly once per second, keep animating at full FPS.
        if elapsed - last_check >= 1.0:
            last_check = elapsed
            if healthy():
                ok = True
                break
        time.sleep(1 / FPS)

    if not ok:
        sys.stdout.write("\n")
        raise SystemExit(f"{_RED}✗ {label} timed out after {int(timeout)}s{_RESET}")
    _finish(label, spin, progress)


def banner() -> None:
    sys.stdout.write(
        f"\n {_MINT}{_BOLD}⣿⣿  Flowka{_RESET}"
        f"  {_DIM}realtime Kafka observability — containerised installer{_RESET}\n\n"
    )
    sys.stdout.flush()


def up() -> None:
    compose = _compose_cmd()
    banner()
    run_step([*compose, "build"], "Building images & dependencies", tau=14.0)
    run_step([*compose, "up", "-d"], "Starting services", tau=6.0)
    wait_for_health(HEALTH_URL, "Waiting for API health")

    sys.stdout.write(
        f"\n {_MINT}{_BOLD}✓ Flowka is up{_RESET}\n"
        f"   {_DIM}Dashboard {_RESET} http://localhost:8080\n"
        f"   {_DIM}API docs  {_RESET} http://localhost:8000/docs\n"
        f"   {_DIM}Metrics   {_RESET} http://localhost:8000/api/metrics/history\n"
        f"   {_DIM}Console   {_RESET} docker compose --profile tools up console  "
        f"{_DIM}(http://localhost:8081){_RESET}\n\n"
        f" {_DIM}Stop with:{_RESET} python scripts/flowka_up.py --down\n\n"
    )
    sys.stdout.flush()


def down() -> None:
    compose = _compose_cmd()
    banner()
    run_step([*compose, "down", "--remove-orphans"], "Stopping services", tau=5.0)
    sys.stdout.write(f"\n {_MINT}✓ Stack stopped{_RESET}\n\n")
    sys.stdout.flush()


def main(argv: list[str]) -> None:
    enable_ansi()
    if any(arg in ("--down", "down", "stop") for arg in argv):
        down()
    else:
        up()


if __name__ == "__main__":
    main(sys.argv[1:])
