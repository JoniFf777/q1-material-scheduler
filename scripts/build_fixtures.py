"""Build explicit offline fixtures. No observations or API results are consulted.

These scripts describe expected demo paths; they are NOT an autonomous scheduler.
Run from the repository root only when intentionally regenerating demo fixtures.
"""
import copy
import json
from pathlib import Path

from schedule_agent.domain.fingerprint import digest


ROOT = Path(__file__).resolve().parents[1]


def write(path, data):
    target = ROOT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def requirement(mid, hour, day="10", channel="douyin", policy="flexible"):
    return {"material_id": mid, "channel": channel, "preferred_time": f"2026-11-{day}T{hour}:00",
            "time_policy": policy, "constraints": {"date_fixed": True, "channel_fixed": True, "not_after": "21:00"}}


def action(name, **args):
    return {"name": name, "arguments": {"reason": "离线脚本验证此步骤", **args}}


def round_(*calls):
    return {"calls": list(calls)}


def item(req, start=None, review="approved", status="not_required", ids=None):
    return {"material_id": req["material_id"], "review_status": review, "risk_reasons": [],
            "slot": {"channel": req["channel"], "start": start} if start else None,
            "confirmation_status": status, "confirmation_ids": ids or []}


def ask(mid, kind, question, proposed=None):
    identity = {"material_id": mid, "type": kind, "proposed_slot": proposed}
    cid = "C-" + digest(identity)[:10]
    args = {"material_id": mid, "type": kind, "question": question, "options": ["同意", "补充信息或拒绝"]}
    if proposed:
        args["proposed_slot"] = proposed
    return action("request_confirmation", **args), cid


def report(items, note="仅生成草稿，未发布"):
    return action("submit_report", items=[{
        "material_id": i["material_id"], "review_status": i["review_status"], "risk_reasons": i["risk_reasons"],
        "suggested_slot": i["slot"]["start"] if i["slot"] else None,
        "confirmation_status": i["confirmation_status"], "pending_items": []} for i in items], overall_note=note)


def read_rounds(reqs):
    return [round_(*(action("get_material", material_id=r["material_id"]) for r in reqs)),
            round_(*(action("check_rules", material_id=r["material_id"], scope="basic") for r in reqs))]


def query(req):
    return action("query_slots", channel=req["channel"], date=req["preferred_time"][:10],
                  **{"from": "08:00", "to": "21:00"})


def finish(script, items, save_count=1, note="仅生成草稿，未发布"):
    return script + [round_(action("save_schedule_draft", items=items)) for _ in range(save_count)] + [round_(report(items, note))]


def scenario(name, reqs, expect, script, setup=None, confirmations=None):
    write(f"examples/inputs/{name}.json", {"name": name, "description": name,
          "setup": setup or {}, "request": {"items": reqs}, "confirmations": confirmations or [], "expect": expect})
    write(f"tests/fixtures/mock_scripts/{name}.json", script)


