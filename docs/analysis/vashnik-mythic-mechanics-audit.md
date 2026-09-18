# Mythic Vashnik mechanics report audit

Audited and implemented 2026-09-17. This document records the evidence and limits behind `vashnik-the-malignant-mythic-mechanics`.

## Recommendation

Use the **Entombed Sentinels mechanics report** as the interaction model: one Mechanics report, a subreport selector, all-pulls/specific-pull selection, rows grouped by pull, and expandable chronological evidence. Provide player/healer bars where attribution is explicit. Scope merged reports by **report code and fight ID**, as Sentinels does.

Recommended initial subreports:

| Subreport | Main rows and columns | Expanded evidence | Readiness |
| --- | --- | --- | --- |
| **Totems & Plague Waves** | One row per Imbibe/totem set: fountains, spawned, removed before failure, detonated, unresolved | Each Froth wave's carriers, release times, associated totem removals, remaining totems, failure deadlines; inferred owner only when uniquely supported | High for group handling; very limited individual attribution |
| **Plague Froth Spreading** | One row per Froth set: marked players, unmarked splash victims/hits, wave-hit victims, early releases | Assignment lifetimes, deaths during Froth, splash and wave damage timeline | High for assignments and exposure; do not label a splash victim as its cause |
| **Exploding Infection Dispels** | One row per infection set: targets, dispeller and timestamp, hold duration, peak stacks, explosion spacing | Explicit dispels, early/unmatched removals, raid damage around explosions; healer dispel bars | High |
| **Stygian Infection Healing** | One row per infection set: targets, clear times, died/unresolved, absorb healing | Per-player absorb lifetime and healer contribution bars; nearby Stygian Burst events | High, including actual absorb-healing attribution |
| **Living Venom Control** | One row per add life: type, observed lifetime, kill/leak/unresolved, damage contributors | Shrouded shield removal and shield damage; Burning death spacing and overlapping Surge; add-originated raid damage | High for observed lives; Burning spawn timestamps are incomplete |
| **Catalytic Bile Soaks** | One row per Catalyst: who soaked, soak hit events, missed-soak bursts, failure damage | Per-impact timestamps and participants; player participation bars | High for participation; exact missed-circle count is not always identifiable |

Include fountain selections and infusion stacks as context in Totems and Adds. A separate tank-swap or fountain-pressure view can follow, but the six above add more beyond the existing base reports. Defer Siphoning Infection until blood-fountain Mythic logs are inspected.

## Evidence cohort

The same **12 Mythic pulls** used for the base reports were examined in greater detail:

