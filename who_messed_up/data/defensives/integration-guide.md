# Defensive-audit integration guide

Version 1.0.0 · Research snapshot 2026-09-23

## Files

- `defensives.json`: authoritative catalogue, per-spec access and base timers, talent modifiers, shared pools, lockouts, single-talent examples and audit guidance.
- `defensives.schema.json`: structural validation schema; validates data shape, not combat rules.
- `icon-manifest.json`: file mapping, source URLs, image properties and hashes.
- `icons/`: preserve beside the JSON and HTML.
- `report.html` / `report.md`: human-readable research.

## Minimum audit input

For each actor and fight, collect specialization, fight-time selected talent entries and ranks, hero tree, alive/connected intervals, pre-pull state, cast events, aura applications/refreshes/stacks/removals, source/target identity, damage/healing/absorb events, resource spending and eligible hit/proc events. Add equipment, inventory and race evidence where those gates matter.

The Warcraft Logs combatant snapshot can supply build context, but the exact API representation must be verified in your integration. Do not assume an omitted talent list is an empty build, or that today’s armory loadout was used in the fight.

## Evaluation sequence

1. Select the matching historical catalogue version and actor specialization.
2. Resolve all access predicates. Confirm talent node, selected entry and rank; enforce mutually exclusive choices and hero-tree membership. If evidence is incomplete, return unknown.
3. Start from `specialization_profiles.base_cooldown_seconds`. The Retribution Divine Protection, non-tank Fortifying Brew and Guardian Barkskin inherent adjustments are already applied; do not apply them twice.
4. Apply eligible static modifiers only. `values_by_rank[0]` is rank 1. Intersect affected ability IDs and specialization applicability, then enforce `only_ability_spell_ids` on individual operations.
5. Replay cooldown/charge consumption, charge restoration, resets, resource-spend reductions and time-varying recovery in time order. More than one effective charge changes the ability to a charge pool even if its unmodified model says cooldown.
6. Resolve shared pools, active-variant replacements, Holy Armaments alternation and recipient lockouts.
7. Determine actual protection from observed auras and recipients. Distinguish manual casts, automatic procs and deliberate free casts; store whether the ordinary cooldown was consumed.
8. Compare eligible ready intervals with dangerous damage events and player exposure. Produce evidence-backed findings, with unknown results where the inputs cannot establish readiness or suitability.

## Stacking and timing

Static cooldown reductions and recovery rate are different. A 20% shorter 60-second timer is 48 seconds. A 20% faster countdown takes 50 seconds if maintained for the whole timer. A 75% recovery increase advances 1.75 seconds of cooldown per real second while its aura is active. Time Skip’s +1000% recovery gives 11 seconds of progress per real second before other effects. Do not replace a temporary recovery buff with a permanent timer multiplier.

The single-talent examples are arithmetic checks, not complete legal builds. Tooltips do not establish every ordering rule for combined flat and percentage modifiers, concurrent recovery buffs or charge resets. Keep an unverified combined timer provisional until validated. Node metadata prevents illegal combinations—for example, Spellwarding and Uther’s Counsel, or Time Skip’s Tomorrow, Today enhancement and Interwoven Threads.

Guardian Angel is event-relative: if the no-save Guardian Spirit aura expires, set the remaining cooldown to 60 seconds then. Do not simply model Guardian Spirit as a 60-second timer from the original cast. A normal 10-second aura implies 70 seconds from cast before other effects; an extended aura changes that boundary.

## Useful finding fields

Store `actor_id`, `fight_id`, `spell_id`, `catalogue_version`, `damage_event_window`, `activation_origin`, `cooldown_consumed`, `access_state`, `readiness_state`, `usability_state`, `suitability_state`, `charges_available`, `ready_at_or_range`, `observed_coverage`, `talent_evidence`, `event_evidence`, `confidence`, `reason_codes`, and `suggested_alternative_window`. Use explicit unknown values rather than false or zero when evidence is missing.

Recommended reason codes include `talent_not_selected`, `talent_snapshot_missing`, `wrong_active_variant`, `shared_pool_spent`, `charge_unavailable`, `recipient_lockout`, `missing_inventory_evidence`, `insufficient_resource`, `no_valid_target`, `wrong_damage_school`, `not_avoidable`, `immunity_bypassed`, `out_of_range`, `automatic_proc`, `free_proc_enabled_cast`, `aura_ended_early`, `uncertain_modifier_stacking`, and `incomplete_log`.

Show separate findings for ready-but-unused protection, poorly timed use, successful coverage and unknown cases. Reserve “wasted” for cases with strong evidence; low recorded absorption can mean a debuff was prevented or damage was successfully avoided.

## Baseline and support replay rules

### brew_tiger_palm

eligible Tiger Palm cast. Baseline brew reduction; additional talented reductions are separate. Validate replacement/proc casts before counting them.

```json
{
  "id": "brew_tiger_palm",
  "specialization_ids": [
    268
  ],
  "affected_ability_spell_ids": [
    115203,
    322507,
    1241059
  ],
  "condition": "eligible Tiger Palm cast",
  "trigger_spell_id": 100780,
  "operation": {
    "field": "remaining_cooldown_seconds",
    "operation": "add",
    "values_by_rank": [
      -1
    ]
  },
  "source_urls": [
    "https://www.wowhead.com/spell=100780"
  ],
  "note": "Baseline brew reduction; additional talented reductions are separate. Validate replacement/proc casts before counting them."
}
```

### brew_keg_smash

eligible Keg Smash cast. 

