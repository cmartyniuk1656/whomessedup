"""
Registry of reports exposed through the v2 UI-facing contract.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Tuple

from .avoidable_damage import ability_manifest_key, resolve_avoidable_manifest_abilities
from .boss_manifests import IMPERATOR_AVERZIAN_MANIFEST, VORASIUS_MANIFEST
from .common import _sanitize_report_code
from .dimensius_deaths import (
    OBLIVION_FILTER_DEFAULT,
    OBLIVION_FILTER_EXCLUDE_ALL,
    OBLIVION_FILTER_EXCLUDE_WITHOUT_RECENT,
    OBLIVION_FILTER_INCLUDE_ALL,
)
from .dimensius_priority_damage import PRIORITY_TARGETS
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
from .view_models.imperator_averzian_avoidable_damage import (
    REPORT_DEFAULT_FIGHT as REPORT_IMPERATOR_AVOIDABLE_DEFAULT_FIGHT,
    REPORT_DESCRIPTION as REPORT_IMPERATOR_AVOIDABLE_DESCRIPTION,
    REPORT_FOOTNOTES as REPORT_IMPERATOR_AVOIDABLE_FOOTNOTES,
    REPORT_ID as REPORT_IMPERATOR_AVOIDABLE_ID,
    REPORT_TITLE as REPORT_IMPERATOR_AVOIDABLE_TITLE,
)
from .view_models.imperator_averzian_deaths import (
    REPORT_DEFAULT_FIGHT as REPORT_IMPERATOR_DEATHS_DEFAULT_FIGHT,
    REPORT_DESCRIPTION as REPORT_IMPERATOR_DEATHS_DESCRIPTION,
    REPORT_FOOTNOTES as REPORT_IMPERATOR_DEATHS_FOOTNOTES,
    REPORT_ID as REPORT_IMPERATOR_DEATHS_ID,
    REPORT_TITLE as REPORT_IMPERATOR_DEATHS_TITLE,
)
from .view_models.lightblinded_vanguard_dispels import (
    REPORT_DEFAULT_FIGHT as REPORT_LIGHTBLINDED_DISPELS_DEFAULT_FIGHT,
    REPORT_DESCRIPTION as REPORT_LIGHTBLINDED_DISPELS_DESCRIPTION,
    REPORT_FOOTNOTES as REPORT_LIGHTBLINDED_DISPELS_FOOTNOTES,
    REPORT_ID as REPORT_LIGHTBLINDED_DISPELS_ID,
    REPORT_TITLE as REPORT_LIGHTBLINDED_DISPELS_TITLE,
)
from .view_models.lightblinded_vanguard_cooldowns import (
    REPORT_DEFAULT_FIGHT as REPORT_LIGHTBLINDED_COOLDOWNS_DEFAULT_FIGHT,
    REPORT_DESCRIPTION as REPORT_LIGHTBLINDED_COOLDOWNS_DESCRIPTION,
    REPORT_FOOTNOTES as REPORT_LIGHTBLINDED_COOLDOWNS_FOOTNOTES,
    REPORT_ID as REPORT_LIGHTBLINDED_COOLDOWNS_ID,
    REPORT_TITLE as REPORT_LIGHTBLINDED_COOLDOWNS_TITLE,
)
from .view_models.vorasius_damage import (
    REPORT_DEFAULT_FIGHT as REPORT_VORASIUS_DEFAULT_FIGHT,
    REPORT_DESCRIPTION as REPORT_VORASIUS_DESCRIPTION,
    REPORT_FOOTNOTES as REPORT_VORASIUS_FOOTNOTES,
    REPORT_ID as REPORT_VORASIUS_ID,
    REPORT_TITLE as REPORT_VORASIUS_TITLE,
)
from .view_models.vorasius_avoidable_damage import (
    REPORT_DEFAULT_FIGHT as REPORT_VORASIUS_AVOIDABLE_DEFAULT_FIGHT,
    REPORT_DESCRIPTION as REPORT_VORASIUS_AVOIDABLE_DESCRIPTION,
    REPORT_FOOTNOTES as REPORT_VORASIUS_AVOIDABLE_FOOTNOTES,
    REPORT_ID as REPORT_VORASIUS_AVOIDABLE_ID,
    REPORT_TITLE as REPORT_VORASIUS_AVOIDABLE_TITLE,
)
from .view_models.vorasius_deaths import (
    REPORT_DEFAULT_FIGHT as REPORT_VORASIUS_DEATHS_DEFAULT_FIGHT,
    REPORT_DESCRIPTION as REPORT_VORASIUS_DEATHS_DESCRIPTION,
    REPORT_FOOTNOTES as REPORT_VORASIUS_DEATHS_FOOTNOTES,
    REPORT_ID as REPORT_VORASIUS_DEATHS_ID,
    REPORT_TITLE as REPORT_VORASIUS_DEATHS_TITLE,
)
from .view_models.report_definitions import (
    ReportDifficulty,
    ReportDefinitionModel,
    RequestFieldKind,
    RequestFieldOptionModel,
    RequestFieldModel,
    RequestFieldTooltipModel,
    RequestSchemaModel,
)

ReportPayloadBuilder = Callable[[Dict[str, Any]], Tuple[Dict[str, Any], bool]]

JOB_V2_DIMENSIUS_ADD_DAMAGE = "v2_report_dimensius_add_damage"
JOB_V2_DIMENSIUS_DEATHS = "v2_report_dimensius_deaths"
JOB_V2_DIMENSIUS_PRIORITY_DAMAGE = "v2_report_dimensius_priority_damage"
JOB_V2_IMPERATOR_AVERZIAN_DAMAGE = "v2_report_imperator_averzian_damage"
JOB_V2_IMPERATOR_AVERZIAN_AVOIDABLE_DAMAGE = "v2_report_imperator_averzian_avoidable_damage"
JOB_V2_IMPERATOR_AVERZIAN_DEATHS = "v2_report_imperator_averzian_deaths"
JOB_V2_COOLDOWN_USAGE = "v2_report_cooldown_usage"
JOB_V2_LIGHTBLINDED_VANGUARD_COOLDOWNS = JOB_V2_COOLDOWN_USAGE
JOB_V2_LIGHTBLINDED_VANGUARD_DISPELS = "v2_report_lightblinded_vanguard_dispels"
JOB_V2_VORASIUS_DAMAGE = "v2_report_vorasius_damage"
JOB_V2_VORASIUS_AVOIDABLE_DAMAGE = "v2_report_vorasius_avoidable_damage"
JOB_V2_VORASIUS_DEATHS = "v2_report_vorasius_deaths"

BELOREN_FIGHT_ID = "beloren-child-of-alar"
CHIMAERUS_FIGHT_ID = "chimaerus-the-undreamt-god"
CROWN_OF_THE_COSMOS_FIGHT_ID = "crown-of-the-cosmos"
DIMENSIUS_FIGHT_ID = "dimensius-the-all-devouring"
FALLEN_KING_SALHADAAR_FIGHT_ID = "fallen-king-salhadaar"
IMPERATOR_AVERZIAN_FIGHT_ID = "imperator-averzian"
LIGHTBLINDED_VANGUARD_FIGHT_ID = "lightblinded-vanguard"
MIDNIGHT_FALLS_FIGHT_ID = "midnight-falls"
VAELGOR_AND_EZZORAK_FIGHT_ID = "vaelgor-and-ezzorak"
VORASIUS_FIGHT_ID = "vorasius"

COOLDOWN_USAGE_FIGHTS: Tuple[Tuple[str, str], ...] = (
    (IMPERATOR_AVERZIAN_FIGHT_ID, "Imperator Averzian"),
    (VORASIUS_FIGHT_ID, "Vorasius"),
    (FALLEN_KING_SALHADAAR_FIGHT_ID, "Fallen-King Salhadaar"),
    (VAELGOR_AND_EZZORAK_FIGHT_ID, "Vaelgor & Ezzorak"),
    (LIGHTBLINDED_VANGUARD_FIGHT_ID, "Lightblinded Vanguard"),
    (CROWN_OF_THE_COSMOS_FIGHT_ID, "Crown of the Cosmos"),
    (CHIMAERUS_FIGHT_ID, "Chimaerus, the Undreamt God"),
    (BELOREN_FIGHT_ID, "Belo'ren, Child of Al'ar"),
    (MIDNIGHT_FALLS_FIGHT_ID, "Midnight Falls"),
)


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


def _coerce_positive_int(values: Dict[str, Any], field_id: str) -> int | None:
    raw = values.get(field_id)
    if raw in (None, ""):
        return None
    try:
        value = int(raw)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_id} must be a whole number.") from exc
    if value <= 0:
        return None
    return value


def _coerce_float_range(
    values: Dict[str, Any],
    field_id: str,
    *,
    default: float,
    min_value: float,
    max_value: float,
) -> float:
    raw = values.get(field_id, default)
    if raw in (None, ""):
        return default
    try:
        value = float(raw)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_id} must be a number.") from exc
    if value < min_value or value > max_value:
        raise ValueError(f"{field_id} must be between {min_value:g} and {max_value:g}.")
    return value


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


def _build_ignore_after_deaths_field() -> RequestFieldModel:
    return RequestFieldModel(
        id="ignore_after_deaths",
        kind=RequestFieldKind.NUMBER,
        label="Ignore after deaths",
        description="Stop counting report events after this many total player deaths in a pull.",
        placeholder="No limit",
        defaultValue="",
    )


def _format_target_field_label(target: Any) -> str:
    bucket = getattr(target, "bucket", None)
    if bucket is None:
        return f"Include {target.label}"
    bucket_value = str(getattr(bucket, "value", bucket)).replace("_", " ").title()
    return f"Include {target.label} ({bucket_value})"


def _target_field_id(target: Any) -> str:
    return f"include_{target.slug}"


def _build_target_fields(manifest: Any) -> List[RequestFieldModel]:
    fields: List[RequestFieldModel] = []
    for target in getattr(manifest, "targets", ()) or ():
        fields.append(
            RequestFieldModel(
                id=_target_field_id(target),
                kind=RequestFieldKind.CHECKBOX,
                label=_format_target_field_label(target),
                defaultValue=bool(getattr(target, "default_enabled", True)),
            )
        )
    return fields


def _build_target_damage_scope_fields(boss_name: str) -> List[RequestFieldModel]:
    return [
        RequestFieldModel(
            id="kill_only",
            kind=RequestFieldKind.CHECKBOX,
            label="Include only kill pulls",
            description=f"Restrict the report to pulls where {boss_name} was killed.",
            defaultValue=False,
        ),
        RequestFieldModel(
            id="omit_dead_players",
            kind=RequestFieldKind.CHECKBOX,
            label="Omit data from players who died",
            description=(
                "Exclude a player's data from any pull where they died so that pull does not affect their "
                "averages."
            ),
            defaultValue=False,
        ),
        RequestFieldModel(
            id="fresh_run",
            kind=RequestFieldKind.CHECKBOX,
            label="Force fresh run (skip cache)",
            defaultValue=False,
        ),
    ]


def _avoidable_ability_field_id(ability: Any) -> str:
    return f"include_avoidable_{ability_manifest_key(ability)}"


def _build_avoidable_ability_fields(manifest: Any) -> List[RequestFieldModel]:
    fields: List[RequestFieldModel] = []
    for ability in resolve_avoidable_manifest_abilities(manifest):
        fields.append(
            RequestFieldModel(
                id=_avoidable_ability_field_id(ability),
                kind=RequestFieldKind.CHECKBOX,
                label=ability.name,
                defaultValue=True,
                tooltip=RequestFieldTooltipModel(
                    description=ability.description,
                    tags=list(ability.tags),
                ),
            )
        )
    return fields


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
    ignore_after_deaths = _coerce_positive_int(values, "ignore_after_deaths")
    fresh_run = _coerce_bool(values, "fresh_run", default=False)

    payload: Dict[str, Any] = {
        "report": report_code,
        "fight": fight_name,
        "oblivion_filter": oblivion_filter,
        "ignore_after_deaths": ignore_after_deaths,
    }
    return payload, fresh_run


def _build_dimensius_priority_damage_payload(values: Dict[str, Any]) -> Tuple[Dict[str, Any], bool]:
    report_code_raw = _coerce_text(values, "report_code", required=True)
    assert report_code_raw is not None
    report_code = _sanitize_report_code(report_code_raw)

    fight_name = _coerce_text(values, "fight_name", default=REPORT_PRIORITY_DEFAULT_FIGHT)
    fresh_run = _coerce_bool(values, "fresh_run", default=False)
    kill_only = _coerce_bool(values, "kill_only", default=False)
    omit_dead_players = _coerce_bool(values, "omit_dead_players", default=False)

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


def _build_target_damage_payload(
    values: Dict[str, Any],
    *,
    manifest: Any,
    default_fight: str,
) -> Tuple[Dict[str, Any], bool]:
    report_codes = _coerce_report_code_list(values)
    report_code = report_codes[0]
    extra_reports = report_codes[1:]

    fresh_run = _coerce_bool(values, "fresh_run", default=False)
    kill_only = _coerce_bool(values, "kill_only", default=False)
    omit_dead_players = _coerce_bool(values, "omit_dead_players", default=False)

    targets: List[str] = []
    for target in getattr(manifest, "targets", ()) or ():
        default_enabled = bool(getattr(target, "default_enabled", True))
        if _coerce_bool(values, _target_field_id(target), default=default_enabled):
            targets.append(target.slug)

    if not targets:
        raise ValueError("Select at least one target.")

    payload: Dict[str, Any] = {
        "report": report_code,
        "fight": default_fight,
        "extra_reports": extra_reports,
        "targets": targets,
        "kill_only": kill_only,
        "omit_dead_players": omit_dead_players,
    }
    return payload, fresh_run


def _build_imperator_averzian_damage_payload(values: Dict[str, Any]) -> Tuple[Dict[str, Any], bool]:
    return _build_target_damage_payload(
        values,
        manifest=IMPERATOR_AVERZIAN_MANIFEST,
        default_fight=REPORT_IMPERATOR_DEFAULT_FIGHT,
    )


def _build_vorasius_damage_payload(values: Dict[str, Any]) -> Tuple[Dict[str, Any], bool]:
    return _build_target_damage_payload(
        values,
        manifest=VORASIUS_MANIFEST,
        default_fight=REPORT_VORASIUS_DEFAULT_FIGHT,
    )


def _build_death_report_payload(
    values: Dict[str, Any],
    *,
    default_fight: str,
) -> Tuple[Dict[str, Any], bool]:
    report_codes = _coerce_report_code_list(values)
    report_code = report_codes[0]
    extra_reports = report_codes[1:]

    ignore_after_deaths = _coerce_positive_int(values, "ignore_after_deaths")
    fresh_run = _coerce_bool(values, "fresh_run", default=False)

    payload: Dict[str, Any] = {
        "report": report_code,
        "fight": default_fight,
        "extra_reports": extra_reports,
        "ignore_after_deaths": ignore_after_deaths,
    }
    return payload, fresh_run


def _build_imperator_averzian_deaths_payload(values: Dict[str, Any]) -> Tuple[Dict[str, Any], bool]:
    return _build_death_report_payload(
        values,
        default_fight=REPORT_IMPERATOR_DEATHS_DEFAULT_FIGHT,
    )


def _build_vorasius_deaths_payload(values: Dict[str, Any]) -> Tuple[Dict[str, Any], bool]:
    return _build_death_report_payload(
        values,
        default_fight=REPORT_VORASIUS_DEATHS_DEFAULT_FIGHT,
    )


def _build_avoidable_damage_payload(
    values: Dict[str, Any],
    *,
    manifest: Any,
    default_fight: str,
) -> Tuple[Dict[str, Any], bool]:
    report_codes = _coerce_report_code_list(values)
    report_code = report_codes[0]
    extra_reports = report_codes[1:]

    ignore_after_deaths = _coerce_positive_int(values, "ignore_after_deaths")
    fresh_run = _coerce_bool(values, "fresh_run", default=False)

    ability_keys: List[str] = []
    for ability in resolve_avoidable_manifest_abilities(manifest):
        ability_key = ability_manifest_key(ability)
        if _coerce_bool(values, _avoidable_ability_field_id(ability), default=True):
            ability_keys.append(ability_key)

    if not ability_keys:
        raise ValueError("Select at least one avoidable damage source.")

    payload: Dict[str, Any] = {
        "report": report_code,
        "fight": default_fight,
        "extra_reports": extra_reports,
        "ability_keys": ability_keys,
        "ignore_after_deaths": ignore_after_deaths,
    }
    return payload, fresh_run


def _build_imperator_averzian_avoidable_damage_payload(values: Dict[str, Any]) -> Tuple[Dict[str, Any], bool]:
    return _build_avoidable_damage_payload(
        values,
        manifest=IMPERATOR_AVERZIAN_MANIFEST,
        default_fight=REPORT_IMPERATOR_AVOIDABLE_DEFAULT_FIGHT,
    )


def _build_vorasius_avoidable_damage_payload(values: Dict[str, Any]) -> Tuple[Dict[str, Any], bool]:
    return _build_avoidable_damage_payload(
        values,
        manifest=VORASIUS_MANIFEST,
        default_fight=REPORT_VORASIUS_AVOIDABLE_DEFAULT_FIGHT,
    )


def _build_lightblinded_vanguard_dispels_payload(values: Dict[str, Any]) -> Tuple[Dict[str, Any], bool]:
    report_codes = _coerce_report_code_list(values)
    report_code = report_codes[0]
    extra_reports = report_codes[1:]

    exclude_revival_dispels = _coerce_bool(values, "exclude_revival_dispels", default=True)
    exclude_dead_player_sets = _coerce_bool(values, "exclude_dead_player_sets", default=False)
    fresh_run = _coerce_bool(values, "fresh_run", default=False)

    payload: Dict[str, Any] = {
        "report": report_code,
        "fight": REPORT_LIGHTBLINDED_DISPELS_DEFAULT_FIGHT,
        "extra_reports": extra_reports,
        "exclude_revival_dispels": exclude_revival_dispels,
        "exclude_dead_player_sets": exclude_dead_player_sets,
    }
    return payload, fresh_run


def _build_cooldown_usage_payload(
    values: Dict[str, Any],
    *,
    report_id: str,
    fight_name: str,
) -> Tuple[Dict[str, Any], bool]:
    report_codes = _coerce_report_code_list(values)
    report_code = report_codes[0]
    extra_reports = report_codes[1:]

    reminder_text = _coerce_text(values, "nsrt_reminders", required=True)
    tolerance_seconds = _coerce_float_range(
        values,
        "tolerance_seconds",
        default=7.5,
        min_value=0.0,
        max_value=15.0,
    )
    ignore_after_deaths = _coerce_positive_int(values, "ignore_after_deaths")
    ignore_after_healer_death = _coerce_bool(values, "ignore_after_healer_death", default=False)
    fresh_run = _coerce_bool(values, "fresh_run", default=False)

    payload: Dict[str, Any] = {
        "report_id": report_id,
        "report_title": REPORT_LIGHTBLINDED_COOLDOWNS_TITLE,
        "report": report_code,
        "fight": fight_name,
        "extra_reports": extra_reports,
        "reminder_text": reminder_text,
        "tolerance_seconds": tolerance_seconds,
        "ignore_after_deaths": ignore_after_deaths,
        "ignore_after_healer_death": ignore_after_healer_death,
    }
    return payload, fresh_run


def _build_lightblinded_vanguard_cooldowns_payload(values: Dict[str, Any]) -> Tuple[Dict[str, Any], bool]:
    return _build_cooldown_usage_payload(
        values,
        report_id=REPORT_LIGHTBLINDED_COOLDOWNS_ID,
        fight_name=REPORT_LIGHTBLINDED_COOLDOWNS_DEFAULT_FIGHT,
    )


def _make_cooldown_usage_payload_builder(*, report_id: str, fight_name: str) -> ReportPayloadBuilder:
    def build(values: Dict[str, Any]) -> Tuple[Dict[str, Any], bool]:
        return _build_cooldown_usage_payload(values, report_id=report_id, fight_name=fight_name)

    return build


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
                    _build_ignore_after_deaths_field(),
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
    REPORT_IMPERATOR_DEATHS_ID: RegisteredReport(
        definition=ReportDefinitionModel(
            id=REPORT_IMPERATOR_DEATHS_ID,
            title=REPORT_IMPERATOR_DEATHS_TITLE,
            description=REPORT_IMPERATOR_DEATHS_DESCRIPTION,
            fightId=IMPERATOR_AVERZIAN_FIGHT_ID,
            fightName=REPORT_IMPERATOR_DEATHS_DEFAULT_FIGHT,
            difficulty=ReportDifficulty.MYTHIC,
            defaultFight=REPORT_IMPERATOR_DEATHS_DEFAULT_FIGHT,
            footnotes=list(REPORT_IMPERATOR_DEATHS_FOOTNOTES),
            requestSchema=RequestSchemaModel(
                fields=[
                    _build_report_codes_field(),
                    _build_ignore_after_deaths_field(),
                    RequestFieldModel(
                        id="fresh_run",
                        kind=RequestFieldKind.CHECKBOX,
                        label="Force fresh run (skip cache)",
                        defaultValue=False,
                    ),
                ]
            ),
        ),
        job_type=JOB_V2_IMPERATOR_AVERZIAN_DEATHS,
        build_payload=_build_imperator_averzian_deaths_payload,
    ),
    REPORT_VORASIUS_DEATHS_ID: RegisteredReport(
        definition=ReportDefinitionModel(
            id=REPORT_VORASIUS_DEATHS_ID,
            title=REPORT_VORASIUS_DEATHS_TITLE,
            description=REPORT_VORASIUS_DEATHS_DESCRIPTION,
            fightId=VORASIUS_FIGHT_ID,
            fightName=REPORT_VORASIUS_DEATHS_DEFAULT_FIGHT,
            difficulty=ReportDifficulty.MYTHIC,
            defaultFight=REPORT_VORASIUS_DEATHS_DEFAULT_FIGHT,
            footnotes=list(REPORT_VORASIUS_DEATHS_FOOTNOTES),
            requestSchema=RequestSchemaModel(
                fields=[
                    _build_report_codes_field(),
                    _build_ignore_after_deaths_field(),
                    RequestFieldModel(
                        id="fresh_run",
                        kind=RequestFieldKind.CHECKBOX,
                        label="Force fresh run (skip cache)",
                        defaultValue=False,
                    ),
                ]
            ),
        ),
        job_type=JOB_V2_VORASIUS_DEATHS,
        build_payload=_build_vorasius_deaths_payload,
    ),
    REPORT_IMPERATOR_AVOIDABLE_ID: RegisteredReport(
        definition=ReportDefinitionModel(
            id=REPORT_IMPERATOR_AVOIDABLE_ID,
            title=REPORT_IMPERATOR_AVOIDABLE_TITLE,
            description=REPORT_IMPERATOR_AVOIDABLE_DESCRIPTION,
            fightId=IMPERATOR_AVERZIAN_FIGHT_ID,
            fightName=REPORT_IMPERATOR_AVOIDABLE_DEFAULT_FIGHT,
            difficulty=ReportDifficulty.MYTHIC,
            defaultFight=REPORT_IMPERATOR_AVOIDABLE_DEFAULT_FIGHT,
            footnotes=list(REPORT_IMPERATOR_AVOIDABLE_FOOTNOTES),
            requestSchema=RequestSchemaModel(
                fields=[
                    _build_report_codes_field(),
                    *_build_avoidable_ability_fields(IMPERATOR_AVERZIAN_MANIFEST),
                    _build_ignore_after_deaths_field(),
                    RequestFieldModel(
                        id="fresh_run",
                        kind=RequestFieldKind.CHECKBOX,
                        label="Force fresh run (skip cache)",
                        defaultValue=False,
                    ),
                ]
            ),
        ),
        job_type=JOB_V2_IMPERATOR_AVERZIAN_AVOIDABLE_DAMAGE,
        build_payload=_build_imperator_averzian_avoidable_damage_payload,
    ),
    REPORT_VORASIUS_AVOIDABLE_ID: RegisteredReport(
        definition=ReportDefinitionModel(
            id=REPORT_VORASIUS_AVOIDABLE_ID,
            title=REPORT_VORASIUS_AVOIDABLE_TITLE,
            description=REPORT_VORASIUS_AVOIDABLE_DESCRIPTION,
            fightId=VORASIUS_FIGHT_ID,
            fightName=REPORT_VORASIUS_AVOIDABLE_DEFAULT_FIGHT,
            difficulty=ReportDifficulty.MYTHIC,
            defaultFight=REPORT_VORASIUS_AVOIDABLE_DEFAULT_FIGHT,
            footnotes=list(REPORT_VORASIUS_AVOIDABLE_FOOTNOTES),
            requestSchema=RequestSchemaModel(
                fields=[
                    _build_report_codes_field(),
                    *_build_avoidable_ability_fields(VORASIUS_MANIFEST),
                    _build_ignore_after_deaths_field(),
                    RequestFieldModel(
                        id="fresh_run",
                        kind=RequestFieldKind.CHECKBOX,
                        label="Force fresh run (skip cache)",
                        defaultValue=False,
                    ),
                ]
            ),
        ),
        job_type=JOB_V2_VORASIUS_AVOIDABLE_DAMAGE,
        build_payload=_build_vorasius_avoidable_damage_payload,
    ),
    REPORT_LIGHTBLINDED_DISPELS_ID: RegisteredReport(
        definition=ReportDefinitionModel(
            id=REPORT_LIGHTBLINDED_DISPELS_ID,
            title=REPORT_LIGHTBLINDED_DISPELS_TITLE,
            description=REPORT_LIGHTBLINDED_DISPELS_DESCRIPTION,
            fightId=LIGHTBLINDED_VANGUARD_FIGHT_ID,
            fightName=REPORT_LIGHTBLINDED_DISPELS_DEFAULT_FIGHT,
            difficulty=ReportDifficulty.MYTHIC,
            defaultFight=REPORT_LIGHTBLINDED_DISPELS_DEFAULT_FIGHT,
            footnotes=list(REPORT_LIGHTBLINDED_DISPELS_FOOTNOTES),
            requestSchema=RequestSchemaModel(
                fields=[
                    _build_report_codes_field(),
                    RequestFieldModel(
                        id="exclude_revival_dispels",
                        kind=RequestFieldKind.CHECKBOX,
                        label="Exclude Revival dispels",
                        description=(
                            "Exclude Revival and same-player same-timestamp multi-dispel bursts from successful "
                            "dispel totals."
                        ),
                        defaultValue=True,
                    ),
                    RequestFieldModel(
                        id="exclude_dead_player_sets",
                        kind=RequestFieldKind.CHECKBOX,
                        label="Exclude sets after player death",
                        description="Remove shield sets from a player's average denominator after that player has died.",
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
        job_type=JOB_V2_LIGHTBLINDED_VANGUARD_DISPELS,
        build_payload=_build_lightblinded_vanguard_dispels_payload,
    ),
    REPORT_LIGHTBLINDED_COOLDOWNS_ID: RegisteredReport(
        definition=ReportDefinitionModel(
            id=REPORT_LIGHTBLINDED_COOLDOWNS_ID,
            title=REPORT_LIGHTBLINDED_COOLDOWNS_TITLE,
            description=REPORT_LIGHTBLINDED_COOLDOWNS_DESCRIPTION,
            fightId=LIGHTBLINDED_VANGUARD_FIGHT_ID,
            fightName=REPORT_LIGHTBLINDED_COOLDOWNS_DEFAULT_FIGHT,
            difficulty=ReportDifficulty.MYTHIC,
            defaultFight=REPORT_LIGHTBLINDED_COOLDOWNS_DEFAULT_FIGHT,
            footnotes=list(REPORT_LIGHTBLINDED_COOLDOWNS_FOOTNOTES),
            requestSchema=RequestSchemaModel(
                fields=[
                    _build_report_codes_field(),
                    RequestFieldModel(
                        id="nsrt_reminders",
                        kind=RequestFieldKind.TEXTAREA,
                        label="NSRT cooldown reminders",
                        description="Paste the NSRT cooldown-reminders string for Mythic Lightblinded Vanguard.",
                        placeholder="EncounterID:3180;Name:Vanguard - Mythic;Difficulty:Mythic\n"
                        "time:11;ph:1;tag:Player;spellid:31884;",
                        defaultValue="",
                        required=True,
                    ),
                    RequestFieldModel(
                        id="tolerance_seconds",
                        kind=RequestFieldKind.RANGE,
                        label="Timing tolerance",
                        description="Cooldown casts inside this +/- seconds window are counted as correct.",
                        defaultValue=7.5,
                        minValue=0,
                        maxValue=15,
                        step=0.5,
                    ),
                    _build_ignore_after_deaths_field(),
                    RequestFieldModel(
                        id="ignore_after_healer_death",
                        kind=RequestFieldKind.CHECKBOX,
                        label="Ignore events after a healer dies",
                        description="Stop counting cooldown assignments after the first healer death in each pull.",
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
        job_type=JOB_V2_LIGHTBLINDED_VANGUARD_COOLDOWNS,
        build_payload=_build_lightblinded_vanguard_cooldowns_payload,
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
                    *_build_target_fields(IMPERATOR_AVERZIAN_MANIFEST),
                    *_build_target_damage_scope_fields("Imperator Averzian"),
                ]
            ),
        ),
        job_type=JOB_V2_IMPERATOR_AVERZIAN_DAMAGE,
        build_payload=_build_imperator_averzian_damage_payload,
    ),
    REPORT_VORASIUS_ID: RegisteredReport(
        definition=ReportDefinitionModel(
            id=REPORT_VORASIUS_ID,
            title=REPORT_VORASIUS_TITLE,
            description=REPORT_VORASIUS_DESCRIPTION,
            fightId=VORASIUS_FIGHT_ID,
            fightName=REPORT_VORASIUS_DEFAULT_FIGHT,
            difficulty=ReportDifficulty.MYTHIC,
            defaultFight=REPORT_VORASIUS_DEFAULT_FIGHT,
            footnotes=list(REPORT_VORASIUS_FOOTNOTES),
            requestSchema=RequestSchemaModel(
                fields=[
                    _build_report_codes_field(),
                    *_build_target_fields(VORASIUS_MANIFEST),
                    *_build_target_damage_scope_fields("Vorasius"),
                ]
            ),
        ),
        job_type=JOB_V2_VORASIUS_DAMAGE,
        build_payload=_build_vorasius_damage_payload,
    ),
}


def _build_cooldown_usage_definition(*, report_id: str, fight_id: str, fight_name: str) -> RegisteredReport:
    return RegisteredReport(
        definition=ReportDefinitionModel(
            id=report_id,
            title=REPORT_LIGHTBLINDED_COOLDOWNS_TITLE,
            description=REPORT_LIGHTBLINDED_COOLDOWNS_DESCRIPTION,
            fightId=fight_id,
            fightName=fight_name,
            difficulty=ReportDifficulty.MYTHIC,
            defaultFight=fight_name,
            footnotes=list(REPORT_LIGHTBLINDED_COOLDOWNS_FOOTNOTES),
            requestSchema=RequestSchemaModel(
                fields=[
                    _build_report_codes_field(),
                    RequestFieldModel(
                        id="nsrt_reminders",
                        kind=RequestFieldKind.TEXTAREA,
                        label="NSRT cooldown reminders",
                        description=f"Paste the NSRT cooldown-reminders string for Mythic {fight_name}.",
                        placeholder="EncounterID:3180;Name:Boss - Mythic;Difficulty:Mythic\n"
                        "time:11;ph:1;tag:Player;spellid:31884;",
                        defaultValue="",
                        required=True,
                    ),
                    RequestFieldModel(
                        id="tolerance_seconds",
                        kind=RequestFieldKind.RANGE,
                        label="Timing tolerance",
                        description="Cooldown casts inside this +/- seconds window are counted as correct.",
                        defaultValue=7.5,
                        minValue=0,
                        maxValue=15,
                        step=0.5,
                    ),
                    _build_ignore_after_deaths_field(),
                    RequestFieldModel(
                        id="ignore_after_healer_death",
                        kind=RequestFieldKind.CHECKBOX,
                        label="Ignore events after a healer dies",
                        description="Stop counting cooldown assignments after the first healer death in each pull.",
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
        job_type=JOB_V2_COOLDOWN_USAGE,
        build_payload=_make_cooldown_usage_payload_builder(report_id=report_id, fight_name=fight_name),
    )


for _fight_id, _fight_name in COOLDOWN_USAGE_FIGHTS:
    _report_id = f"{_fight_id}-cooldowns"
    if _report_id in _REPORTS:
        continue
    _REPORTS[_report_id] = _build_cooldown_usage_definition(
        report_id=_report_id,
        fight_id=_fight_id,
        fight_name=_fight_name,
    )


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
    "JOB_V2_COOLDOWN_USAGE",
    "JOB_V2_DIMENSIUS_ADD_DAMAGE",
    "JOB_V2_DIMENSIUS_DEATHS",
    "JOB_V2_DIMENSIUS_PRIORITY_DAMAGE",
    "JOB_V2_IMPERATOR_AVERZIAN_AVOIDABLE_DAMAGE",
    "JOB_V2_IMPERATOR_AVERZIAN_DAMAGE",
    "JOB_V2_IMPERATOR_AVERZIAN_DEATHS",
    "JOB_V2_LIGHTBLINDED_VANGUARD_COOLDOWNS",
    "JOB_V2_LIGHTBLINDED_VANGUARD_DISPELS",
    "JOB_V2_VORASIUS_DAMAGE",
    "JOB_V2_VORASIUS_AVOIDABLE_DAMAGE",
    "JOB_V2_VORASIUS_DEATHS",
    "RegisteredReport",
    "build_report_job_request",
    "get_registered_report",
    "list_report_definitions",
]
