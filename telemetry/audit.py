from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Dict


def audit_log(event_type: str, payload: Dict[str, object]) -> str:
    record = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "event_type": event_type,
        "payload": payload,
    }
    line = json.dumps(record, ensure_ascii=True)
    print(line)
    return line
