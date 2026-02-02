from datetime import date
from typing import Set

from pydantic import BaseModel, Field, field_validator


class Member(BaseModel):
    id: int
    name: str
    roles: Set[str]
    max_shifts: int = Field(default=4, ge=0)


class ServiceTemplate(BaseModel):
    event_template: str
    role: str
    min_qty: int = Field(ge=0)
    max_qty: int

    @field_validator("max_qty")
    @classmethod
    def check_max_qty(cls, v: int, info):
        if "min_qty" in info.data and v < info.data["min_qty"]:
            raise ValueError("max_qty must be greater than or equal to min_qty")
        return v


class AgendaEntry(BaseModel):
    date: date
    event_template: str


class RoleDemand(BaseModel):
    date: date
    event_type: str
    role: str
    min_qty: int = Field(ge=0)
    max_qty: int
    source: str = "Template"

    @property
    def is_mandatory(self):
        return self.min_qty > 0

    @field_validator("max_qty")
    @classmethod
    def check_max_qty(cls, v: int, info):
        if "min_qty" in info.data and v < info.data["min_qty"]:
            raise ValueError("max_qty must be greater than or equal to min_qty")
        return v
