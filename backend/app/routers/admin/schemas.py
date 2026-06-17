from typing import Literal

from pydantic import BaseModel, Field, field_validator

RoleValue = Literal["user", "super_admin"]
StatusValue = Literal["active", "disabled"]


class UpdateUserRequest(BaseModel):
    role: RoleValue | None = None
    status: StatusValue | None = None


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


class RechargePackageConfig(BaseModel):
    id: str = Field(..., min_length=1, max_length=64)
    name: str = Field(..., min_length=1, max_length=100)
    credits: int = Field(..., ge=1, le=10000000)
    amount_cents: int = Field(..., ge=1, le=100000000)
    badge: str = Field(default="", max_length=30)
    enabled: bool = True


class AdminSettingsRequest(BaseModel):
    image_credit_costs: dict[str, int]
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
