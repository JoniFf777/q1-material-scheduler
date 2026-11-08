from datetime import date as Date, time as Time

from .common import ok, error


def query_slots(ctx, channel, date, **window):
    config = ctx.repo.slot_config
    parsed_date = Date.fromisoformat(date)
    start, end = window["from"], window["to"]
    if parsed_date.isoformat() != date or any(Time.fromisoformat(t).strftime("%H:%M") != t for t in (start, end)):
        return error("INVALID_ARGUMENTS", "日期或时间格式无效")
    if channel not in config["channels"] or start > end:
        return error("INVALID_ARGUMENTS", "渠道或查询窗口无效")
    slots = []
    for hour in range(config["start_hour"], config["end_hour"] + 1):
        value = f"{hour:02d}:00"
        if start <= value <= end:
            status, source = ctx.repo.occupancy(ctx, channel, date + "T" + value)
            item = {"start": value, "status": status}
            if source:
                item["occupied_by"] = source
            slots.append(item)
    result = dict(channel=channel, date=date, slots=slots)
    ctx.queries.append(result)
    return ok(result, "；".join(f"{s['start']} {s['status']}" +
              (f"({s['occupied_by']['material_id']})" if "occupied_by" in s else "") for s in slots))
