from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.core.coupons import normalize_coupon_code

RoleValue = Literal["user", "super_admin"]
StatusValue = Literal["active", "disabled"]


class UpdateUserRequest(BaseModel):
    role: RoleValue | None = None
    status: StatusValue | None = None


class UpdateUserBusinessRequest(BaseModel):
    consumption_multiplier: Decimal | None = Field(
        default=None, ge=Decimal("0.01"), le=Decimal("9.99"), decimal_places=2
    )
    distribution_enabled: bool | None = None
    commission_rate: Decimal | None = Field(default=None, ge=Decimal("0"), le=Decimal("100"), decimal_places=2)


class AdjustCreditsRequest(BaseModel):
    amount: int = Field(..., ge=-1000000, le=1000000)
    note: str = Field(..., min_length=1, max_length=255)

    @field_validator("note")
    @classmethod
    def note_not_blank(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("备注不能为空")
        return cleaned


class ResetUserPasswordRequest(BaseModel):
    new_password: str


class CreateCouponCodeRequest(BaseModel):
    code: str
    credits: int = Field(..., ge=1, le=10000000)
    usage_limit: int | None = Field(default=None, ge=1, le=1000000)
    enabled: bool = True

    @field_validator("code")
    @classmethod
    def normalize_code(cls, value: str) -> str:
        return normalize_coupon_code(value)


class UpdateCouponCodeRequest(BaseModel):
    credits: int | None = Field(default=None, ge=1, le=10000000)
    usage_limit: int | None = Field(default=None, ge=1, le=1000000)
    enabled: bool | None = None


class RechargePackageConfig(BaseModel):
    id: str = Field(..., min_length=1, max_length=64)
    name: str = Field(..., min_length=1, max_length=100)
    credits: int = Field(..., ge=1, le=10000000)
    amount_cents: int = Field(..., ge=1, le=100000000)
    badge: str = Field(default="", max_length=30)
    enabled: bool = True


class AdminSettingsRequest(BaseModel):
    image_credit_costs: dict[str, int]
    video_credit_costs: dict[str, int]
    digital_human_credit_costs: dict[str, int]
    digital_human_precharge_costs: dict[str, int]
    video_translation_credit_costs: dict[str, int]
    voiceover_credit_cost_per_100_chars: int = Field(..., ge=1, le=100000)
    recharge_packages: list[RechargePackageConfig]


class PromptTemplateRequest(BaseModel):
    scenario: str | None = Field(default=None, max_length=32)
    purpose: str = Field(..., min_length=1, max_length=32)
    platform: str | None = Field(default=None, max_length=64)
    type_id: str | None = Field(default=None, max_length=50)
    model: str = Field(..., min_length=1, max_length=64)
    name: str = Field(..., min_length=1, max_length=100)
    content: str = Field(..., min_length=1)
    version: int = Field(default=1, ge=1, le=100000)
    active: bool = True


class UpdateOutfitModelRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    sort_order: int | None = Field(default=None, ge=-100000, le=100000)
    active: bool | None = None


class ProductCatalogRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field(..., min_length=1)
    strategy: str = Field(..., min_length=1)
    default_count: int | None = Field(default=None, ge=1, le=100)
    max_count: int | None = Field(default=None, ge=1, le=100)
    enabled: bool = True
    sort: int = Field(default=0, ge=-100000, le=100000)


class UpdateHeygenResourceRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    sort_order: int | None = Field(default=None, ge=-100000, le=100000)
    enabled: bool | None = None


class UpdateHeygenTranslationLanguageRequest(BaseModel):
    display_name_zh: str | None = Field(default=None, min_length=1, max_length=120)
    sort_order: int | None = Field(default=None, ge=-100000, le=100000)
    enabled: bool | None = None
