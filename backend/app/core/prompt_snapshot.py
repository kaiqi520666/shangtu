from typing import Any

from app.core.json_utils import dump_json, parse_json_object


def build_prompt_snapshot(
    *,
    system: str | None = None,
    task: str | None = None,
    user: str | None = None,
    final: str | None = None,
    template_refs: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    return {
        "system": system or "",
        "task": task or "",
        "user": user or "",
        "final": final or "",
        "template_refs": template_refs or [],
    }


def dump_prompt_snapshot(snapshot: dict[str, Any] | None) -> str | None:
    if not snapshot:
        return None
    return dump_json(snapshot)


def parse_prompt_snapshot(raw: str | None) -> dict[str, Any]:
    snapshot = parse_json_object(raw)
    return build_prompt_snapshot(
        system=snapshot.get("system") if isinstance(snapshot.get("system"), str) else "",
        task=snapshot.get("task") if isinstance(snapshot.get("task"), str) else "",
        user=snapshot.get("user") if isinstance(snapshot.get("user"), str) else "",
        final=snapshot.get("final") if isinstance(snapshot.get("final"), str) else "",
        template_refs=snapshot.get("template_refs")
        if isinstance(snapshot.get("template_refs"), list)
        else [],
    )