def build():
    r2 = requirement("M02", "20")
    normal = item(r2, r2["preferred_time"])
    normal_script = finish(read_rounds([r2]) + [round_(query(r2))], [normal])
    scenario("S01_normal", [r2], {"M02": {"review_status": "approved", "slot_status": "as_requested", "confirmation_status": "not_required"}, "draft_result": "created", "status": "completed"}, normal_script)

    r1 = requirement("M01", "18")
    confirmation, cid = ask("M01", "time_change", "18:00 被 M90 占用，是否改到 19:00？", "2026-11-10T19:00")
    alt = item(r1, "2026-11-10T19:00", status="pending", ids=[cid])
    conflict_script = finish(read_rounds([r1]) + [round_(query(r1)), round_(confirmation)], [alt])
    conflict_expect = {"M01": {"suggested_slot": "2026-11-10T19:00", "slot_status": "alternative", "confirmation_status": "pending"}, "draft_result": "created", "status": "completed_with_pending", "draft_count": 1}
    scenario("S04_slot_conflict", [r1], conflict_expect, conflict_script)
    duplicate_expect = dict(copy.deepcopy(conflict_expect), draft_result="duplicate")
    scenario("S06_duplicate", [r1], duplicate_expect, conflict_script)
    changed = item(r1, r1["preferred_time"])
    scenario("S06b_slot_changed", [r1], {"M01": {"suggested_slot": r1["preferred_time"], "slot_status": "as_requested", "confirmation_status": "not_required"}, "draft_result": "updated", "version": 2, "draft_count": 1},
             finish(read_rounds([r1]) + [round_(query(r1))], [changed]),
             {"schedule_patch": {"remove": [{"material_id": "M90"}], "add": [{"material_id": "M90", "channel": "douyin", "start": "2026-11-10T19:00"}]}})

    r6 = requirement("M06", "20", day="11", policy="fixed")
    confirmation, cid = ask("M06", "constraint_relax", "20:00 被 M91 占用，请决定是否提出新的时间要求。")
    fixed = item(r6, status="pending", ids=[cid])
    scenario("S05_hard_conflict", [r6], {"M06": {"review_status": "approved", "suggested_slot": None, "confirmation_status": "pending"}, "draft_result": "created", "status": "completed_with_pending"},
             finish(read_rounds([r6]) + [round_(query(r6)), round_(confirmation)], [fixed]))

    r3, r8 = requirement("M03", "15"), requirement("M08", "16")
    a3, c3 = ask("M03", "info_needed", "请补充版权方和授权状态。")
    a8, c8 = ask("M08", "info_needed", "素材 M08 不存在，请提供正确的素材 ID。")
    missing = [item(r3, review="need_info", status="pending", ids=[c3]), item(r8, review="need_info", status="pending", ids=[c8])]
    script = [round_(action("get_material", material_id="M03"), action("get_material", material_id="M08")),
              round_(action("check_rules", material_id="M03", scope="basic")),
              round_(action("get_material", material_id="M03", detail="full")),
              round_(action("check_rules", material_id="M03", scope="basic")), round_(a3, a8)]
    scenario("S02_missing_info", [r3, r8], {"M03": {"review_status": "need_info", "suggested_slot": None}, "M08": {"review_status": "need_info", "suggested_slot": None}, "draft_result": "created", "status": "completed_with_pending"}, finish(script, missing))

    r4, r5, r7 = requirement("M04", "19"), requirement("M05", "12", channel="xiaohongshu"), requirement("M07", "21")
    risk, cid = ask("M05", "risk_ack", "标题含极限用语‘第一’，请确认风险或修改素材。")
    risks = [item(r4, review="blocked"), item(r5, r5["preferred_time"], review="needs_confirmation", status="pending", ids=[cid]), item(r7, r7["preferred_time"])]
    script = read_rounds([r4, r5, r7]) + [round_(action("check_rules", material_id="M04", scope="license"), action("check_rules", material_id="M07", scope="license")), round_(query(r5), query(r7)), round_(risk)]
    scenario("S03_rule_risk", [r4, r5, r7], {"M04": {"review_status": "blocked", "suggested_slot": None, "confirmation_status": "not_required"}, "M05": {"review_status": "needs_confirmation", "confirmation_status": "pending", "suggested_slot": r5["preferred_time"], "slot_status": "as_requested"}, "M07": {"review_status": "approved", "suggested_slot": r7["preferred_time"], "confirmation_status": "not_required", "slot_status": "as_requested"}, "draft_result": "created"}, finish(script, risks))

    scenario("S07_save_failure", [r2], {"draft_result": "failed", "status": "save_failed", "draft_count": 0, "error_code": "STORAGE_UNAVAILABLE"},
             finish(read_rounds([r2]) + [round_(query(r2))], [normal], save_count=2, note="保存失败，请检查存储。"), {"faults": {"save_schedule_draft": "always"}})
    scenario("S08_tool_retry", [r2], {"draft_result": "created", "status": "completed", "trace_errors": ["TOOL_TIMEOUT"]},
             finish(read_rounds([r2]) + [round_(query(r2)), round_(query(r2))], [normal]), {"faults": {"query_slots": "once"}})
    reqs = [r1, r2, r4, r7]
    script = [round_(action("get_material", material_id=r["material_id"])) for r in reqs]
    scenario("S09_step_limit", reqs, {"status": "incomplete", "incomplete_reason": "MAX_STEPS_REACHED", "draft_result": "not_saved"}, script, {"limits": {"max_steps": 4}})
    confirmed = copy.deepcopy(alt)
    confirmed["confirmation_status"] = "confirmed"
    scenario("S10_confirm_round2", [r1], {"M01": {"suggested_slot": "2026-11-10T19:00", "confirmation_status": "confirmed"}, "draft_result": "updated", "version": 2, "draft_count": 1, "status": "completed"},
             finish(read_rounds([r1]) + [round_(query(r1)), round_(ask("M01", "time_change", "18:00 被 M90 占用，是否改到 19:00？", "2026-11-10T19:00")[0])], [confirmed]),
             confirmations=[{"material_id": "M01", "type": "time_change", "proposed_slot": "2026-11-10T19:00", "status": "confirmed", "user_reply": "同意改到19点"}])


if __name__ == "__main__":
    build()
