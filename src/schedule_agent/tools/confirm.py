from ..domain.fingerprint import digest
from .common import ok, error


def request_confirmation(ctx, material_id, type, question, options, proposed_slot=None):
    if not ctx.requirement(material_id):
        return error("INVALID_ARGUMENTS", "素材不在本请求中")
    identity = {"material_id": material_id, "type": type, "proposed_slot": proposed_slot}
    cid = "C-" + digest(identity)[:10]
    record = dict(identity, id=cid, question=question, options=options, status="pending")
    for reply in ctx.confirmations:
        if (reply.get("material_id") == material_id and reply.get("type") == type
                and (proposed_slot is None or reply.get("proposed_slot") == proposed_slot)
                and reply.get("status") in ("confirmed", "rejected")):
            record.update(status=reply["status"], user_reply=reply.get("user_reply", ""))
            break
    ctx.confirmation_records[cid] = record
    return ok({"confirmation_id": cid, "status": record["status"],
               **({"user_reply": record["user_reply"]} if "user_reply" in record else {})},
              f"{material_id} {type}：{record['status']}")
