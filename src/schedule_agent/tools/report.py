from .common import ok, error


def submit_report(ctx, items, overall_note):
    ids = [i["material_id"] for i in items]
    if not ctx.items or set(ids) != {i["material_id"] for i in ctx.items} or len(ids) != len(set(ids)):
        return error("VALIDATION_FAILED", "报告必须且只能覆盖请求全部素材")
    return ok({"accepted": True}, "报告已接收；保存状态以工具记录为准")
