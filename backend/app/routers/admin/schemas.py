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
