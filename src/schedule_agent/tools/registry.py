import copy
import json

from jsonschema import Draft202012Validator

from ..domain.models import REVIEW_STATUSES, CONFIRMATION_STATUSES
from ..domain.guards import validate
from . import materials, rules, slots, confirm, drafts, report
from .common import error


def obj(properties, required=()):
    return {"type": "object", "properties": properties, "required": list(required), "additionalProperties": False}


def array(schema):
    return {"type": "array", "items": schema}


STRING = {"type": "string"}
STRINGS = array(STRING)
MID = {"type": "string", "minLength": 1}
SLOT = {"anyOf": [obj({"channel": MID, "start": MID}, ("channel", "start")), {"type": "null"}]}
SAVE_ITEM = obj({"material_id": MID, "review_status": {"enum": REVIEW_STATUSES},
                 "risk_reasons": STRINGS, "slot": SLOT,
                 "confirmation_status": {"enum": CONFIRMATION_STATUSES}, "confirmation_ids": STRINGS},
                ("material_id", "review_status", "risk_reasons", "slot", "confirmation_status", "confirmation_ids"))
REPORT_ITEM = obj({"material_id": MID, "review_status": {"enum": REVIEW_STATUSES},
                   "risk_reasons": STRINGS, "suggested_slot": {"type": ["string", "null"]},
                   "confirmation_status": {"enum": CONFIRMATION_STATUSES}, "pending_items": STRINGS},
                  ("material_id", "review_status", "risk_reasons", "suggested_slot", "confirmation_status", "pending_items"))


DEFINITIONS = {
    "list_pending_materials": (materials.list_pending_materials, "列出待处理素材", {"channel": STRING}, ()),
    "get_material": (materials.get_material, "读取素材，full 补查扩展信息", {"material_id": MID, "detail": {"enum": ["basic", "full"]}}, ("material_id",)),
    "check_rules": (rules.check_rules, "按当前已查信息审核；license 查授权库，content 查字幕", {"material_id": MID, "scope": {"enum": ["basic", "license", "content"]}, "publish_date": STRING}, ("material_id", "scope")),
    "query_slots": (slots.query_slots, "查询时段，held_by_this_request 视为可用", {"channel": MID, "date": MID, "from": MID, "to": MID}, ("channel", "date", "from", "to")),
    "request_confirmation": (confirm.request_confirmation, "登记确认问题，只有用户答复能确认", {"material_id": MID, "type": {"enum": ["time_change", "constraint_relax", "risk_ack", "info_needed"]}, "question": MID, "options": STRINGS, "proposed_slot": STRING}, ("material_id", "type", "question", "options")),
    "save_schedule_draft": (drafts.save_schedule_draft, "校验并保存全部素材的草稿；不得发布", {"items": array(SAVE_ITEM)}, ("items",)),
    "submit_report": (report.submit_report, "提交逐项报告结束运行，保存结果由代码组装", {"items": array(REPORT_ITEM), "overall_note": STRING}, ("items", "overall_note")),
}


class ToolRegistry:
    def __init__(self, faults=None):
        self.faults = faults or {}
        if any(k not in DEFINITIONS or v not in ("once", "always") for k, v in self.faults.items()):
            raise ValueError("故障必须为已知工具=once|always")
        self.counts = {}
        self.parameters = {}
        for name, (_, _, properties, required) in DEFINITIONS.items():
            self.parameters[name] = obj(dict(properties, reason={"type": "string", "minLength": 1, "maxLength": 30}), (*required, "reason"))

    def schemas(self):
        return [{"type": "function", "function": {"name": name, "description": definition[1],
                "parameters": self.parameters[name]}} for name, definition in DEFINITIONS.items()]

    def execute(self, name, args, ctx):
        try:
            if name not in DEFINITIONS:
                return error("INVALID_ARGUMENTS", "未知工具")
            if isinstance(args, str):
                args = json.loads(args)
            issues = list(Draft202012Validator(self.parameters[name]).iter_errors(args))
            if issues:
                return self._remember(name, error("INVALID_ARGUMENTS", "; ".join(i.message for i in issues)[:1000]), ctx)
            clean = {k: copy.deepcopy(v) for k, v in args.items() if k != "reason"}
            # Validation precedes fault injection on the save boundary.
            if name == "save_schedule_draft":
                violations = validate(ctx, clean["items"])
                if violations:
                    return self._remember(name, error("VALIDATION_FAILED", "草稿校验失败", violations=violations), ctx)
                ctx.attempt_items = ctx.canonical_items(clean["items"])
            self.counts[name] = self.counts.get(name, 0) + 1
            mode = self.faults.get(name)
            if mode == "always" or (mode == "once" and self.counts[name] == 1):
                code = "STORAGE_UNAVAILABLE" if name == "save_schedule_draft" else "TOOL_TIMEOUT"
                return self._remember(name, error(code, "注入的工具故障", True), ctx)
            obs = DEFINITIONS[name][0](ctx, **clean)
        except (ValueError, TypeError, KeyError) as exc:
            obs = error("INVALID_ARGUMENTS", f"参数或数据无效：{type(exc).__name__}")
        except OSError:
            obs = error("STORAGE_UNAVAILABLE", "本地存储不可用", True)
        except Exception as exc:
            obs = error("TOOL_ERROR", f"工具执行异常：{type(exc).__name__}")
        return self._remember(name, obs, ctx)

    def _remember(self, name, obs, ctx):
        if name == "save_schedule_draft":
            ctx.save_observation = copy.deepcopy(obs)
        return obs
