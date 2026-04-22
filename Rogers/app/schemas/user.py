from datetime import datetime

from pydantic import BaseModel, ConfigDict


class UserPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str | None
    phone: str | None
    name: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
