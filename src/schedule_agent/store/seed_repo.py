import copy
import json
from pathlib import Path


class SeedRepo:
    def __init__(self, data_dir="data", patch=None):
        for name in ("materials", "rules", "schedule", "slot_config", "license_db", "terms"):
            setattr(self, name, json.loads((Path(data_dir) / f"{name}.json").read_text(encoding="utf-8-sig")))
        patch = patch or {}
        self.schedule = [s for s in self.schedule if not any(
            all(s.get(k) == v for k, v in remove.items()) for remove in patch.get("remove", []))]
        self.schedule.extend(copy.deepcopy(patch.get("add", [])))

    def material(self, material_id):
        return copy.deepcopy(self.materials.get(material_id))

    def occupancy(self, ctx, channel, start):
        own = None
        for s in self.schedule:
            if s["channel"] == channel and s["start"] == start:
                return "occupied", {"material_id": s["material_id"], "source": "schedule"}
        for draft in ctx.store.read()["drafts"]:
            for item in draft["items"]:
                if item.get("slot") == {"channel": channel, "start": start}:
                    source = {"material_id": item["material_id"], "source": "draft", "draft_id": draft["draft_id"]}
                    if draft["idempotency_key"] != ctx.key:
                        return "occupied", source
                    own = source
        return ("held_by_this_request", own) if own else ("available", None)
