# Mythic Entombed Sentinels: base and mechanics reports

Verified 2026-09-16 using `docs/boss-manifest-scrape-playbook.md`.

## Evidence and scope

- [Guild report J3y9gP2bqmkphY7f](https://www.warcraftlogs.com/reports/J3y9gP2bqmkphY7f): encounter **3445**, difficulty **5**, **11 wipes**, fights **15-19 and 21-26**. Pull lengths range from 82.9 to 433.4 seconds. Fight 20 is a non-encounter fragment and is excluded.
- [Mythic Trap Mythic guide](https://www.mythictrap.com/en/venomous-abyss/entombed-sentinels/mythic): checked the required soaks, infected-player pairing, intermission puzzle, and positioning hazards.
- [Wowhead guide and encounter journal](https://www.wowhead.com/guide/midnight/raids/venomous-abyss-entombed-sentinels-boss-strategy-abilities): checked which mechanics persist on Mythic and the distinction between assignments and explosion exposure.
- [Shifting Protovenom](https://www.wowhead.com/spell=1296878/shifting-protovenom) and [Protovenom Eruption](https://www.wowhead.com/spell=1296962/protovenom-eruption): checked collision rules and the eruption's 10-yard damage/knockback radius.

Downloaded player DamageTaken, hostile casts, player debuffs, hostile buffs, and dispels. Resolved spell names from report master data and player roles from player details. Filtered damage to the selected pulls' friendly-player IDs; excluded player/pet sources and the explicit self-damage exceptions below. Compared sources, roles, per-pull player counts, timings, and simultaneous damage clusters before choosing classifications.

The Mythic manifest composes the existing Heroic manifest, retaining **3 selectable damage targets**: Blood of Ula'tek, Breath of Ula'tek, and the priority add Venom Coagulation. Vashnik is the logged source of the Mythic mechanic, not an added damage target.

## Reports added

| Report | ID |
| --- | --- |
| Damage | `entombed-sentinels-damage-mythic` |
| Deaths | `entombed-sentinels-deaths-mythic` |
| Avoidable Damage | `entombed-sentinels-avoidable-damage-mythic` |
| Cooldowns | `entombed-sentinels-cooldowns-mythic` |
| Aggregate Reports | `entombed-sentinels-mythic-aggregate-reports` |
| Mechanics | `entombed-sentinels-mythic-mechanics` |

Existing Heroic IDs and defaults remain available, including `entombed-sentinels-cooldowns`. Both difficulties use the existing shared services and page builders. The Mythic aggregate includes Damage, Deaths, Avoidable Damage, and Mechanics; cooldowns retain their separate reminder-based workflow.

## Observed damage coverage

All **19** encounter/hazard damage spell IDs are manifested. Counts below are raw player-targeted event rows across the 11 wipes, without a death cutoff. They are observations, not counts of independent mistakes. The compact test fixture at `tests/fixtures/entombed_sentinels_mythic_observed.json` also records sources, role distributions, unique targets, and the largest 100-ms target cluster.

| Damage spell | ID | Rows | Base classification |
| --- | ---: | ---: | --- |
| Mark of Acid | 1284500 | 17,617 | Stacking side-assignment DoT |
| Mark of Blood | 1284506 | 16,847 | Stacking side-assignment DoT |
| Contaminate | 1284258 | 8,056 | Raid damage while priority add lives |
| Toxic Droplets | 1284451 | 1,528 | Required orb soak |
| Unstable Miasma | 1288282 | 497 | Required group soak |
| Bloodvenom Injection (DoT) | 1310126 | 2,988 | Tank damage |
| Blood Venom | 1284210 | 1,359 | Avoidable ground damage |
| Clinging Murk | 1303097 | 1,270 | Soak aftereffect |
| Living Venom | 1284209 | 270 | Avoidable projectile |
| Shifting Protovenom | 1296882 | 328 | Mythic assignment DoT |
| Empowering Slam | 1284458 | 119 | Tank damage |
| Noxious Blast | 1284452 | 218 | Raid damage from missed droplets |
| Bloodvenom Injection (Impact) | 1284487 | 117 | Tank damage |
| Helical Toxins | 1284813 | 1,488 | Intermission puzzle DoT |
| Blighted Blood | 1284471 | 233 | Assigned dispellable DoT |
| Deadly Venom | 1297338 | 226 | Avoidable environmental ground damage |
| Protovenom Eruption | 1296962 | 57 | Avoidable collision-explosion exposure |
| Cultivated Burst (Explosion) | 1284941 | 13 | Avoidable puzzle-failure damage |
| Cultivated Burst (DoT) | 1284948 | 30 | Avoidable puzzle-failure aftereffect |

Avoidable selection is the five existing Heroic damage IDs plus **1296962**. Eruption hit 16 different players in five pulls; its WCL source is **Vashnik**. This is evidence of exposure, not proof that the victim initiated the bad collision. That limitation appears in Mythic report footnotes and spell descriptions. Do not automatically label every eruption victim a failed carrier in a future mechanics report.

Protovenom's 328 damage ticks are not its assignment count: the aura stream contains **432 applications** of **1296880**, associated with **54 completed casts** of **1296878**. Fast pairing can clear an assignment before its first damage tick. The manifest correctly uses **1296882** for damage; assignment analysis must use the aura.

Both Injection components and Empowering Slam hit only the two tanks. Marks and Contaminate reached all 20 players over the report. Noxious Blast has raid-wide clusters of up to 20 targets, while intentional droplet pops are dispersed individual soaks. These observations support keeping tank damage, required soaks, and collective missed-orb damage out of individual avoidable selections.

## Intentionally ignored damage sources

No player-originated damage becomes an encounter ability. Observed exclusions:

| ID | Observed effect | Reason |
| ---: | --- | --- |
| 1 | Melee from the two Sentinels | Generic auto-attacks; death reports still retain raw hit context |
| 32409 | Shadow Word: Death | Player self-damage despite an Environment source in this report |
| 210380 | Blessing of Dawn | Player-originated effect |
| 1287955 | Rune of Void-Tainted Shell | Player gear effect |
| 124255 | Stagger | Player damage deferral |
| 387846 | Fel Armor | Player damage deferral |
| 1309786 | Refraction | Player-originated effect |
| 1292299 | Seriously Sharp Seashell | Player gear effect |
| 111400 | Burning Rush | Player self-damage |
| 361029 | Time Dilation | Player damage deferral |

Deadly Venom is deliberately retained even though WCL attributes it to Environment: it is the encounter's ground hazard. Exclusion is based on mechanic identity as well as actor type.

## Mechanics evidence

These IDs were observed in this report; names alone must not substitute for spell IDs.

| Candidate view | Useful signals | Attribution constraints |
| --- | --- | --- |
| Protovenom assignments and clear times | Cast 1296878; aura apply/remove 1296880; damage tick 1296882; eruption 1296962 | Match applications by wave and player. Removal can also mean death or encounter end. Damage source Vashnik cannot identify the colliding players. |
| Helical Toxins puzzle | Stasis casts/buffs 1284588 and 1284606; aura/stacks 1284590; damage 1284813; failure explosion 1284941, aura 1284947, DoT 1284948 | Both bosses log Stasis; deduplicate paired windows. Use stacks and removal timing, exclude death cleanup, and avoid inferring a partner from close timestamps alone. |
| Mythic intermission context | Concealing Shadows cast/buff 1297724 | Observed alongside 31 Stasis windows. Keep as context until its effect on puzzle information is separately verified. |
| Miasma soak participation | Cast 1288232; assignment aura 1288260; impact 1288282; Murk aura 1288297, damage 1303097 | Anchor to casts and match actual soak hits. Carrier, soaker, and aftereffect are separate observations. Some casts have no matching player aura late in wipes. |
| Droplet participation and misses | Cast 1284434; successful pop damage 1284451; failed-orb damage 1284452 | Pop hits show participation. One failed orb damages many players, so victim counts cannot count missed orbs. |
| Blighted Blood dispels | Cast 1284483; debuff 1284471; actual dispel events with `extraAbilityGameID` | Distinguish logged healer dispels from expiry and death removal; record duration and dispeller. |
| Coagulation uptime/damage | Summon cast 1284251; Contaminate cast/buff 1284257 and damage 1284258; damage to Venom Coagulation | Track add instances and lifetimes; raid-wide ticks do not count as individual mistakes. |
| Side swaps and tank pressure | Marks 1284500/1284506; Injection aura 1284491 and damage 1284487/1310126; Slam 1284458 | Ordinary mark overlap during a transition is expected. Require a defined reset/side policy before scoring. |
| Boss separation and damage balance | Dominance buffs 1290189/1290193; Stasis windows; both boss health/damage streams | Guides disagree on the separation radius (25 vs 40 yards); use logged buffs instead of assuming a geometric threshold. Stasis healing requires health/healing evidence beyond damage totals. |

## Reproduction and validation

With the local API running, capture the three new baselines using the shared helper. It now supports both legacy GET endpoints and v2 POST jobs, preserving the existing polling flow:

```powershell
.venv/Scripts/python.exe scripts/capture_regressions.py --base-url http://localhost:5511 --out-dir regression_snapshots_current --case sentinels_mythic_damage --case sentinels_mythic_deaths --case sentinels_mythic_avoidable_damage --case sentinels_mythic_mechanics
.venv/Scripts/python.exe -m compileall -q app.py who_messed_up scripts/capture_regressions.py
.venv/Scripts/python.exe -m pytest -q
cd frontend
npm run build
```

Direct application-job smoke tests against the supplied report returned the correct Mythic page IDs and all 11 pulls. Damage has 20 player rows and all three target breakdowns. With no death cutoff, Deaths reports 200 deaths (66 with an avoidable killing ability), and Avoidable Damage reports 223,186,839 damage. These are baseline totals over all wipes, not a diagnosis of the first failure in each pull.

Validation passed: 162 pytest tests plus 3 subtests, backend compilation, frontend production build, and all three new HTTP regression snapshot cases. The aggregate returned all three Mythic child pages. The cooldown workflow was smoke-tested on fight 26 with a synthetic assignment to validate plumbing only; no guild cooldown plan was inferred.

Raw research streams are disposable local data in `.local/sentinels/`; they contain no credentials. The committed observed-spell fixture and this document retain the reviewable metadata. No production deployment is included in this change.

## Implemented mechanics views

All seven views support Aggregate and individual pulls, including merged reports with overlapping fight IDs. Expandable rows show application/impact times, player evidence, and observed outcomes. No player scores or unverified pairing partners are inferred. Side Swaps & Tank Pressure was removed from the mechanics report, including its dedicated analysis and event queries; the underlying boss damage metadata remains available to the base reports.

Droplet Handling defaults to **Bars**, with a **Waves** toggle for the original expandable rows. Aggregate bars sum each player's observed droplet soaks across all selected pulls/reports; selecting a pull sums only that report/fight's waves. Bars sort by soak count and scale to the highest count within the current scope. Fully absorbed pop hits count, while Noxious Blast hits and pet targets do not. Counts are stored explicitly on each wave, not parsed from display text.

Expanded wave details show class-colored player soak bars for that wave in place of the Observed pops list. Noxious Blast event details remain available alongside the chart.

| View | Observed baseline across the 11 wipes |
| --- | --- |
| Protovenom Pairing | 54 waves, 432 aura assignments, 421 early removals alive, 57 eruption victim hit events |
| Helical Toxins | 31 deduplicated intermissions, 590 aura assignments, 538 early removals alive, 11 Cultivated Burst applications |
| Miasma Soaks | 63 completed casts, 497 player soak participations, 11 soaker deaths within two seconds of impact |
| Droplet Handling | 83 waves, 1,528 pop hit events, 16 Noxious Blast time clusters containing 218 victim hit events |
| Coagulation Kills | 53 confirmed kills; 1,267,961,464 player/pet damage, matching the base damage report; 563,711,914 Contaminate damage |
| Dispels | 34 Blighted Blood sets, 131 applications, 118 recorded dispels, 13 applications without dispel evidence |
| Intermission Resolution | 31 windows, 18 clean observed completions, 13.79s average clear, 8.12s fastest clear; 337,538,107 boss healing across all windows |

Implementation details and limits:

- Aura lifetimes start only on application packets. Death within one second of removal and removal within one second of pull end are censored. A missing removal before reapplication is retained as unresolved. Helical removals at its 28-second expiry are unresolved. “Removed alive” reports an observation, not proof of a correct partner or removal method.
- All 590 initial Helical aura applications in this report omit a stack count. The UI displays “not logged”, while preserving the 38 explicit stack changes. Cultivated Burst assignment uses aura 1284947; splash victims alone do not identify failed puzzlers.
- Miasma matches impact hits to the assignment's eight-second duration, with a two-second tolerance. Fully absorbed hits count as participation. Casts without observed impacts remain visible. Nearby deaths are temporal associations, not attribution of the killing blow.
- Droplet damage is allocated between successive completed casts. Blast clusters span at most 100 ms from their first hit, avoiding transitive chains; they cannot measure simultaneous missed-orb counts.
- Coagulations reuse actor and even instance IDs within a pull. Separate death/channel boundaries keep lives distinct. WCL `amount` already excludes overkill; it must not be subtracted again. Pet damage is credited to its owner. One-point residue is excluded.
- Coagulation timing starts with instance-specific evidence; summon-to-first-hit time includes spawn travel time. Of 63 evidence rows, 53 have a death, eight end without a death, one is a summon with no observed instance, and one is an unmatched buff-only actor. On fight 21 at 2:52.765, the Contaminate cast identifies actor 191 but the buff identifies actor 190 with the same instance. The latter is explicitly an unmatched signal, not a confirmed extra add, and has no inferred lifetime.

The mechanics HTTP job was checked against all 11 wipes and matched the independently loaded research streams. Unit coverage includes absorbed soaks, death/wipe cleanup, omitted initial stacks, reused/missing add IDs, pet ownership, overkill, empty casts, and merged-report isolation. The existing frontend contract is reused without component changes. Browser visual verification was unavailable because the computer-use tool reported no available browser.

Final checks: 176 pytest tests and 3 subtests passed, backend compilation passed, and the frontend production build passed. The `ghosts_first_per_set`, `nexus_phase_damage_full`, and `dimensius_add_damage_default` HTTP snapshots differ from the older stored goldens, but all three match fresh results from an isolated, untouched `HEAD` checkout exactly; the drift predates these changes. Existing goldens were not replaced.

The seven-view mechanics report contains 84 pull/mechanic combinations (Aggregate plus 11 pulls), plus 24 Droplet Bars/Waves combinations and 24 Dispel By set/By healer combinations. The Mythic Aggregate HTTP job also completed with all four expected child reports, including Mechanics.

Droplet bar-view validation: all 11 individual pull totals were compared directly with the raw player-targeted pop events. Aggregate totals match 1,528 soaks across 20 players. Tests additionally cover multiple waves, duplicate fight IDs across merged reports, absorbed hits, empty pulls, and per-scope bar scaling. With this addition, 177 tests and 3 subtests pass and the frontend production build passes. The mechanics snapshot adds Bars/Waves keys for every scope alongside the original keys.

### Dispels and intermission resolution

Blighted Blood applications arrive 0.354–2.904 seconds after completed cast 1284483. Thirty casts assign four players, three assign three, and one assigns two. Group by completed cast, with a five-second application fallback when cast evidence is absent; a one-second aura cluster would split legitimate sets. Credit only actual `dispel` events whose `extraAbilityGameID` is 1284471, matching target and aura lifetime. The set view shows targets, dispellers, timestamps, delay tooltips, and applications without observed dispels. The healer bars aggregate only the selected report/pull scope. Mass Dispel counts each debuff removed, rather than treating the cast as one dispel.

Intermission timers start on the first Helical Toxins application (1284590), not either boss's preceding Stasis cast. A successful finish requires all observed applications to have early removals alive, without Cultivated Burst applications. Death, expiry, missing removals, and wipe cleanup retain a failed/incomplete row and its healing but do not contribute to average/fastest clear time. New Stasis/application windows isolate repeated intermissions, so a missing removal cannot be resolved by a later application.

Boss healing uses observed Vitriolic Stasis heal events (1284635), independently bounded by each boss's Stasis buffs (1284588/1284606). Include the final heal when Stasis ends, even when it follows the toxin timer. A 250 ms packet-order tolerance includes the 1 ms late final heal on fight 24 and remains bounded by the next window and pull end. Missing Stasis removals are marked in details and bounded by the 30-second Stasis duration/pull end. Expanded details show healing bars per boss and each player's toxin resolution. All 476 cached healing packets are accounted for exactly once, totaling 337,538,107; no overheal was present in these packets.

The [Wowhead encounter guide](https://www.wowhead.com/guide/midnight/raids/venomous-abyss-entombed-sentinels-boss-strategy-abilities) corroborates the 28-second toxin expiry, four-stack neutralization, and Stasis healing of the weaker boss. Timings and totals above come from the supplied combat log rather than guide estimates.

Validation after these additions: 190 tests plus three subtests pass, backend compilation passes, and the frontend production build passes. Coverage includes staggered and missing casts, explicit dispel attribution, Mass Dispel targets, reapplication boundaries, late exit heals, missing Stasis ends, failed/partial toxin clears, aggregate averages, and merged-report scope isolation.

The live mechanics HTTP result matches the independently cached event analysis for all rows and metrics across 132 selector combinations. The ghost, phase-damage, and add-damage HTTP snapshots also match the prior clean-HEAD comparison snapshots exactly.
