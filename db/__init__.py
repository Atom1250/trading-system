"""Top-level shim package exposing backend/db for legacy imports.

Adds `backend/db` to `db` package search path so imports like
`from db.database import ...` work before proper packaging is added.
"""

from __future__ import annotations

import os
import pathlib
from pathlib import Path

_backend_db_path = Path(__file__).resolve().parent.parent / "backend" / "db"
__path__.insert(0, os.path.abspath(str(_backend_db_path)))

_repo_root = pathlib.Path(__file__).resolve().parent.parent
_backend_db = (_repo_root / "backend" / "db").as_posix()
if _backend_db not in __path__:
    __path__.insert(0, _backend_db)
