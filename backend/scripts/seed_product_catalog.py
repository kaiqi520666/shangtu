from __future__ import annotations

import asyncio
import sys
from pathlib import Path

from sqlalchemy import select

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.core.database import Base, SessionLocal, engine  # noqa: E402
from app.core.time import utc_now  # noqa: E402
from app.models import ProductCatalog  # noqa: E402
import app.models  # noqa: E402,F401


PRODUCT_IMAGE_MODULES = [
    ("first-screen", "首屏主视觉", "极简大图与大字报，第一眼传递核心卖点价值。", "大标题聚焦，高饱和度背板突显商品核心形态。"),
    ("core-selling", "核心卖点图", "突出商品三大硬核优势，多点对照打消疑虑。", "三栏目清单排版，配图层级鲜明。"),
    ("use-scenario", "使用场景图", "呈现真实使用状态或家居融入。", "融合淡雅环境投影，拉近用户心理距离。"),
    ("multi-angle", "多角度呈现图", "展示侧面、背面及折叠等完整外观。", "三视图对齐，透视比例精准缩放。"),
    ("ambient-scene", "场景氛围图", "强光影写实渲染，增强商品的高级质感。", "暖色调逆光底板，配合微小阴影质感。"),
    ("detail-zoom", "商品细节图", "局部放大，精细展现材质和精湛工艺。", "中心放大镜切割圆圈，拉线批注。"),
    ("brand-story", "品牌故事图", "传达品牌匠心，突显高档商品格调。", "英文点缀，加宽留白，典雅无衬线排版。"),
    ("specs-info", "尺寸/规格/容量图", "直观标注物理尺寸与对比参照物。", "添加标注线与比例尺，数值一目了然。"),
    ("contrast-effect", "效果对比图", "使用前/后、升级前/后的直观效果。", "双栏垂直切割，BEFORE / AFTER 徽章强对抗。"),
    ("tech-specs", "详细规格/参数表", "将复杂工业数据整合为超清美化表格。", "圆角半透明卡片表格，结构化突出核心。"),
    ("manufacturing", "工艺制作图", "展示精密做工、材质层级拆解。", "爆炸视图效果，精细拆解元器件架构。"),
    ("freebies", "配件/赠品图", "明确告知用户收货拆箱的丰富组合。", "买即送角贴，配全套礼盒全家福。"),
    ("series-show", "系列展示图", "多配色、多SKU合辑呈现，极大提升加购。", "多色环绕渐变，卡片式并列。"),
    ("ingredients", "商品成分图", "透明呈现成分比例或纯净配料表。", "分子网格配图，科学健康风骨。"),
    ("warranty", "售后保障图", "官方质保、包邮无忧、金牌认证退换。", "醒目信任徽章，构建消费安全感。"),
    ("usage-tips", "使用建议图", "温馨提示使用建议、充电与养护说明。", "简洁图标列表，避免售后客诉纠纷。"),
]


PRODUCT_SUITE_STRUCTURES = [
    (
        "white-bg",
        "白底图",
        "适配平台首图规范，突出商品主体与干净轮廓。",
        "纯净浅色或白色背景，商品主体居中完整展示，轮廓清晰，光影自然。",
        1,
        6,
    ),
    (
        "scene",
        "场景图",
        "把商品放进真实使用环境，强化购买代入感。",
        "围绕商品用途构建可信场景，保持商品主体准确，背景服务商品而不喧宾夺主。",
        1,
        6,
    ),
    (
        "selling-point",
        "卖点图",
        "提炼核心优势，用高可读信息块表达产品价值。",
        "用清晰标题、短句卖点和适量视觉标注表达核心优势，避免信息过密。",
        1,
        6,
    ),
    (
        "detail",
        "细节图",
        "展示材质、结构、功能细节，降低用户决策疑虑。",
        "使用局部特写、放大框或简洁标注展示材质、结构、功能或工艺细节。",
        1,
        6,
    ),
]


