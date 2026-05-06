"""
Shared Pydantic models for the v2 report rendering contract.
"""
from __future__ import annotations

from enum import Enum
from typing import Dict, List, Optional, Union

from pydantic import BaseModel, Field

try:  # pragma: no cover - compatibility shim
    from pydantic import ConfigDict
except ImportError:  # pragma: no cover - pydantic v1
    ConfigDict = None

ScalarValue = Union[str, int, float, bool, None]


class ViewModelBase(BaseModel):
    if ConfigDict is not None:
        model_config = ConfigDict(populate_by_name=True, use_enum_values=True)
    else:
        class Config:
            allow_population_by_field_name = True
            use_enum_values = True


class SortDirection(str, Enum):
    ASC = "asc"
    DESC = "desc"


class TextAlign(str, Enum):
    LEFT = "left"
    RIGHT = "right"
    CENTER = "center"


class ValueFormat(str, Enum):
    TEXT = "text"
    INTEGER = "integer"
    DECIMAL = "decimal"


class TableFilterKind(str, Enum):
    MULTI_SELECT = "multi_select"


class CellKind(str, Enum):
    TEXT = "text"
    NUMBER = "number"
    PLAYER = "player"
    BADGE = "badge"
    LINK = "link"


class ContentVariant(str, Enum):
    TABLE = "table"


class RowDetailsVariant(str, Enum):
    EVENT_GROUPS = "event_groups"


class SortModel(ViewModelBase):
    column_id: str = Field(..., alias="columnId")
    direction: SortDirection


class HeaderTagModel(ViewModelBase):
    id: str
    label: str
    value: str


class ReportHeaderModel(ViewModelBase):
    subtitle: Optional[str] = None
    tags: List[HeaderTagModel] = Field(default_factory=list)


class SummaryMetricModel(ViewModelBase):
    id: str
    label: str
    value: ScalarValue
    format: Optional[ValueFormat] = None
    precision: Optional[int] = None
    display: Optional[str] = None


class TableFilterOptionModel(ViewModelBase):
    id: str
    label: str
    default_selected: bool = Field(True, alias="defaultSelected")


class TableFilterModel(ViewModelBase):
    id: str
    label: str
    kind: TableFilterKind = TableFilterKind.MULTI_SELECT
    options: List[TableFilterOptionModel] = Field(default_factory=list)


class TableViewOptionModel(ViewModelBase):
    value: str
    label: str


class TableViewControlModel(ViewModelBase):
    id: str
    label: str
    default_value: str = Field(..., alias="defaultValue")
    options: List[TableViewOptionModel] = Field(default_factory=list)


class DamageTableColumnGroupModel(ViewModelBase):
    target_id: str = Field(..., alias="targetId")
    label: str
    total_column_id: str = Field(..., alias="totalColumnId")
    average_column_id: str = Field(..., alias="averageColumnId")


class DamageTableFilterConfigModel(ViewModelBase):
    target_filter: TableFilterModel = Field(..., alias="targetFilter")
    metric_filter: TableFilterModel = Field(..., alias="metricFilter")
    selected_total_column_id: str = Field(..., alias="selectedTotalColumnId")
    selected_average_column_id: str = Field(..., alias="selectedAverageColumnId")
    target_columns: List[DamageTableColumnGroupModel] = Field(default_factory=list, alias="targetColumns")


class SpecAnalysisMetricModel(ViewModelBase):
    id: str
    label: str


class SpecAnalysisSortOptionModel(ViewModelBase):
    id: str
    label: str


class SpecAnalysisSeriesModel(ViewModelBase):
    id: str
    class_name: Optional[str] = Field(None, alias="className")
    spec_name: str = Field(..., alias="specName")
    color_token: Optional[str] = Field(None, alias="colorToken")
    player_count: int = Field(..., alias="playerCount")
    values: Dict[str, float] = Field(default_factory=dict)


class SpecAnalysisModel(ViewModelBase):
    button_label: str = Field(..., alias="buttonLabel")
    title: str
    subtitle: Optional[str] = None
    basis_label: Optional[str] = Field(None, alias="basisLabel")
    default_sort: str = Field(..., alias="defaultSort")
    sort_options: List[SpecAnalysisSortOptionModel] = Field(default_factory=list, alias="sortOptions")
    metrics: List[SpecAnalysisMetricModel] = Field(default_factory=list)
    series: List[SpecAnalysisSeriesModel] = Field(default_factory=list)


class TableColumnModel(ViewModelBase):
    id: str
    label: str
    align: TextAlign = TextAlign.LEFT
    sortable: bool = False
    cell_kind: CellKind = Field(..., alias="cellKind")
    format: Optional[ValueFormat] = None
    precision: Optional[int] = None


