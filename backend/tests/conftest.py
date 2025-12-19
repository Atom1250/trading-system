"""Pytest conftest to ensure repository root is on sys.path for imports.

Some tests run with the test directory as sys.path[0], which can prevent
top-level shim packages from being importable. Add the project root to
sys.path at collection time so `import services` resolves correctly.
"""
import os
import sys

_repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _repo_root not in sys.path:
    sys.path.insert(0, _repo_root)