OUTFIT_SCENES = [
    ("studio", "纯色棚拍", "纯色或浅灰棚拍背景，画面干净专业，突出服装整体版型、长度、肩线和垂坠感。", "柔和商业摄影布光，模特自然站立或轻微转身，背景克制，服装轮廓完整清晰。"),
    ("street", "都市街头", "都市街头场景，突出服装的日常穿搭感和街拍质感。", "自然日光或轻微电影感光影，模特行走或站立，背景有城市线条但不抢主体。"),
    ("cafe", "街角咖啡", "街角咖啡店或休闲空间，强化服装的生活方式氛围和亲和力。", "暖色自然光，模特坐姿或站姿放松，画面带轻松社交和日常出街感。"),
    ("lawn", "自然草坪", "公园草坪或自然绿地场景，呈现舒适、清新、自然的穿搭氛围。", "柔和户外光线，背景清爽不过度杂乱，模特姿态自然舒展。"),
    ("beach", "度假海滩", "海滩或滨海步道场景，突出服装在户外度假场景中的搭配效果。", "明亮自然光和轻松假日氛围，模特动作轻盈，画面干净通透。"),
    ("home", "温馨居家", "居家室内场景，展示服装的舒适度、日常感和亲和力。", "柔和窗光、简洁家具和温暖色调，模特自然坐立或轻松活动。"),
    ("gallery", "艺术展馆", "艺术展馆或现代极简空间，突出服装的时尚感和高级质感。", "留白充足、线条干净、光影高级，模特姿态克制自然。"),
]


def _catalog_rows() -> list[dict]:
    rows: list[dict] = []
    for index, (item_id, name, description, strategy) in enumerate(PRODUCT_IMAGE_MODULES, start=1):
        rows.append(
            {
                "scenario": "product_image",
                "item_id": item_id,
                "name": name,
                "description": description,
                "strategy": strategy,
                "default_count": None,
                "max_count": None,
                "sort": index * 10,
            }
        )

    for index, (item_id, name, description, strategy, default_count, max_count) in enumerate(
        PRODUCT_SUITE_STRUCTURES,
        start=1,
    ):
        rows.append(
            {
                "scenario": "product_suite",
                "item_id": item_id,
                "name": name,
                "description": description,
                "strategy": strategy,
                "default_count": default_count,
                "max_count": max_count,
                "sort": index * 10,
            }
        )

    for index, (item_id, name, description, strategy) in enumerate(OUTFIT_SCENES, start=1):
        rows.append(
            {
                "scenario": "outfit",
                "item_id": item_id,
                "name": name,
                "description": description,
                "strategy": strategy,
                "default_count": None,
                "max_count": None,
                "sort": index * 10,
            }
        )
    return rows


async def upsert_catalog() -> tuple[int, int, int]:
    inserted = 0
    updated = 0
    unchanged = 0

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with SessionLocal() as db:
        for row in _catalog_rows():
            result = await db.execute(
                select(ProductCatalog)
                .where(
                    ProductCatalog.scenario == row["scenario"],
                    ProductCatalog.item_id == row["item_id"],
                )
                .limit(1)
            )
            item = result.scalar_one_or_none()
            if item is None:
                db.add(ProductCatalog(**row, enabled=True))
                inserted += 1
                continue

            changed = False
            for field_name in (
                "name",
                "description",
                "strategy",
                "default_count",
                "max_count",
            ):
                value = row[field_name]
                if getattr(item, field_name) != value:
                    setattr(item, field_name, value)
                    changed = True

            if changed:
                item.updated_at = utc_now()
                updated += 1
            else:
                unchanged += 1

        await db.commit()

    return inserted, updated, unchanged


async def main() -> None:
    inserted, updated, unchanged = await upsert_catalog()
    print(
        "product catalog seeded:",
        f"inserted={inserted}",
        f"updated={updated}",
        f"unchanged={unchanged}",
    )


if __name__ == "__main__":
    asyncio.run(main())
