from .common import ok, error


def list_pending_materials(ctx, channel=None):
    materials = [{"material_id": mid, "title": m["title"], "status": "pending_review"}
                 for mid, m in ctx.repo.materials.items()
                 if not channel or channel in m.get("channels", [])]
    if ctx.request.get("scope") == "pending":
        defaults = ctx.request.get("defaults", {})
        if not all(k in defaults for k in ("channel", "preferred_time")):
            return error("INVALID_ARGUMENTS", "scope=pending 需要 defaults.channel 和 defaults.preferred_time")
        ctx.request["items"] = [dict(defaults, material_id=m["material_id"],
                                     time_policy=defaults.get("time_policy", "flexible")) for m in materials]
    return ok({"materials": materials}, f"找到 {len(materials)} 个待审核素材")


def get_material(ctx, material_id, detail="basic"):
    material = ctx.repo.material(material_id)
    if material is None:
        ctx.missing.add(material_id)
        return error("NOT_FOUND", f"素材 {material_id} 不存在")
    extended = material.pop("extended", {})
    if detail == "full":
        for k, v in extended.items():
            if k == "copyright_owner":
                if material["copyright"].get("owner") is None:
                    material["copyright"]["owner"] = v
            elif material.get(k) is None:
                material[k] = v
        material["extended"] = extended
    # A subsequent basic read must not discard already discovered full fields.
    if detail == "full" or material_id not in ctx.views:
        ctx.views[material_id] = material
    return ok(ctx.views[material_id], f"读取 {material_id}（{detail}）")
