"""
Request-schema models for the v2 report-definition registry.
"""
from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import Field

from .common import ViewModelBase


class RequestFieldKind(str, Enum):
    TEXT = "text"
    NUMBER = "number"
    CHECKBOX = "checkbox"
    SELECT = "select"
    MULTI_TEXT = "multi_text"


class ReportDifficulty(str, Enum):
    HEROIC = "heroic"
    MYTHIC = "mythic"


class RequestFieldOptionModel(ViewModelBase):
    value: str
    label: str


class RequestFieldModel(ViewModelBase):
    id: str
    kind: RequestFieldKind
    label: str
    description: Optional[str] = None
    required: bool = False
    placeholder: Optional[str] = None
    default_value: Optional[Any] = Field(None, alias="defaultValue")
    options: List[RequestFieldOptionModel] = Field(default_factory=list)


class RequestSchemaModel(ViewModelBase):
    fields: List[RequestFieldModel] = Field(default_factory=list)


class ReportDefinitionModel(ViewModelBase):
    id: str
    title: str
    description: str
    fight_id: Optional[str] = Field(None, alias="fightId")
    fight_name: Optional[str] = Field(None, alias="fightName")
    difficulty: Optional[ReportDifficulty] = None
    default_fight: Optional[str] = Field(None, alias="defaultFight")
    footnotes: List[str] = Field(default_factory=list)
    request_schema: RequestSchemaModel = Field(..., alias="requestSchema")


class ReportDefinitionsResponseModel(ViewModelBase):
    reports: List[ReportDefinitionModel] = Field(default_factory=list)


class RunReportRequestModel(ViewModelBase):
    values: Dict[str, Any] = Field(default_factory=dict)


__all__ = [
    "ReportDifficulty",
    "ReportDefinitionModel",
    "ReportDefinitionsResponseModel",
    "RequestFieldKind",
    "RequestFieldModel",
    "RequestFieldOptionModel",
    "RequestSchemaModel",
    "RunReportRequestModel",
]
