"""Top-level shim package exposing backend/services for legacy imports.

This file makes `import services.data.price_service` and similar imports
work by adding the repository's `backend/services` directory to the
package search path. It's a small compatibility shim until the project
is installed as a proper package (see TODO: Add proper packaging).
"""
import os
from pathlib import Path

# Insert backend/services at the front of the package search path so
# subpackages like `services.data` resolve to `backend/services/data`.
_backend_services_path = Path(__file__).resolve().parent.parent / "backend" / "services"
__path__.insert(0, os.path.abspath(str(_backend_services_path)))
