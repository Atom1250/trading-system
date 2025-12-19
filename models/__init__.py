"""Top-level shim package exposing backend/models for legacy imports.

This allows `import models` (e.g., `from models.portfolio import ...`)
to resolve to `backend/models` until proper packaging is in place.
"""
from __future__ import annotations

import os
from pathlib import Path
import pathlib

_backend_models_path = Path(__file__).resolve().parent.parent / "backend" / "models"
__path__.insert(0, os.path.abspath(str(_backend_models_path)))

_repo_root = pathlib.Path(__file__).resolve().parent.parent
_backend_models = (_repo_root / "backend" / "models").as_posix()
if _backend_models not in __path__:
    __path__.insert(0, _backend_models)
