import copy
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from ..domain.fingerprint import digest


class DraftStore:
    """Single-process store; atomic replacement, deliberately no concurrency lock."""

    def __init__(self, state_dir):
        self.path = Path(state_dir) / "drafts.json"

    def read(self):
        if not self.path.exists():
            return {"schema_version": 1, "drafts": []}
        data = json.loads(self.path.read_text(encoding="utf-8"))
        if data.get("schema_version") != 1 or not isinstance(data.get("drafts"), list):
            raise ValueError("invalid draft store")
        keys = [d["idempotency_key"] for d in data["drafts"]]
        if len(keys) != len(set(keys)):
            raise ValueError("duplicate idempotency keys in store")
        return data

    def save(self, key, items, pending, run_id):
        data = self.read()
        items = sorted(copy.deepcopy(items), key=lambda i: i["material_id"])
        pending = sorted(copy.deepcopy(pending), key=lambda c: c["id"])
        # Presentation wording and model call order do not change business content.
        semantic_items = copy.deepcopy(items)
        for item in semantic_items:
            item["confirmation_ids"] = sorted(item.get("confirmation_ids", []))
            item["risk_reasons"] = sorted(item.get("risk_reasons", []))
        semantic_pending = [{k: v for k, v in c.items() if k not in ("question", "options")}
                            for c in pending]
        content_hash = "sha256:" + digest({"items": semantic_items, "pending_confirmations": semantic_pending})
        draft = next((d for d in data["drafts"] if d["idempotency_key"] == key), None)
        if draft and draft["content_hash"] == content_hash:
            return self._result(draft, "duplicate")
        now = datetime.now(timezone.utc).isoformat()
        result = "updated" if draft else "created"
        if draft is None:
            draft = {"draft_id": "D-" + key[3:], "idempotency_key": key,
                     "status": "draft", "version": 0, "created_at": now, "history": []}
            data["drafts"].append(draft)
        draft.update(version=draft["version"] + 1, content_hash=content_hash,
                     items=items, pending_confirmations=pending, updated_at=now)
        draft["history"].append({"version": draft["version"], "content_hash": content_hash,
                                 "run_id": run_id, "saved_at": now})
        self.path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(prefix="drafts.", suffix=".tmp", dir=self.path.parent)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as stream:
                json.dump(data, stream, ensure_ascii=False, indent=2)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(tmp, self.path)
        finally:
            if os.path.exists(tmp):
                os.unlink(tmp)
        return self._result(draft, result)

    def _result(self, draft, result):
        return {"draft_id": draft["draft_id"], "version": draft["version"],
                "result": result, "store_file": str(self.path)}

    def reset(self):
        # Only this store's file is removed; never recursively delete state-dir.
        self.path.unlink(missing_ok=True)
