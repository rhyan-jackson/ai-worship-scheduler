from datetime import date
from typing import List, Set

from pydantic import BaseModel, Field, model_validator


class Member(BaseModel):
    id: int
    name: str
    roles: Set[str]
    max_shifts: int = Field(default=4, ge=0)


class AgendaEntry(BaseModel):
    date: date
    event_template: str


class TemplateRule(BaseModel):
    role: str
    min_qty: int = Field(ge=0)
    max_qty: int = Field(ge=0)

    @model_validator(mode="after")
    def check_max_ge_min(self):
        if self.max_qty < self.min_qty:
            raise ValueError(
                f"Role '{self.role}': max_qty ({self.max_qty}) must be >= min_qty ({self.min_qty})"
            )
        return self


class EventTemplate(BaseModel):
    name: str
    rules: List[TemplateRule]


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

    @model_validator(mode="after")
    def check_max_ge_min(self):
        if self.max_qty < self.min_qty:
            raise ValueError("max_qty must be greater than or equal to min_qty")
        return self
