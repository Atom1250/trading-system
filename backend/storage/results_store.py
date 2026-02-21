import json
import os
from datetime import datetime
from typing import Any, Dict, List


class ResultsStore:
    def __init__(self, storage_dir: str = "backend/storage"):
        self.storage_dir = storage_dir
        self.results_file = os.path.join(storage_dir, "backtest_results.json")
        self._ensure_storage()

    def _ensure_storage(self):
        if not os.path.exists(self.storage_dir):
            os.makedirs(self.storage_dir)
        if not os.path.exists(self.results_file):
            with open(self.results_file, "w") as f:
                json.dump([], f)

    def save_result(self, result: Dict[str, Any]):
        results = self.get_all_results()
        # Add timestamp/id if missing
        if "id" not in result:
            # simple ID generation
            import uuid

            result["id"] = str(uuid.uuid4())

        if "timestamp" not in result:
            result["timestamp"] = datetime.utcnow().isoformat()

        results.append(result)
        with open(self.results_file, "w") as f:
            json.dump(results, f, default=str)
        return result["id"]

    def get_all_results(self) -> List[Dict[str, Any]]:
        try:
            with open(self.results_file, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return []

    def get_result(self, result_id: str) -> Dict[str, Any] | None:
        results = self.get_all_results()
        for r in results:
            if r.get("id") == result_id:
                return r
        return None
