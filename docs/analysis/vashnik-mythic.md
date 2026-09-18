# Mythic Vashnik: base reports

Verified 2026-09-17 using `docs/boss-manifest-scrape-playbook.md`.

## Sources and scope

Selected public reports from the WCL encounter 3455 Mythic rankings (difficulty 5), including progression pulls and kills:

| Report | Pulls | Result |
| --- | --- | --- |
| [AZfwY8vr1DanQbch](https://www.warcraftlogs.com/reports/AZfwY8vr1DanQbch?fight=40) | 40 | One 323.5-second kill |
| [Nr7yQvGqjz8atHYc](https://www.warcraftlogs.com/reports/Nr7yQvGqjz8atHYc?fight=15) | 11, 13, 14, 15 | Three wipes and one kill |
| [6x4fbqFQLagcRCKD](https://www.warcraftlogs.com/reports/6x4fbqFQLagcRCKD?fight=43) | 36, 37, 38, 40, 41, 42, 43 | Six wipes and one kill |

Reviewed **12 pulls: nine wipes and three kills**, spanning 122.6 to 426.2 seconds. Names come from report master data; roles come from WCL player details. Damage observations select player targets, reject player/pet sources, and retain the known encounter environmental hazard. Cross-checked sources, role counts, per-pull target counts, first timestamps, and largest 100-ms target clusters. Raw rows include zero-damage immunity events, so these are not mistake counts.

The [Mythic Trap guide](https://www.mythictrap.com/en/venomous-abyss/vashnik-the-malignant/mythic) describes clearing tumors with Plague Waves, dodgeable shadow impacts, fountain choices, and required soaks. Spell descriptions clarify [Malignance](https://www.wowhead.com/spell=1304459/malignance), [Stygian Burst](https://www.wowhead.com/spell=1302489/stygian-burst), and [Deadly Venom](https://www.wowhead.com/spell=1297338/deadly-venom).

## Implementation

The Mythic manifest composes the Heroic manifest, with **four selectable damage targets and 25 abilities**. Shared services and page builders select the manifest/configuration from the requested difficulty. Existing Heroic IDs and classifications remain unchanged. Frontend discovery uses the backend catalog; no new frontend component is needed.

| Report | ID |
| --- | --- |
| Damage | `vashnik-the-malignant-damage-mythic` |
| Deaths | `vashnik-the-malignant-deaths-mythic` |
| Avoidable Damage | `vashnik-the-malignant-avoidable-damage-mythic` |
| Cooldowns | `vashnik-the-malignant-cooldowns-mythic` |
| Aggregate Reports | `vashnik-the-malignant-mythic-aggregate-reports` |

The aggregate includes Damage, Deaths, and Avoidable Damage. Cooldowns uses the existing reminder workflow with encounter 3455 validation. The existing hidden Heroic mechanics scorecard is not promoted to Mythic without a separate mechanics analysis.

Targets remain Vashnik (WCL enemy name `Vashnik`), Burning Venom, Clotting Venom, and Shrouded Venom. The sampled groups activate fire and shadow: Clotting Venom and the three blood-fountain damage IDs are retained from the shared encounter mechanics, but were not observed in these Mythic pulls. Mythic Trap identifies the same blood adds and siphoning assignment on Mythic. Blood-fountain behavior deserves a follow-up log check if that strategy is used.

Tumors are logged as **Malignant Totem** (NPC 269430). Enemy casts and player damage confirm Malignance 1304459; a targeted enemy DamageTaken query found no direct damage rows for totems in the seven-pull report. They are cleared by waves, so they are not included as a DPS target. This base report does not attribute tumor clears to players.

## Observed damage coverage

The fixture `tests/fixtures/vashnik_mythic_observed.json` records all 22 retained encounter damage IDs, source/role distributions, per-pull counts and first-hit timings. The remaining three manifest IDs are shared blood-fountain mechanics: Siphoning Infection 1295224, Siphon Blood 1295229, and Hemo Expulsion 1298582.

| Damage | ID | Rows | Classification |
| --- | ---: | ---: | --- |
| Toxic Vapor | 1284561 | 32,931 | Raid Damage, Unavoidable, Soft Enrage, Stacking |
| Burning Presence | 1305901 | 18,630 | Raid Damage, Priority Add, Periodic |
| Caustic Surge | 1285979 | 8,163 | Raid Damage, Add Death, DoT, Stacking |
| Caustic Explosion | 1295209 | 5,444 | Raid Damage, Dispel, Staggered |
| Plague Froth | 1281925 | 3,598 | Targeted, Proximity, DoT, Spread |
| Malignance | 1304459 | 2,133 | Raid Damage, Raid Failure, DoT, Stacking, Mythic |
| Virulent Fumes | 1291467 | 1,957 | Avoidable, Area Denial, Fountain, Periodic |
| Congealing Bolt | 1305833 | 1,832 | Targeted, Priority Add, Slow, Stacking |
| Exploding Infection | 1295173 | 1,814 | Targeted, DoT, Dispel |
| Dripping Fangs (DoT) | 1280934 | 1,721 | Tank Mechanic, Unavoidable, DoT, Tank Swap |
| Malignant Catalyst | 1282525 | 1,498 | Raid Damage, Unavoidable, Bile Setup |
| Stygian Infection | 1294994 | 881 | Targeted, DoT, Healing Absorb |
| Conflagrating Expulsion | 1298587 | 863 | Raid Damage, Unavoidable, Imbibe, Flame Fountain |
| Gloom Expulsion | 1298583 | 862 | Raid Damage, Unavoidable, Imbibe, Shadow Fountain |
| Catalytic Bile (Soak) | 1282602 | 370 | Soak, Required Mechanic, Impact |
| Plague Wave | 1295798 | 338 | Avoidable, Line, Cardinal, Projectile |
| Deadly Venom | 1297338 | 148 | Avoidable, Area Denial, Periodic |
| Dripping Fangs (Impact) | 1280935 | 125 | Tank Mechanic, Unavoidable, Tank Swap |
| Stygian Burst | 1302489 | 94 | Avoidable, Swirl, Ground Impact |
| Catalytic Bile (Missed Soak) | 1282616 | 94 | Raid Damage, Missed Soak, Raid Failure |
| Umbral Ejection | 1286737 | 16 | Avoidable, Ground Impact, Add Death |
| Malignant Burst | 1280189 | 10 | Raid Damage, Add Leak, Raid Failure, DoT |

Avoidable selection: **Stygian Burst 1302489, Plague Wave 1295798, Virulent Fumes 1291467, Umbral Ejection 1286737, and Deadly Venom 1297338**.

Stygian Burst is an impact within 3.5 yards, separate from the assigned infection DoT; the guide identifies dodgeable ground markers. Its 94 rows affect small clusters (maximum four players), supporting the Mythic avoidable classification. Heroic's existing classification is intentionally retained within this Mythic-only change.

Malignance produced 2,133 player rows with clusters up to 20. It first appears around 112 seconds on several failed pulls, consistent with the totem's 85-second cast after the first Imbibe. Its initial hit and stacking DoT are group failure damage, not personal avoidability. Likewise, missed Catalytic Bile soaks and leaked Living Venoms do not assign personal fault to every raid member. Actual Bile soak damage and blood siphon participation remain required mechanics.

Dripping Fangs DoT exclusively hits tanks. Its impact has one non-tank row among 125, insufficient to redefine a tank mechanic as personal avoidability. Plague Froth mixes assigned and proximity damage under one ID; it remains unscored without assignment-aware attribution. Deadly Venom appears mostly late in wipes: retain its ground-hazard classification, and use the death cutoff to omit intentional wipe cleanup when desired.

## Intentionally excluded IDs

| ID | Effect | Reason |
| ---: | --- | --- |
| 1 | Melee | Generic boss auto-attacks; raw death context remains available |
| 1291461 | Virulent Fumes | All 15 rows have hitType 10, amount 0; wrapper immunity events, damage is 1291467 |
| 1305826 / 1305832 | Congealing Bolt | Eight immunity rows each, all zero damage; dummy/trigger spells, real damage is 1305833 |
| 132466 | Chi Wave | Five zero-damage player-effect artifacts attributed to hostile NPCs |
| 32409 | Shadow Word: Death | Player self-damage attributed to Environment |
| 387846 | Fel Armor | Player damage deferral |
| 1309786 | Refraction | Player effect |
| 1292299 | Seriously Sharp Seashell | Player gear effect |
| 1287955 | Rune of Void-Tainted Shell | Player gear effect |
| 453286 | Set Fire to the Pain | Player damage deferral |
| 6940 | Blessing of Sacrifice | Player damage transfer |
| 111400 | Burning Rush | Player self-damage |
| 361029 | Time Dilation | Player damage deferral |
| 448005 | Light of the Martyr | Player ability |

The [Virulent Fumes wrapper](https://www.wowhead.com/spell=1291461/virulent-fumes) and [Congealing Bolt trigger](https://www.wowhead.com/spell=1305826/congealing-bolt) share names with their damage subspells; keep IDs separate. Encounter casts such as Imbibe and Malignant Catalyst 1282516/1282509 are context rather than new damage IDs.

## Validation

- `.venv/Scripts/python.exe -m pytest -q`: 203 tests and three subtests passed, including all difficulty-routing, coverage, toggle, aggregate and cooldown checks.
- `python -m compileall -q app.py who_messed_up`: passed.
- `npm run build` in `frontend`: passed (existing browser data freshness warnings).
- New snapshot cases: `vashnik_mythic_damage`, `vashnik_mythic_deaths`, `vashnik_mythic_avoidable_damage`, using the seven-pull report above.

Live API smoke tests against `6x4fbqFQLagcRCKD` completed for all three base pages: each contains 20 player rows across seven pulls, with the expected Mythic page ID. Deaths totals 138 deaths (13 avoidable); Avoidable Damage totals 149,384,506 damage with no death cutoff. Snapshot artifacts are in `regression_snapshots_current/vashnik_mythic_*.json`.

Legacy `ghosts_first_per_set`, `nexus_phase_damage_full`, and `dimensius_add_damage_default` snapshots also completed. Saved historical goldens differ from current output, so each was rerun against an isolated, unchanged HEAD checkout: all three results are identical as parsed JSON to this working tree. The historical differences predate this change.

## Changed files

- `who_messed_up/services/manifests/midnight_season_2/vashnik_the_malignant.py`: Mythic manifest.
- `who_messed_up/services/manifests/midnight_season_2/__init__.py`, `who_messed_up/services/boss_manifests.py`, `who_messed_up/service.py`: registration and exports.
- `who_messed_up/services/report_registry.py`: Mythic definitions, payloads, cooldowns, and automatic aggregate discovery.
- `who_messed_up/services/vashnik_the_malignant_{damage,deaths,avoidable_damage}.py`: difficulty-aware service wrappers.
- `who_messed_up/services/view_models/vashnik_the_malignant_{damage,deaths,avoidable_damage}.py`, `app.py`: Mythic page identity and routing.
- `tests/test_boss_manifests.py`, `tests/test_vashnik_the_malignant_reports.py`, `tests/test_vashnik_mythic.py`, `tests/fixtures/vashnik_mythic_observed.json`: coverage, catalog and routing regressions.
- `scripts/capture_regressions.py`: three live regression cases.
- `README.md`, `docs/analysis/vashnik-mythic.md`: maintenance notes and evidence.

## Mechanics follow-up

See [the mechanics audit](vashnik-mythic-mechanics-audit.md) for six proposed subreports following the Sentinels report pattern, including group-level totem clearance and the limits of individual wave attribution.