- [AZfwY8vr1DanQbch, fight 40](https://www.warcraftlogs.com/reports/AZfwY8vr1DanQbch?fight=40): clean 323.5-second kill.
- [Nr7yQvGqjz8atHYc](https://www.warcraftlogs.com/reports/Nr7yQvGqjz8atHYc): fights 11, 13, 14, 15; three wipes and one kill.
- [6x4fbqFQLagcRCKD](https://www.warcraftlogs.com/reports/6x4fbqFQLagcRCKD): fights 36, 37, 38, 40, 41, 42, 43; six wipes and one kill.

Reviewed the [Mythic Trap guide](https://www.mythictrap.com/en/venomous-abyss/vashnik-the-malignant/mythic), the existing Sentinels fetch/calculation/model/rendering modules, and the spell descriptions linked below. Pulled All events involving totems, player debuffs, player/enemy deaths, hostile casts/buffs, dispels, add summons, and Stygian heal-absorb events. Also inspected a full kill's add-damage and healing streams. Player metrics exclude pets; pet damage contribution should be credited to owners.

Compact per-pull counts are saved alongside this document in `vashnik-mythic-mechanics-audit.json`. Raw event research is cached under `.local/vashnik/` and is not application data.

## Can we identify whose waves clear totems?

**Usually we can identify the five-player wave group, but not one player. A few isolated early releases support explicitly labeled inference.**

Across the cohort:

| Observation | Count |
| --- | ---: |
| Imbibe completions | 44 |
| Logged totem summons | 1,056 |
| Totem deaths | 878 |
| Totem deaths with a logged player killer | 0 |
| Totems completing Malignance | 14 |
| Death without a prior Malignance completion | 873 |
| Failed totem subsequently removed | 5 |
| Failed totem without a later death | 9 |
| No observed death or completed cast by pull end | 169 |
| Froth applications, using the actual six-second aura | 426 |
| Froth assignment groups | 86 |

All 878 totem deaths use `sourceID=-1`, `abilityGameID=0`, and have no `killerID` or `killingAbilityGameID`. All-events queries find no player damage to the totems. Summons and deaths contain no coordinates. Completed Malignance casts expose the **failed** totem's position; damage-event coordinates belong to the victim (`resourceActor=2`), not the totem. That sparse position data cannot locate normally cleared totems or support a general geometric attribution algorithm.

Normal Froth carriers release within the same few milliseconds. Their wave-hit events are sourced to **Vashnik**, not the originating player. Choosing the nearest aura-removal timestamp would fabricate precision.

### A useful group-level result

In the clean kill, 96 totems spawn, 92 die, and none complete Malignance. Four have no recorded death before the boss dies: these are **censored at encounter end**, not failed assignments.

At **59.994 seconds**, five carriers release together. **16 totems die over the next 4.644 seconds**. At **93.006 seconds**, the next five-player group releases and seven more die. These make useful expandable wave rows, without pretending to know which carrier earned each clear.

Also preserve cross-set travel: the first Froth releases at **19.028 seconds**, before the first totems spawn around 24.6 seconds, and a totem dies at **25.445 seconds**. Matching only waves released after a totem's spawn would miss this removal.

### A defensible individual inference

In [Nr7yQvGqjz8atHYc, fight 13](https://www.warcraftlogs.com/reports/Nr7yQvGqjz8atHYc?fight=13):

| Pull time | Evidence |
| --- | --- |
| 138.061 | Lazerzpewpew receives Froth with four other players |
| 142.078 | Their Froth removes early, after 4.017 seconds |
| 142.079 | Their death is logged |
| 142.136 | A Plague Wave hit occurs |
| 142.157 / 142.473 / 142.584 | Three totems die |
| 144.065-144.066 | The other four carriers' Froth expires |

Those first three totem deaths can reasonably be labeled **likely cleared by Lazerzpewpew's early wave**, because no other carrier has released. This is an inference from timing and observed wave hits, not a WCL kill-credit field. It must also show that the release occurred on death; it is not necessarily successful assigned play.

A fourth totem dies at 143.952, just 113 ms before the other carriers' removal events. Leave it ambiguous under a conservative timestamp tolerance.

An exploratory rule using a 10-second travel window and a 250-ms boundary tolerance produces:

- Six deaths with only one candidate carrier: three for Lazerzpewpew, one for Grisnaingui (report 6x4..., fight 36), and two for Bowerdemo (fight 43).
- Eight with two candidates, one with three, and **863 with five**.

This is only **six of 878** potential individual attributions. The window is an audited heuristic, not a proven projectile lifetime; observed normal-wave removal delays extend to 7.774 seconds. The other isolated cases lack the same independent wave-hit corroboration as the example above. Do not build a general per-player totem leaderboard from these results.

Recommended attribution labels: **logged**, **inferred single carrier**, **wave group only**, and **unknown**. Most totem rows will be wave-group-only. A zero inferred-clear count must never mean that a player cleared zero totems.

## Signals and implementation constraints

### Totems and Froth

- Totem summon: **1306820**, WCL NPC name **Malignant Totem**; source stalkers identify Fire/Shadow fountains.
- Malignance begin/completion: **1304459**. Count completed `cast` events per totem life, not every damage victim or every `begincast`. A completed Malignance can be followed by another cast attempt.
- Froth assignment: **1281913**. The other same-name aura **1281910** often removes immediately or after two seconds; it is not the six-second wave-release clock.
- Froth splash: **1281925**; Plague Wave damage: **1295798**.
- In this sample, 991 of 3,598 Froth player-hit rows occur on players without the active assignment, using a 250-ms aura-boundary tolerance. These are useful exposure events, not proof of which marked player caused them. Assigned players can also receive overlapping splash, so this is not a complete count of overlap mistakes.
- Maintain totem identity as report + fight + actor + instance + life. Retain late-cleared-after-detonation separately from clean removals. Missing deaths and encounter cleanup must not become successful clears.

### Exploding Infection

- Application/stacks/removal: **1295173**; explosion damage: **1295209**.
- 285 player applications and 271 explicit dispel events were observed; 268 dispels match observed application lifetimes. Preserve the remaining unmatched/extra events for inspection instead of inventing applications.
- Show dispeller and exact timestamp, holding time, stack progression, and gaps between explosions. Overlapping explosions should be visible with raid damage and nearby deaths.
- Removal can happen on death, immunity, or cleanup. Only explicit `dispel` events receive healer dispel credit. An aura removal alone does not identify its method.
- Avoid a universal fastest-dispel score: deliberately staggering explosions can be correct. Do not rank victim distance from explosion damage alone; mitigation, immunities and absorbs also affect damage.

### Stygian Infection

- Application/removal and healing absorb: **1294994**; ground impacts: **1302489**.
- 285 player assignments and **17,095 player-targeted `healabsorbed` events**, totaling **396,352,252** absorb healing, are available across the sample.
- Crucial fetch detail: ordinary friendly `Healing` events omit the encounter's hostile-source absorb records. Fetch `All` with `type = "healabsorbed" and ability.id = 1294994`. The absorb's `sourceID` is Vashnik; **`healerID`** identifies the contributing healer, and `extraAbilityGameID` identifies the healing spell.
- Match those events to a specific player's aura life. Show healer contributions and the last absorb-heal near removal; separate deaths and encounter-end removals from successful healing clears.
- On the clean kill, all 28 assignments remove alive, with a median observed removal time of **6.291 seconds** and **39,787,496** absorb healing.
- Nearby Stygian Burst hits provide exposure context. Do not automatically credit every burst in a set to every infected player.

### Living Venom

- Match enemy deaths, first instance-specific signals, and damage to each add life, as Sentinels does for Coagulations.
- **107 Burning Venom explosion casts** (`1285979`) and three adjacent explosion pairs less than three seconds apart were observed. Show actual gaps and the stacking Surge aura; a three-second gap is an inspection threshold, not a universal failure verdict.
- **Four Malignant Burst casts** (`1280189`) expose leaks. Count casts/instances rather than raid victim rows.
- Shrouded summons are logged, but the targeted summon stream did not contain Burning Venom summons. Label Burning lifespan as **observed lifetime**, beginning with its first reliable signal; do not claim true spawn-to-kill time.
- Shrouded shield: **Miasmic Coating 1312366**. Buff applications include shield capacity and removals expose shield resolution. Identical duplicate buff packets occur and need deduplication.
- Player add-damage events expose both health damage and `absorbed` damage. In the inspected kill, 10,357 of 25,798 add-damage rows have absorbed damage, totaling **187,392,240**. Dropping fully absorbed hits would omit much of the work on Shrouded Venoms. Show shield and health damage separately; include owned pets and exclude overkill.
- Clotting Venom remains a documented but unobserved variant in this cohort.

### Catalytic Bile

- Anchor sets to **1282509**; use **1282516** as supporting cast timing rather than counting both IDs as independent mechanics. The sampled pulls contain 83 primary Catalyst casts, including incomplete late casts.
- Successful player soak impacts: **1282602** (370 player-hit rows).
- Failed impacts: **1282616** (12 player-damage clusters at a 100-ms grouping tolerance).
- Show participants, hit events, damage, and failed-impact clusters. Fully absorbed player hits still show participation.
- A burst hitting 20 players is not 20 missed circles. Simultaneous failures can merge into one cluster, so label them **missed-soak bursts**, not an exact missed-circle count. A cast with no impact evidence should remain visible as incomplete/unobserved.

## Reuse from Entombed Sentinels

The reference implementation separates fetch/merge (`entombed_sentinels_mechanics.py`), pure per-pull calculators, event/aura lifetimes, data models, and the view-model renderer. Preserve that separation for Vashnik.

Reuse the existing page contract: `TableViewControlModel`, combined pull/view keys, grouped rows, `RowDetailsModel`, class-colored player lists, and contribution bars. There is no need for a new frontend renderer. If shared aura/lifetime or mechanics-row abstractions are extracted, retain the existing Sentinels entry points and run its regression tests before adding Vashnik behavior.

Suggested implementation sequence:

1. Totem/wave lifecycle and inference labels, with the clean kill and isolated early-release example as fixtures.
2. Stygian absorb resolution and Exploding Infection dispels.
3. Bile participation and Living Venom lifetimes/shields.
4. Froth exposure details; integrate the Mechanics page into the Mythic aggregate.

Required boundary coverage: simultaneous five-carrier releases, isolated early death, overlapping early releases, a pre-spawn wave clearing a new totem, late clear after Malignance, surviving totems at a kill, duplicate shield packets, shield-only add damage, unmatched dispels, missing aura removals, and repeated fight/actor/instance IDs across reports.

## Reproduction notes

Use `fetch_events` with `include_resources=True`, `use_actor_ids=True`, and explicit selected fight IDs. For totems, use `data_type="All"` and `source.name = "Malignant Totem" or target.name = "Malignant Totem"`. Use hostile casts/deaths/buffs for enemy lifecycles and default friendly debuffs/deaths/dispels for players. Filter all player metrics using the selected encounter roster, not merely an event's hostility.

Relevant spell references: [Froth aura](https://www.wowhead.com/spell=1281913/plague-froth), [Malignance](https://www.wowhead.com/spell=1304459/malignance), [Stygian Infection](https://www.wowhead.com/spell=1294994/stygian-infection), [Exploding Infection](https://www.wowhead.com/spell=1295173/exploding-infection), [Miasmic Coating](https://www.wowhead.com/spell=1312366/miasmic-coating).

## Implementation and verification

All six subreports are registered in the Mythic catalog and aggregate. They share the existing pull/mechanic selectors, expandable evidence groups, WCL pull links, and class-colored contribution bars. Dispels, Stygian, Adds, and Bile also offer aggregate or per-pull player/healer bars. Totems deliberately has no player leaderboard.

Totems now defaults to **Totem outcomes**: one compact stacked bar per set showing cleared, missed/detonated, and unresolved counts. Unresolved totems remain separate from misses. **Wave carriers** lists every Froth group with class-colored players, assignment and release timing, group-associated clears, and removals after detonation. It preserves zero-clear groups and assignments without a release; no missed-player count is inferred. **Totem details** retains the full individual evidence. Compact expanded rows show chronological wave and fountain context, avoiding a long totem list by default.

The cached 12-pull audit reproduces 1,056 totem summons, 873 removals before detonation, 14 detonated totem lives, 169 unresolved lives, and six single-carrier inferences. It also reproduces 426 Froth assignments and 991 unmarked splash hits, 271 explicit Exploding Infection dispels (three with no matched application), 285 Stygian applications with 396,352,252 absorb healing, and all 107 Burning Surges with three close pairs. The clean kill has 28 healing-supported Stygian clears and 187,392,240 shield damage. Bile has 369 non-immune soak hits; the audit's raw count of 370 included one immunity-only event. Missed-soak bursts remain 12.

Burning Surge casts arrive shortly after enemy death packets. The lifecycle helper attaches those casts to the preceding life while excluding delayed player attacks from damage credit. Shrouded shield applications are deduplicated, and shield removals near death are labeled possible cleanup. Infusion stacks and add-originated damage are context, not individual blame.

`tests/fixtures/vashnik_wave_inference.json` preserves the four totem deaths around the early Lazerzpewpew release: three single-carrier inferences and one ambiguous boundary. Synthetic tests cover pre-spawn waves, late removal after Malignance, encounter cleanup, absorbed hits, immunity exclusion, unmatched dispels, healer attribution, shield damage, owned pets, repeated instances, and merged reports sharing fight IDs.

Validation: full Python suite and frontend build; fresh live API captures for Vashnik and Sentinels mechanics; ghost, phase-damage, and add-damage comparisons against unchanged HEAD. Capture with `scripts/capture_regressions.py --case vashnik_mythic_mechanics --case sentinels_mythic_mechanics`. Raw captures remain under `.local/vashnik/mechanics-validation/`, not application data.
