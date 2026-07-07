"""Braille progress animation for the Flowka installer.

A horizontal bar built from Unicode Braille cells (U+2800..U+28FF). It fills
from *both ends* toward the centre. The two moving frontiers shimmer with
randomised single dots so the fill looks like it is being "decoded" in real
time, then settles into solid cells behind the wave.

The module is pure stdlib so it can run with the system Python, without the
project's dependencies installed.

Braille dot -> bit layout for ``chr(0x2800 + mask)``::

    dot1 (bit0)  dot4 (bit3)      row 0
    dot2 (bit1)  dot5 (bit4)      row 1
    dot3 (bit2)  dot6 (bit5)      row 2
    dot7 (bit6)  dot8 (bit7)      row 3
"""

from __future__ import annotations

import os
import random
import sys

BRAILLE_BASE = 0x2800
BLANK_CELL = chr(BRAILLE_BASE)
FULL_CELL = chr(BRAILLE_BASE + 0xFF)  # ⣿

ALL_BITS: tuple[int, ...] = (0, 1, 2, 3, 4, 5, 6, 7)
# Fill order for a settling cell: left column top->bottom, then right column.
FILL_ORDER: tuple[int, ...] = (0, 1, 2, 6, 3, 4, 5, 7)

# Classic braille spinner frames.
SPINNER = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"

_RESET = "\x1b[0m"
_BOLD = "\x1b[1m"
_DIM = "\x1b[2m"

# Theme colours matching the Flowka dashboard (teal/mint on ink).
_MINT = (45, 212, 191)
_EDGE = (186, 247, 243)
_TRACK = (39, 55, 70)
_STATIC = (56, 78, 96)
_GOLD = (250, 204, 21)


def _fg(rgb: tuple[int, int, int]) -> str:
    r, g, b = rgb
    return f"\x1b[38;2;{r};{g};{b}m"


def enable_ansi() -> None:
    """Prepare the terminal: UTF-8 output plus ANSI escapes on Windows."""
    # Braille glyphs need a UTF-8 capable stream; Windows consoles often
    # default to a legacy code page (e.g. cp1251) that cannot encode them.
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]
        except Exception:
            pass
    if os.name != "nt":
        return
    try:
        import ctypes

        kernel32 = ctypes.windll.kernel32  # type: ignore[attr-defined]
        # ENABLE_PROCESSED_OUTPUT | ENABLE_VIRTUAL_TERMINAL_PROCESSING
        kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
    except Exception:
        pass


def _cell(bits: list[int]) -> str:
    mask = 0
    for bit in bits:
        mask |= 1 << bit
    return chr(BRAILLE_BASE + mask)


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _bar(progress: float, width: int) -> str:
    """Render the two-ended braille bar for ``progress`` in [0, 1]."""
    progress = _clamp(progress, 0.0, 1.0)
    reach = progress * (width / 2)  # how many cells each side has advanced
    parts: list[str] = []

    for index in range(width):
        left_cov = _clamp(reach - index, 0.0, 1.0)
        right_cov = _clamp(reach - (width - 1 - index), 0.0, 1.0)
        coverage = max(left_cov, right_cov)

        if coverage >= 1.0:
            parts.append(_fg(_MINT) + FULL_CELL)
        elif coverage <= 0.0:
            # Idle track: mostly blank with the occasional flickering dot.
            if random.random() < 0.05:
                parts.append(_fg(_STATIC) + _cell([random.choice(ALL_BITS)]))
            else:
                parts.append(_fg(_TRACK) + BLANK_CELL)
        else:
            # Frontier: randomised shimmer of ~coverage*8 lit dots.
            lit = max(1, round(coverage * 8))
            bits = random.sample(ALL_BITS, min(lit, 8))
            parts.append(_fg(_EDGE) + _cell(bits))

    return "".join(parts) + _RESET


def frame(
    progress: float,
    label: str,
    spin: int,
    *,
    width: int = 28,
    done: bool = False,
) -> str:
    """Build a single status line (spinner + bar + percent + label)."""
    progress = _clamp(progress, 0.0, 1.0)
    pct = int(round(progress * 100))
    if done:
        head = _fg(_MINT) + "⣿"
    else:
        head = _fg(_GOLD) + SPINNER[spin % len(SPINNER)]
    bar = _bar(progress, width)
    pct_str = f"{_BOLD}{pct:3d}%{_RESET}"
    label_str = f"{_DIM}{label}{_RESET}" if not done else f"{_fg(_MINT)}{label}{_RESET}"
    return f" {head}{_RESET}  {bar}  {pct_str}  {label_str}"


def write_frame(line: str) -> None:
    """Overwrite the current terminal line with ``line``."""
    sys.stdout.write("\r\x1b[2K" + line)
    sys.stdout.flush()


def _demo() -> None:  # pragma: no cover - manual visual check
    import math
    import time

    enable_ansi()
    start = time.monotonic()
    spin = 0
    while True:
        elapsed = time.monotonic() - start
        progress = 1 - math.exp(-elapsed / 2.5)
        if progress > 0.995:
            break
        write_frame(frame(progress, "Decoding braille stream", spin))
        spin += 1
        time.sleep(1 / 24)
    write_frame(frame(1.0, "Complete", spin, done=True))
    sys.stdout.write("\n")


if __name__ == "__main__":
    _demo()
