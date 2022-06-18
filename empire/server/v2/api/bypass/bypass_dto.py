from datetime import datetime
from typing import List

from pydantic import BaseModel

from empire.server.v2.api.shared_dto import Author


def domain_to_dto_bypass(bypass):
    return Bypass(
        id=bypass.id,
        name=bypass.name,
        authors=bypass.authors or [],
        code=bypass.code,
        created_at=bypass.created_at,
        updated_at=bypass.updated_at,
    )


class Bypass(BaseModel):
    id: int
    name: str
    authors: List[Author]
    code: str
    created_at: datetime
    updated_at: datetime


class Bypasses(BaseModel):
    records: List[Bypass]


class BypassUpdateRequest(BaseModel):
    name: str
    code: str


class BypassPostRequest(BaseModel):
    name: str
    code: str
