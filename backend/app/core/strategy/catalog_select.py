def _catalog_by_id(catalog: list[dict]) -> dict[str, dict]:
    return {str(item.get("id") or "").strip(): item for item in catalog if item.get("id")}


def _selected_product_image_modules(module_ids: list[str], catalog: list[dict]) -> list[dict]:
    if not module_ids:
        raise ValueError("请至少选择一个生成图种")

    catalog_by_id = _catalog_by_id(catalog)
    selected: list[dict] = []
    seen: set[str] = set()
    unsupported: list[str] = []
    for module_id in module_ids:
        module_id = str(module_id or "").strip()
        if not module_id or module_id in seen:
            continue
        module = catalog_by_id.get(module_id)
        if not module:
            unsupported.append(module_id)
            continue
        selected.append({"id": module_id, **module})
        seen.add(module_id)

    if unsupported:
        raise ValueError(f"存在不支持的图种：{', '.join(unsupported)}")
    if not selected:
        raise ValueError("请至少选择一个生成图种")
    return selected


def _selected_product_suite_structures(structure: list[dict], catalog: list[dict]) -> list[dict]:
    if not structure:
        raise ValueError("请至少选择一个套图类型")

    catalog_by_id = _catalog_by_id(catalog)
    selected: list[dict] = []
    seen: set[str] = set()
    unsupported: list[str] = []
    for item in structure:
        if not isinstance(item, dict):
            continue
        structure_id = str(item.get("id") or "").strip()
        if not structure_id or structure_id in seen:
            continue
        config = catalog_by_id.get(structure_id)
        if not config:
            unsupported.append(structure_id)
            continue
        enabled = bool(item.get("enabled", True))
        if not enabled:
            seen.add(structure_id)
            continue
        default_count = int(config.get("default_count") or 1)
        max_count = int(config.get("max_count") or default_count)
        try:
            count = int(item.get("count", default_count))
        except (TypeError, ValueError):
            raise ValueError(f"{config['name']}数量无效")
        if count < 1 or count > max_count:
            raise ValueError(f"{config['name']}数量必须在 1-{max_count} 张之间")
        selected.append(
            {
                "id": structure_id,
                "name": config["name"],
                "desc": config["desc"],
                "strategy": config["strategy"],
                "count": count,
                "enabled": True,
            }
        )
        seen.add(structure_id)

    if unsupported:
        raise ValueError(f"存在不支持的套图类型：{', '.join(unsupported)}")
    if not selected:
        raise ValueError("请至少选择一个套图类型")
    return selected


def _selected_outfit_scenes(scene_ids: list[str], catalog: list[dict]) -> list[dict]:
    if not scene_ids:
        raise ValueError("请至少选择一个拍摄场景")

    catalog_by_id = _catalog_by_id(catalog)
    selected: list[dict] = []
    seen: set[str] = set()
    unsupported: list[str] = []
    for scene_id in scene_ids:
        scene_id = str(scene_id or "").strip()
        if not scene_id or scene_id in seen:
            continue
        scene = catalog_by_id.get(scene_id)
        if not scene:
            unsupported.append(scene_id)
            continue
        selected.append({"id": scene_id, **scene})
        seen.add(scene_id)

    if unsupported:
        raise ValueError(f"存在不支持的拍摄场景：{', '.join(unsupported)}")
    if not selected:
        raise ValueError("请至少选择一个拍摄场景")
    return selected