```json
{
  "id": "brew_keg_smash",
  "specialization_ids": [
    268
  ],
  "affected_ability_spell_ids": [
    115203,
    322507,
    1241059
  ],
  "condition": "eligible Keg Smash cast",
  "trigger_spell_id": 121253,
  "operation": {
    "field": "remaining_cooldown_seconds",
    "operation": "add",
    "values_by_rank": [
      -3
    ]
  },
  "source_urls": [
    "https://www.wowhead.com/spell=121253"
  ]
}
```

### impending_victory_reset

experience/honor-qualifying killing blow. Not every raid add death qualifies, and kill credit matters.

```json
{
  "id": "impending_victory_reset",
  "specialization_ids": [
    71,
    72,
    73
  ],
  "affected_ability_spell_ids": [
    202168
  ],
  "condition": "experience/honor-qualifying killing blow",
  "operation": {
    "field": "remaining_cooldown_seconds",
    "operation": "set",
    "values_by_rank": [
      0
    ]
  },
  "source_urls": [
    "https://www.wowhead.com/spell=202168"
  ],
  "note": "Not every raid add death qualifies, and kill credit matters."
}
```

### black_ox_restore

Black Ox Brew cast with talent selected. 

```json
{
  "id": "black_ox_restore",
  "specialization_ids": [
    268
  ],
  "affected_ability_spell_ids": [
    322507,
    1241059
  ],
  "trigger_spell_id": 115399,
  "condition": "Black Ox Brew cast with talent selected",
  "operation": {
    "field": "available_charges",
    "operation": "restore",
    "values_by_rank": [
      1
    ]
  },
  "source_urls": [
    "https://www.wowhead.com/spell=115399"
  ]
}
```

### cold_snap_reset

Cold Snap cast with talent selected. Charge restoration needs log validation. Does not clear Hypothermia.

```json
{
  "id": "cold_snap_reset",
  "specialization_ids": [
    64
  ],
  "affected_ability_spell_ids": [
    45438,
    414658,
    11426
  ],
  "trigger_spell_id": 235219,
  "condition": "Cold Snap cast with talent selected",
  "operation": {
    "field": "cooldown",
    "operation": "reset",
    "values_by_rank": [
      null
    ]
  },
  "charge_restore_count": null,
  "source_urls": [
    "https://www.wowhead.com/spell=235219"
  ],
  "note": "Charge restoration needs log validation. Does not clear Hypothermia."
}
```

### time_skip_recovery

Time Skip channel is active. 1000% faster means an extra 10 seconds of progress per elapsed second, before resolving other concurrent recovery effects.

```json
{
  "id": "time_skip_recovery",
  "specialization_ids": [
    1473
  ],
  "affected_ability_spell_ids": [
    363916,
    374227
  ],
  "trigger_spell_id": 404977,
  "condition": "Time Skip channel is active",
  "operation": {
    "field": "cooldown_recovery_rate",
    "operation": "add",
    "values_by_rank": [
      10
    ]
  },
  "source_urls": [
    "https://www.wowhead.com/spell=404977"
  ],
  "note": "1000% faster means an extra 10 seconds of progress per elapsed second, before resolving other concurrent recovery effects."
}
```

## Shared pools and target lockouts

```json
{
  "shared_pools": [
    {
      "id": "paladin_protection_blessings",
      "spell_ids": [
        1022,
        204018
      ],
      "type": "shared_cooldown",
      "notes": "Spellwarding is mutually exclusive with Uther\u2019s Counsel."
    },
    {
      "id": "mage_ice_block_variant",
      "spell_ids": [
        45438,
        414658
      ],
      "type": "replacement_shared_cooldown",
      "notes": "Only the selected active variant is available."
    },
    {
      "id": "monk_celestial_choice",
      "spell_ids": [
        322507,
        1241059
      ],
      "type": "mutually_exclusive_talent_variants",
      "notes": "One selected variant; reset effects target the selected brew."
    },
    {
      "id": "holy_armaments",
      "spell_ids": [
        432459,
        432472
      ],
      "type": "alternating_ability_shared_charges",
      "notes": "432472 is the related Sacred Weapon spell record, not a second defensive entry. Validate event mapping and next-armament state."
    }
  ],
  "target_lockouts": [
    {
      "name": "Forbearance",
      "aura_spell_id": 25771,
      "nominal_seconds": 30,
      "blocks_spell_ids": [
        642,
        633,
        1022,
        204018
      ],
      "exception_talent_spell_id": 146956,
      "exception_applies_to_spell_ids": [
        642
      ],
      "notes": "Check the recipient aura at cast time, not merely the caster cooldown."
    },
    {
      "name": "Hypothermia",
      "aura_spell_id": 41425,
      "nominal_seconds": 30,
      "blocks_spell_ids": [
        45438,
        414658
      ],
      "notes": "Cold Snap does not remove this lockout; more charges do not override it."
    }
  ]
}
```

## Known limitations

- This is a dated research catalogue, not an executable or combat-log-validated cooldown simulator. No user fight logs were supplied for replay validation.
- Individual static modifier values and simple examples are recorded. Ordering/stacking of multiple flat, percentage and recovery modifiers is not universally established by tooltips; unverified combinations must remain provisional.
- Some effect strengths depend on stats, talent ranks or hidden aura details; the report deliberately avoids a universal single-number defensive-value score.
- Some triggered spells share names or Lorrgs grouping records. Candidate event IDs must be validated against actual log event types before use.
- Charges restored by Cold Snap, Fiery Brand self-aura extension, empowered hero recovery rates and historical hotfix boundaries need particular integration testing.
