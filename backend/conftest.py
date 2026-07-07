"""Pytest bootstrap.

In normal environments (CI, Docker, a populated virtualenv) the project
dependencies are installed via ``pip install -e ".[dev]"`` and this file is a
no-op. For constrained/offline machines the dependencies may instead be
vendored into ``backend/.deps`` (gitignored). When that directory exists and a
core dependency is not otherwise importable, we append it to ``sys.path`` as a
*lowest priority* fallback so the documented ``python -m pytest`` command works
without callers having to set ``PYTHONPATH`` by hand.

Appending (not prepending) guarantees real installed packages always win, so
this never shadows a proper installation.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

_VENDORED_DEPS = Path(__file__).parent / ".deps"


def _bootstrap_vendored_deps() -> None:
    if not _VENDORED_DEPS.is_dir():
        return
    # Only fall back to the vendored tree if a core dependency is missing.
    if importlib.util.find_spec("fastapi") is not None:
        return
    vendored = str(_VENDORED_DEPS.resolve())
    if vendored not in sys.path:
        sys.path.append(vendored)


_bootstrap_vendored_deps()
