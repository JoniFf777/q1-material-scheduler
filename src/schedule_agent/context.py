import copy
import uuid

from .domain.fingerprint import request_key


class RunContext:
    def __init__(self, request, repo, store, confirmations=None):
        self.request = copy.deepcopy(request)
        self.key = request_key(request)
        self.repo, self.store = repo, store
        self.confirmations = copy.deepcopy(confirmations or [])
        self.run_id = "run-" + uuid.uuid4().hex[:12]
        self.views = {}
        self.missing = set()
        self.checked = {}
        self.findings = {}
        self.check_dates = {}
        self.confirmation_records = {}
        self.queries = []
        self.save_observation = None
        self.saved_items = None
        self.tool_calls_used = 0

    @property
    def items(self):
        return self.request.get("items", [])

    def requirement(self, material_id):
        return next((i for i in self.items if i["material_id"] == material_id), None)

    def confirmation_matches(self, material_id, kind, slot=None):
        return [c for c in self.confirmation_records.values()
                if c["material_id"] == material_id and c["type"] == kind
                and (slot is None or c.get("proposed_slot") == slot)]

    def approved_by_user(self, material_id, kind, slot=None):
        return any(c["status"] == "confirmed" for c in self.confirmation_matches(material_id, kind, slot))

    def pending(self):
        return [{k: v for k, v in c.items() if k != "status"}
                for c in self.confirmation_records.values() if c["status"] == "pending"]
