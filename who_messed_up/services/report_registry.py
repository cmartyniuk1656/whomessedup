"""
Registry of reports exposed through the v2 UI-facing contract.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Tuple

from .common import _sanitize_report_code
from .dimensius_deaths import (
    OBLIVION_FILTER_DEFAULT,
    OBLIVION_FILTER_EXCLUDE_ALL,
    OBLIVION_FILTER_EXCLUDE_WITHOUT_RECENT,
    OBLIVION_FILTER_INCLUDE_ALL,
)
from .dimensius_priority_damage import PRIORITY_TARGETS
from .imperator_averzian_damage import IMPERATOR_AVERZIAN_TARGETS
from .view_models.dimensius_add_damage import (
    REPORT_DEFAULT_FIGHT,
    REPORT_DESCRIPTION,
    REPORT_FOOTNOTES,
    REPORT_ID,
    REPORT_TITLE,
)
from .view_models.dimensius_deaths import (
    REPORT_DEFAULT_FIGHT as REPORT_DEATHS_DEFAULT_FIGHT,
    REPORT_DESCRIPTION as REPORT_DEATHS_DESCRIPTION,
    REPORT_FOOTNOTES as REPORT_DEATHS_FOOTNOTES,
    REPORT_ID as REPORT_DEATHS_ID,
    REPORT_TITLE as REPORT_DEATHS_TITLE,
)
from .view_models.dimensius_priority_damage import (
    REPORT_DEFAULT_FIGHT as REPORT_PRIORITY_DEFAULT_FIGHT,
    REPORT_DESCRIPTION as REPORT_PRIORITY_DESCRIPTION,
    REPORT_FOOTNOTES as REPORT_PRIORITY_FOOTNOTES,
    REPORT_ID as REPORT_PRIORITY_ID,
    REPORT_TITLE as REPORT_PRIORITY_TITLE,
)
from .view_models.imperator_averzian_damage import (
    REPORT_DEFAULT_FIGHT as REPORT_IMPERATOR_DEFAULT_FIGHT,
    REPORT_DESCRIPTION as REPORT_IMPERATOR_DESCRIPTION,
    REPORT_FOOTNOTES as REPORT_IMPERATOR_FOOTNOTES,
    REPORT_ID as REPORT_IMPERATOR_ID,
    REPORT_TITLE as REPORT_IMPERATOR_TITLE,
)
from .view_models.report_definitions import (
    ReportDifficulty,
    ReportDefinitionModel,
    RequestFieldKind,
    RequestFieldOptionModel,
    RequestFieldModel,
    RequestSchemaModel,
)

ReportPayloadBuilder = Callable[[Dict[str, Any]], Tuple[Dict[str, Any], bool]]

JOB_V2_DIMENSIUS_ADD_DAMAGE = "v2_report_dimensius_add_damage"
JOB_V2_DIMENSIUS_DEATHS = "v2_report_dimensius_deaths"
JOB_V2_DIMENSIUS_PRIORITY_DAMAGE = "v2_report_dimensius_priority_damage"
JOB_V2_IMPERATOR_AVERZIAN_DAMAGE = "v2_report_imperator_averzian_damage"

DIMENSIUS_FIGHT_ID = "dimensius-the-all-devouring"
IMPERATOR_AVERZIAN_FIGHT_ID = "imperator-averzian"


@dataclass(frozen=True)
class RegisteredReport:
    definition: ReportDefinitionModel
    job_type: str
    build_payload: ReportPayloadBuilder


def _coerce_text(
    values: Dict[str, Any],
    field_id: str,
    *,
    required: bool = False,
    default: str | None = None,
) -> str | None:
    raw = values.get(field_id, default)
    if raw is None:
        if required:
            raise ValueError(f"{field_id} is required.")
        return default
    text = str(raw).strip()
    if not text:
        if required:
            raise ValueError(f"{field_id} is required.")
        return default
    return text


def _coerce_bool(values: Dict[str, Any], field_id: str, *, default: bool = False) -> bool:
    raw = values.get(field_id, default)
    if isinstance(raw, bool):
        return raw
    if isinstance(raw, (int, float)):
        return bool(raw)
    if raw is None:
        return default
    text = str(raw).strip().lower()
    if text in {"1", "true", "yes", "on"}:
        return True
    if text in {"0", "false", "no", "off", ""}:
        return False
    raise ValueError(f"{field_id} must be a boolean.")


def _coerce_multi_text(values: Dict[str, Any], field_id: str) -> List[str]:
    raw = values.get(field_id, [])
    if raw is None:
        return []
    if isinstance(raw, list):
        candidates = raw
    else:
        candidates = [raw]
    items: List[str] = []
    for candidate in candidates:
        text = str(candidate or "").strip()
        if text:
            items.append(text)
    return items


def _coerce_additional_report_codes(
    values: Dict[str, Any],
    *,
    primary_report_code: str,
    field_id: str = "additional_reports",
) -> List[str]:
    extra_reports: List[str] = []
    for candidate in _coerce_multi_text(values, field_id):
        normalized = _sanitize_report_code(candidate)
        if normalized == primary_report_code or normalized in extra_reports:
            continue
        extra_reports.append(normalized)
    return extra_reports


def _coerce_report_code_list(
    values: Dict[str, Any],
    *,
    field_id: str = "report_codes",
) -> List[str]:
    report_codes: List[str] = []
    for candidate in _coerce_multi_text(values, field_id):
        normalized = _sanitize_report_code(candidate)
        if normalized in report_codes:
            continue
        report_codes.append(normalized)
    if not report_codes:
        raise ValueError("Add at least one Warcraft Logs report code or URL.")
    return report_codes


def _build_report_codes_field() -> RequestFieldModel:
    return RequestFieldModel(
        id="report_codes",
        kind=RequestFieldKind.MULTI_TEXT,
        label="Warcraft Logs report codes or URLs",
        placeholder="https://www.warcraftlogs.com/reports/...",
        defaultValue=[],
        required=True,
    )


def _build_additional_reports_field() -> RequestFieldModel:
    return RequestFieldModel(
        id="additional_reports",
        kind=RequestFieldKind.MULTI_TEXT,
        label="Additional report codes or URLs (optional)",
        placeholder="https://www.warcraftlogs.com/reports/...",
        defaultValue=[],
    )


def _build_dimensius_add_damage_payload(values: Dict[str, Any]) -> Tuple[Dict[str, Any], bool]:
    report_code_raw = _coerce_text(values, "report_code", required=True)
    assert report_code_raw is not None
    report_code = _sanitize_report_code(report_code_raw)

    fight_name = _coerce_text(values, "fight_name", default=REPORT_DEFAULT_FIGHT)
    ignore_first_add_set = _coerce_bool(values, "ignore_first_add_set", default=True)
    fresh_run = _coerce_bool(values, "fresh_run", default=False)

    extra_reports = _coerce_additional_report_codes(values, primary_report_code=report_code)

    payload: Dict[str, Any] = {
        "report": report_code,
        "fight": fight_name,
        "extra_reports": extra_reports,
        "ignore_first_add_set": ignore_first_add_set,
    }
    return payload, fresh_run


def _build_dimensius_deaths_payload(values: Dict[str, Any]) -> Tuple[Dict[str, Any], bool]:
    report_code_raw = _coerce_text(values, "report_code", required=True)
    assert report_code_raw is not None
    report_code = _sanitize_report_code(report_code_raw)

    fight_name = _coerce_text(values, "fight_name", default=REPORT_DEATHS_DEFAULT_FIGHT)
    oblivion_filter = _coerce_text(values, "oblivion_filter", default=OBLIVION_FILTER_DEFAULT)
    fresh_run = _coerce_bool(values, "fresh_run", default=False)

    payload: Dict[str, Any] = {
        "report": report_code,
        "fight": fight_name,
        "oblivion_filter": oblivion_filter,
    }
    return payload, fresh_run


def _build_dimensius_priority_damage_payload(values: Dict[str, Any]) -> Tuple[Dict[str, Any], bool]:
    report_code_raw = _coerce_text(values, "report_code", required=True)
    assert report_code_raw is not None
    report_code = _sanitize_report_code(report_code_raw)

    fight_name = _coerce_text(values, "fight_name", default=REPORT_PRIORITY_DEFAULT_FIGHT)
    fresh_run = _coerce_bool(values, "fresh_run", default=False)

    targets: List[str] = []
    target_field_map = {
        "include_artoshion": "artoshion",
        "include_pargoth": "pargoth",
        "include_nullbinder": "nullbinder",
        "include_voidwarden": "voidwarden",
    }
    for field_id, slug in target_field_map.items():
        if _coerce_bool(values, field_id, default=(slug == "artoshion")):
            targets.append(slug)

    payload: Dict[str, Any] = {
        "report": report_code,
        "fight": fight_name,
        "targets": targets,
    }
    return payload, fresh_run


def _build_imperator_averzian_damage_payload(values: Dict[str, Any]) -> Tuple[Dict[str, Any], bool]:
    report_codes = _coerce_report_code_list(values)
    report_code = report_codes[0]
    extra_reports = report_codes[1:]

    fresh_run = _coerce_bool(values, "fresh_run", default=False)

    targets: List[str] = []
    target_field_map = {
        "include_imperator_averzian": "imperator_averzian",
        "include_abyssal_voidshaper": "abyssal_voidshaper",
        "include_abyssal_annihilator": "abyssal_annihilator",
    }
    for field_id, slug in target_field_map.items():
        if _coerce_bool(values, field_id, default=True):
            targets.append(slug)

    if not targets:
        raise ValueError("Select at least one target.")

    payload: Dict[str, Any] = {
        "report": report_code,
        "fight": REPORT_IMPERATOR_DEFAULT_FIGHT,
        "extra_reports": extra_reports,
        "targets": targets,
    }
    return payload, fresh_run


_REPORTS: Dict[str, RegisteredReport] = {
    REPORT_ID: RegisteredReport(
        definition=ReportDefinitionModel(
            id=REPORT_ID,
            title=REPORT_TITLE,
            description=REPORT_DESCRIPTION,
            fightId=DIMENSIUS_FIGHT_ID,
            fightName=REPORT_DEFAULT_FIGHT,
            difficulty=ReportDifficulty.MYTHIC,
            defaultFight=REPORT_DEFAULT_FIGHT,
            footnotes=list(REPORT_FOOTNOTES),
            requestSchema=RequestSchemaModel(
                fields=[
                    RequestFieldModel(
                        id="report_code",
                        kind=RequestFieldKind.TEXT,
                        label="Report URL or code",
                        placeholder="https://www.warcraftlogs.com/reports/...",
                        required=True,
                    ),
                    RequestFieldModel(
                        id="fight_name",
                        kind=RequestFieldKind.TEXT,
                        label="Fight name",
                        defaultValue=REPORT_DEFAULT_FIGHT,
                    ),
                    _build_additional_reports_field(),
                    RequestFieldModel(
                        id="ignore_first_add_set",
                        kind=RequestFieldKind.CHECKBOX,
                        label="Ignore first add set",
                        defaultValue=True,
                    ),
                    RequestFieldModel(
                        id="fresh_run",
                        kind=RequestFieldKind.CHECKBOX,
                        label="Force fresh run (skip cache)",
                        defaultValue=False,
                    ),
                ]
            ),
        ),
        job_type=JOB_V2_DIMENSIUS_ADD_DAMAGE,
        build_payload=_build_dimensius_add_damage_payload,
    ),
    REPORT_DEATHS_ID: RegisteredReport(
        definition=ReportDefinitionModel(
            id=REPORT_DEATHS_ID,
            title=REPORT_DEATHS_TITLE,
            description=REPORT_DEATHS_DESCRIPTION,
            fightId=DIMENSIUS_FIGHT_ID,
            fightName=REPORT_DEATHS_DEFAULT_FIGHT,
            difficulty=ReportDifficulty.MYTHIC,
            defaultFight=REPORT_DEATHS_DEFAULT_FIGHT,
            footnotes=list(REPORT_DEATHS_FOOTNOTES),
            requestSchema=RequestSchemaModel(
                fields=[
                    RequestFieldModel(
                        id="report_code",
                        kind=RequestFieldKind.TEXT,
                        label="Report URL or code",
                        placeholder="https://www.warcraftlogs.com/reports/...",
                        required=True,
                    ),
                    _build_additional_reports_field(),
                    RequestFieldModel(
                        id="fight_name",
                        kind=RequestFieldKind.TEXT,
                        label="Fight name",
                        defaultValue=REPORT_DEATHS_DEFAULT_FIGHT,
                    ),
                    RequestFieldModel(
                        id="oblivion_filter",
                        kind=RequestFieldKind.SELECT,
                        label="Oblivion",
                        defaultValue=OBLIVION_FILTER_DEFAULT,
                        options=[
                            RequestFieldOptionModel(
                                value=OBLIVION_FILTER_INCLUDE_ALL,
                                label="Count all Oblivion deaths",
                            ),
                            RequestFieldOptionModel(
                                value=OBLIVION_FILTER_EXCLUDE_WITHOUT_RECENT,
                                label="Exclude Oblivion deaths preceded by instances of Airborne, Fists of the Voidlord, or Devour",
                            ),
                            RequestFieldOptionModel(
                                value=OBLIVION_FILTER_EXCLUDE_ALL,
                                label="Exclude all Oblivion deaths",
                            ),
                        ],
                    ),
                    RequestFieldModel(
                        id="fresh_run",
                        kind=RequestFieldKind.CHECKBOX,
                        label="Force fresh run (skip cache)",
                        defaultValue=False,
                    ),
                ]
            ),
        ),
        job_type=JOB_V2_DIMENSIUS_DEATHS,
        build_payload=_build_dimensius_deaths_payload,
    ),
    REPORT_PRIORITY_ID: RegisteredReport(
        definition=ReportDefinitionModel(
            id=REPORT_PRIORITY_ID,
            title=REPORT_PRIORITY_TITLE,
            description=REPORT_PRIORITY_DESCRIPTION,
            fightId=DIMENSIUS_FIGHT_ID,
            fightName=REPORT_PRIORITY_DEFAULT_FIGHT,
            difficulty=ReportDifficulty.MYTHIC,
            defaultFight=REPORT_PRIORITY_DEFAULT_FIGHT,
            footnotes=list(REPORT_PRIORITY_FOOTNOTES),
            requestSchema=RequestSchemaModel(
                fields=[
                    RequestFieldModel(
                        id="report_code",
                        kind=RequestFieldKind.TEXT,
                        label="Report URL or code",
                        placeholder="https://www.warcraftlogs.com/reports/...",
                        required=True,
                    ),
                    RequestFieldModel(
                        id="fight_name",
                        kind=RequestFieldKind.TEXT,
                        label="Fight name",
                        defaultValue=REPORT_PRIORITY_DEFAULT_FIGHT,
                    ),
                    RequestFieldModel(
                        id="include_artoshion",
                        kind=RequestFieldKind.CHECKBOX,
                        label=f"Include {PRIORITY_TARGETS['artoshion'].label}",
                        defaultValue=True,
                    ),
                    RequestFieldModel(
                        id="include_pargoth",
                        kind=RequestFieldKind.CHECKBOX,
                        label=f"Include {PRIORITY_TARGETS['pargoth'].label}",
                        defaultValue=False,
                    ),
                    RequestFieldModel(
                        id="include_nullbinder",
                        kind=RequestFieldKind.CHECKBOX,
                        label=f"Include {PRIORITY_TARGETS['nullbinder'].label}",
                        defaultValue=False,
                    ),
                    RequestFieldModel(
                        id="include_voidwarden",
                        kind=RequestFieldKind.CHECKBOX,
                        label=f"Include {PRIORITY_TARGETS['voidwarden'].label}",
                        defaultValue=False,
                    ),
                    RequestFieldModel(
                        id="fresh_run",
                        kind=RequestFieldKind.CHECKBOX,
                        label="Force fresh run (skip cache)",
                        defaultValue=False,
                    ),
                ]
            ),
        ),
        job_type=JOB_V2_DIMENSIUS_PRIORITY_DAMAGE,
        build_payload=_build_dimensius_priority_damage_payload,
    ),
    REPORT_IMPERATOR_ID: RegisteredReport(
        definition=ReportDefinitionModel(
            id=REPORT_IMPERATOR_ID,
            title=REPORT_IMPERATOR_TITLE,
            description=REPORT_IMPERATOR_DESCRIPTION,
            fightId=IMPERATOR_AVERZIAN_FIGHT_ID,
            fightName=REPORT_IMPERATOR_DEFAULT_FIGHT,
            difficulty=ReportDifficulty.MYTHIC,
            defaultFight=REPORT_IMPERATOR_DEFAULT_FIGHT,
            footnotes=list(REPORT_IMPERATOR_FOOTNOTES),
            requestSchema=RequestSchemaModel(
                fields=[
                    _build_report_codes_field(),
                    RequestFieldModel(
                        id="include_imperator_averzian",
                        kind=RequestFieldKind.CHECKBOX,
                        label=f"Include {IMPERATOR_AVERZIAN_TARGETS['imperator_averzian'].label}",
                        defaultValue=True,
                    ),
                    RequestFieldModel(
                        id="include_abyssal_voidshaper",
                        kind=RequestFieldKind.CHECKBOX,
                        label=f"Include {IMPERATOR_AVERZIAN_TARGETS['abyssal_voidshaper'].label}",
                        defaultValue=True,
                    ),
                    RequestFieldModel(
                        id="include_abyssal_annihilator",
                        kind=RequestFieldKind.CHECKBOX,
                        label=f"Include {IMPERATOR_AVERZIAN_TARGETS['abyssal_annihilator'].label}",
                        defaultValue=True,
                    ),
                    RequestFieldModel(
                        id="fresh_run",
                        kind=RequestFieldKind.CHECKBOX,
                        label="Force fresh run (skip cache)",
                        defaultValue=False,
                    ),
                ]
            ),
        ),
        job_type=JOB_V2_IMPERATOR_AVERZIAN_DAMAGE,
        build_payload=_build_imperator_averzian_damage_payload,
    ),
}


def list_report_definitions() -> List[ReportDefinitionModel]:
    return [registered.definition for registered in _REPORTS.values()]


def get_registered_report(report_id: str) -> RegisteredReport:
    try:
        return _REPORTS[report_id]
    except KeyError as exc:
        raise KeyError(f"Unknown report id '{report_id}'") from exc


def build_report_job_request(report_id: str, values: Dict[str, Any]) -> Tuple[str, Dict[str, Any], bool]:
    registered = get_registered_report(report_id)
    payload, fresh_run = registered.build_payload(values)
    if registered.definition.difficulty is not None and "difficulty" not in payload:
        difficulty = registered.definition.difficulty
        payload = dict(payload)
        payload["difficulty"] = getattr(difficulty, "value", difficulty)
    return registered.job_type, payload, fresh_run


__all__ = [
    "JOB_V2_DIMENSIUS_ADD_DAMAGE",
    "JOB_V2_DIMENSIUS_DEATHS",
    "JOB_V2_DIMENSIUS_PRIORITY_DAMAGE",
    "JOB_V2_IMPERATOR_AVERZIAN_DAMAGE",
    "RegisteredReport",
    "build_report_job_request",
    "get_registered_report",
    "list_report_definitions",
]
