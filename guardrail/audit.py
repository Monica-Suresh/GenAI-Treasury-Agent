import hashlib
import json
from datetime import datetime


class AuditLogger:
    def __init__(self):
        self.entries = []
        self.prev_hash = "0" * 64

    def log(self, record: dict):
        entry = {**record, "timestamp": datetime.utcnow().isoformat(),
                 "prev_hash": self.prev_hash}
        entry_json = json.dumps(entry, sort_keys=True)
        entry["entry_hash"] = hashlib.sha256(entry_json.encode()).hexdigest()
        self.prev_hash = entry["entry_hash"]
        self.entries.append(entry)
        return entry

    def verify_chain(self) -> bool:
        prev = "0" * 64
        for entry in self.entries:
            copy = {k: v for k, v in entry.items() if k != "entry_hash"}
            expected = hashlib.sha256(json.dumps(copy, sort_keys=True).encode()).hexdigest()
            if entry["entry_hash"] != expected or entry["prev_hash"] != prev:
                return False
            prev = entry["entry_hash"]
        return True
