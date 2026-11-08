from .common import ok, error
from ..domain.guards import validate


def submit_report(ctx, items, overall_note):
    ids = [i["material_id"] for i in items]
    if not ctx.items or set(ids) != {i["material_id"] for i in ctx.items} or len(ids) != len(set(ids)):
        return error("VALIDATION_FAILED", "报告必须且只能覆盖请求全部素材")
    if ctx.saved_items and ctx.save_observation and ctx.save_observation["ok"]:
        violations = validate(ctx, ctx.saved_items)
        if violations:
            return error("VALIDATION_FAILED", "保存后事实发生变化，请更新草稿再结束", violations=violations)
    return ok({"accepted": True}, "报告已接收；保存状态以工具记录为准")
