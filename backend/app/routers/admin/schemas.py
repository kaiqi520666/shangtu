from typing import Literal

from pydantic import BaseModel, Field

RoleValue = Literal["user", "super_admin"]
StatusValue = Literal["active", "disabled"]


class UpdateUserRequest(BaseModel):
    role: RoleValue | None = None
    status: StatusValue | None = None


class AdjustCreditsRequest(BaseModel):
    amount: int = Field(..., ge=-1000000, le=1000000)
    note: str = Field(..., min_length=1, max_length=255)


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
