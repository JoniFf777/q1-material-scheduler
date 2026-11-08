import hashlib
import json


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def digest(value):
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


def request_key(request):
    keys = ("material_id", "channel", "preferred_time", "time_policy", "constraints")
    items = [{k: item[k] for k in keys if k in item} for item in request.get("items", [])]
    return "RQ-" + digest({"items": sorted(items, key=lambda i: i["material_id"]),
                           "scope": request.get("scope")})[:12]