class TableCellIndicatorModel(ViewModelBase):
    id: str
    label: str
    tone: Optional[str] = None


class TableCellModel(ViewModelBase):
    value: ScalarValue
    display: Optional[str] = None
    sort_value: Optional[ScalarValue] = Field(None, alias="sortValue")
    href: Optional[str] = None
    color_token: Optional[str] = Field(None, alias="colorToken")
    tone: Optional[str] = None
    indicators: List[TableCellIndicatorModel] = Field(default_factory=list)


class RowDetailChildItemModel(ViewModelBase):
    id: str
    label: str
    kind: Optional[str] = None
    ability_label: Optional[str] = Field(None, alias="abilityLabel")
    ability_href: Optional[str] = Field(None, alias="abilityHref")
    timestamp_label: Optional[str] = Field(None, alias="timestampLabel")
    description: Optional[str] = None
    tone: Optional[str] = None
    tooltip: Optional[str] = None
    tooltip_badges: List[str] = Field(default_factory=list, alias="tooltipBadges")
    badges: List[str] = Field(default_factory=list)


class RowDetailItemModel(ViewModelBase):
    id: str
    label: str
    kind: Optional[str] = None
    ability_label: Optional[str] = Field(None, alias="abilityLabel")
    ability_href: Optional[str] = Field(None, alias="abilityHref")
    timestamp_label: Optional[str] = Field(None, alias="timestampLabel")
    description: Optional[str] = None
    tone: Optional[str] = None
    tooltip: Optional[str] = None
    tooltip_badges: List[str] = Field(default_factory=list, alias="tooltipBadges")
    badges: List[str] = Field(default_factory=list)
    children: List[RowDetailChildItemModel] = Field(default_factory=list)


class RowDetailGroupModel(ViewModelBase):
    id: str
    title: str
    subtitle: Optional[str] = None
    link: Optional[str] = None
    items: List[RowDetailItemModel] = Field(default_factory=list)


class RowDetailsModel(ViewModelBase):
    variant: RowDetailsVariant
    groups: List[RowDetailGroupModel] = Field(default_factory=list)


class TableRowModel(ViewModelBase):
    id: str
    cells: Dict[str, TableCellModel] = Field(default_factory=dict)
    details: Optional[RowDetailsModel] = None


class TableModel(ViewModelBase):
    default_sort: SortModel = Field(..., alias="defaultSort")
    columns: List[TableColumnModel] = Field(default_factory=list)
    rows: List[TableRowModel] = Field(default_factory=list)
    rows_by_view: Dict[str, List[TableRowModel]] = Field(default_factory=dict, alias="rowsByView")
    empty_state: str = Field(..., alias="emptyState")
    damage_filter_config: Optional[DamageTableFilterConfigModel] = Field(None, alias="damageFilterConfig")
    view_control: Optional[TableViewControlModel] = Field(None, alias="viewControl")


class ReportContentModel(ViewModelBase):
    variant: ContentVariant
    table: TableModel


class ReportPageModel(ViewModelBase):
    report_id: str = Field(..., alias="reportId")
    title: str
    report_code: str = Field(..., alias="reportCode")
    header: ReportHeaderModel
    summary: List[SummaryMetricModel] = Field(default_factory=list)
    content: ReportContentModel
    footnotes: List[str] = Field(default_factory=list)
    spec_analysis: Optional[SpecAnalysisModel] = Field(None, alias="specAnalysis")


__all__ = [
    "CellKind",
    "ContentVariant",
    "DamageTableColumnGroupModel",
    "DamageTableFilterConfigModel",
    "HeaderTagModel",
    "ReportContentModel",
    "ReportHeaderModel",
    "ReportPageModel",
    "RowDetailGroupModel",
    "RowDetailChildItemModel",
    "RowDetailItemModel",
    "RowDetailsModel",
    "RowDetailsVariant",
    "ScalarValue",
    "SortDirection",
    "SortModel",
    "SpecAnalysisMetricModel",
    "SpecAnalysisModel",
    "SpecAnalysisSeriesModel",
    "SpecAnalysisSortOptionModel",
    "SummaryMetricModel",
    "TableFilterKind",
    "TableFilterModel",
    "TableFilterOptionModel",
    "TableCellModel",
    "TableCellIndicatorModel",
    "TableColumnModel",
    "TableModel",
    "TableRowModel",
    "TableViewControlModel",
    "TableViewOptionModel",
    "TextAlign",
    "ValueFormat",
]
