import hashlib
import json
from typing import Any


def hash_plan(plan: dict[str, Any]) -> str:
    serialized_plan = json.dumps(plan, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(serialized_plan.encode("utf-8")).hexdigest()
