import copy

from ..domain.guards import validate
from .common import ok, error


def save_schedule_draft(ctx, items):
    violations = validate(ctx, items)
    if violations:
        return error("VALIDATION_FAILED", "草稿校验失败", violations=violations)
    items = ctx.canonical_items(items)
    ids = {cid for item in items for cid in item.get("confirmation_ids", [])}
    result = ctx.store.save(ctx.key, items, ctx.pending(ids), ctx.run_id)
    ctx.saved_items = copy.deepcopy(items)
    return ok(result, f"草稿 {result['result']}（v{result['version']}，未发布）")
