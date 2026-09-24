# Defensive Usage Report

Available for the same nine Midnight Season 2 bosses and Heroic/Mythic difficulties as Cooldown Coverage Report. Supply one or more Warcraft Logs report codes; every matching pull is queried through the existing paginated event-stream service. The report opens at full width.

## Views

- **This pull / Everyone:** an aggregate raid incoming-damage graph above one compact row per participant, with recorded casts, duration windows, personal damage miniatures, a boss ability filter, and all player deaths. Players without casts remain visible. Miniatures share a common scale.
- **This pull / selected player (default):** one row per known or observed defensive, that player's incoming damage, and their deaths with existing five-second recaps. Selecting Everyone restores the aggregate raid graph. The three largest separated health-damage spikes without a tracked personal window are review prompts, not missed-use penalties.
- **Across pulls:** every attempt for that player on a shared axis. Each row retains its own boss casts, deaths and personal-damage curve. Align by pull start or by an exact mechanic occurrence; attempts without that occurrence are explicitly excluded. Timings are never averaged into a synthetic boss schedule. Shorter pulls end visibly on the shared axis. Summary tiles retain usage across all of the player's pulls even when alignment excludes some rows.
- **Cast details:** measured shield absorption and estimated damage prevented by this cooldown, clearly separated. Unsupported estimates explain the missing evidence instead of displaying a zero-value verdict. The compact panel retains duration, readiness time, effective healing/overhealing when present, nearest boss cast, and a Warcraft Logs link. Targeted externals measure the recipient. Calculation methodology and context window totals are omitted from the panel.

## Research and interpretation

The supplied `midnight-12.1-defensives` package is preserved under `who_messed_up/data/defensives/`, including source receipts, schema, original integration guide and icon manifest. Its 69 defensive records cover 40 specializations; the three support/reset spells remain research metadata rather than defensive uses. Artwork is served from `frontend/public/defensives/icons/`.

`consumables.json` adds Healthstone (6262), Silvermoon Health Potion (1234768), Concentrated Silvermoon Health Potion (1295247), and Potent Healing Potion (1262857). The first three were verified against Wowhead spell tooltips and real Warcraft Logs casts/heals; Potent Healing Potion is additionally listed by Lorrgs and its 50% healing effect was verified through Wowhead. Demonic Healthstone (452930) comes from the supplied research and is categorized as a consumable in this UI. Potion variants share one timeline lane while casts retain their exact identity. Inventory, charges and availability are unknown when a use is absent.

Access checks match specialization and selected talent entry **and** node/rank. Missing talent snapshots remain unknown. Baseline/confirmed selected abilities get unused rows, as do the general consumables; observed casts always remain visible. The report does not implement a complete charge/reset/recovery simulator or definitive missed-opportunity score. Candidate aliases in the package are not silently promoted to cast mappings.

Durations use a paired same-source/recipient aura when possible. Otherwise the window uses a nominal research duration, including supported unconditional selected duration modifiers. Dashed borders identify nominal windows. Windows are clipped at pull end or recipient death. Effects without a recorded cast and pre-pull activations are not counted. A recorded cast does not establish whether it was automatic, proc-enabled or cooldown-consuming.

Personal and item casts with WCL's `targetID=-1` are attributed to the caster; external casts with missing recipients remain unknown. Casts on others are not treated as self protection. Raid/group casts are shown separately from personal use. Healing credit uses only that source, recipient and spell in the following seven seconds; other heals and overhealing are not counted as effective output.

Damage graphs default to health-damage `amount` (orange), shields matched to tracked casts (cyan), other shields (grey), and estimated supported cooldown reduction (green), with two-second bins and the actual final-bin width. **Show all mitigation** restores all-source WCL mitigation. Overkill is already separate from `amount`; it participates in the counterfactual hit calculation but is not health damage taken. Per Warcraft Logs' [DamageEvent contract](https://es.classic.warcraftlogs.com/scripting-api-docs/warcraft/interfaces/RpgLogs.DamageEvent.html), `mitigated` includes blocking, armor and damage reductions, but excludes absorbs: never add `blocked` again. Heal absorbs remain separate from incoming damage and shield protection.

### Cooldown attribution

`defensive_attribution.py` supports 20 explicitly mapped all-school reduction spells using the supplied research. It requires a same-source/recipient paired buff application and end; nominal windows are insufficient. Known selected talent changes modify the base percentage. When a relevant build snapshot is absent, or Bloody Fortitude makes the rate health-dependent, the model withholds an estimate. Sentinel starts at the researched 15 stacks and follows recorded stack changes, not a synthetic decay timer. School-restricted, area-dependent, armor-increase, deferred-damage and other unsupported effects remain unvalued. Automatic/pre-pull effects without a tracked cast remain outside this attribution.

For a supported rate `r`, estimated marginal reduction is `(amount + absorbed + overkill) × r / (1-r)`. This models removal of that one cooldown while holding armor, other reductions, and the rest of the hit fixed; it does not claim additional health damage would actually land, since shields and death saves can change the outcome. Each hit is bounded by WCL's recorded mitigation, and missing mitigation amounts are not invented. A 70k post-reduction impact at 30% reduction therefore implies 30k prevented by that multiplier, not all of the hit's baseline mitigation. The estimate is not a direct combat-log measurement and is not a score of the whole ability's benefit.

Overlaps matter: per-cast figures remove only that cast, so they are **not additive**. The graph removes the product of the supported active multipliers once, with the same logged upper bound. Identical buffs from multiple sources do not multiply with themselves. External casts contribute to the recipient's graph; Everyone sums recipient graphs once. Hover/readout labels identify the contributing abilities and casters, including received externals that are not on the recipient's own cast lanes. Unvalued immunity, avoidance, health, healing amplification and death-save effects can still be valuable.

The default automatic scale prevents isolated extreme hits from flattening the graph. With at least ten nonzero bins, if the peak exceeds twice the 95th percentile, the display ceiling becomes 125% of that percentile. White overflow chevrons mark clipped bins; hover/readout values and cast totals remain unchanged. The label shows both the display ceiling and actual peak. **Full range** restores the uncapped linear scale. Across-pull rows and Everyone's personal miniatures compute one shared scale across their compared rows, preserving comparability. Pressure shading is capped to the same display scale.

The `immunities` stream queries `type = "miss" AND missType = "immune"`. This matters because the damage-only filter omits immune misses even though the API returns them as damage-shaped events. They are normalized internally to immune observations and shown as violet markers/counts; their prevented damage is unknown. Do not infer immunity from a gap or a zero-amount fully absorbed hit. See [WCL expression documentation](https://www.warcraftlogs.com/help/pins).

Absorption credited to a specific shield requires the same spell, caster and recipient in the healing `absorbed` stream during that cast's window. Credit stops at the next same-spell cast on that recipient to avoid counting recast output twice when durations are nominal. This is a subset of total absorbed damage, not an additional contribution. Candidate spell aliases remain unverified; armor/passive/external mitigation and overlapping windows cannot be assigned wholesale to one defensive.

Player identity is report code plus actor ID. This prevents accidental merging of namesakes and keeps different reports' identities separate. Within a report, all of a player's attempts remain selectable, including specialization changes.


## Structure and verification

- `services/defensive_catalog.py`: research adapter, access predicates and nominal duration metadata.
- `services/defensive_usage.py`: stream orchestration, participant timelines, aura windows and measured cast context. Re-exported through `service.py`.
- `services/defensive_attribution.py`: evidence-gated cooldown reduction estimates and matched shielding, with separate marginal cast and joint graph calculations.
- `services/defensive_damage.py`: recorded protection totals and personal/raid damage bins, without estimating unknown immunity amounts or attributing all mitigation to one cast.
- `services/defensive_reference.py`: legacy reference helpers, no longer called by the report.
- `services/view_models/defensive_usage.py`: typed `defensive_timeline` contract; table and healer timeline contracts remain separate.
- `frontend/src/components/v2/defensives/`: report selection, pull/aggregate tracks, stacked damage graph, cast drawer and comparison. Boss filters, shading and death recap components are shared with coverage; the healer pressure graph remains unchanged.
- `frontend/src/utils/defensiveUsage.js`: pure aggregation, alignment, personal-use and reference-denominator helpers.

Run `.venv/Scripts/python.exe -m pytest -q`, `npm run test:defensives`, `npm run test:coverage`, and `npm run build` (npm commands from `frontend`). Focused ESLint covers the changed UI and tests. New snapshot cases are `defensive_usage_sentinels_mythic` and `defensive_usage_nymrissa_mythic`; they disable changing external ranking samples for reproducible snapshots. Legacy ghosts, phase-damage and add-damage snapshots are also checked. The render fixture contains two real Sentinels attempts with bounded death/reference samples.

First-draft validation: 285 backend tests passed, including three subtests; both report interaction suites, focused ESLint and the production build passed. Live validation covered 11 Sentinels pulls (1,335 uses, 184 consumables) and 14 Nymrissa pulls (2,450 uses, 279 consumables). The three legacy snapshots matched their saved baselines. Chrome checks covered full-width default, player/pull selection, mechanic alignment, personal damage and the potion healing drawer. The drawer uses a body portal so transformed report surfaces cannot move it outside the viewport. A real potion cast with `targetID=-1` was verified against its 394,427-point self heal.

Personal protection update: 290 backend tests and three subtests passed, plus defensive/healer interaction suites, focused ESLint and build. Both live report snapshots were refreshed, and the three legacy snapshots still match. Tests cover absorb/block/overkill separation, immune observations, external recipients, short observed windows, shield recasts, personal/Everyone graphs and overflow scaling with unchanged exact values. Chrome confirmed the 7:11 Chocolate pull now shows a roughly 296k/s readable scale with its 4M/s outlier explicitly marked, and the Prismatic Barrier drawer separates 291,151 absorbed in the window from 265,925 directly matched to the barrier.

Cooldown attribution update: 298 backend tests and three subtests passed, along with defensive interaction tests, focused ESLint and build. Tests cover baseline exclusion, talent-dependent rates, Sentinel stacks, nominal/unknown windows, non-additive overlaps, same-buff replacement, recipient targeting, logged upper bounds and shield depletion hits. Both 25-pull live datasets were refreshed with cache version 5; per-player estimates stay within logged mitigation, matched shielding stays within total shielding, and raid bins reconcile with player bins. Legacy snapshots remain unchanged. Chrome verified Sentinel's 782,117 estimate, named contributing cooldowns, and the default view with baseline mitigation excluded.

### Graph keys

`DamageLegend` sits directly below the single-pull damage graph. Across pulls uses one shared legend at the top of the table, covering outcomes across all displayed pulls. It distinguishes measured shielding from estimated cooldown reduction and explains immunity and clipped peaks only when present. Cast colours and duration markers are separate, collapsed `TimelineLegend` help beside the lanes.

## Estimated readiness

`services/defensive_readiness.py` resolves specialization base timers and selected static cooldown/charge modifiers. Estimated readiness is shown by default with dashed recovery lines and clickable diamonds in individual, Everyone and across-pull tracks. A multi-charge diamond means a charge replenishes, not that the button was previously unavailable. Charges recharge sequentially, explicitly assuming full charges at pull start. There are no pre-first-cast availability or missed-use claims.

A later recorded reuse that contradicts the pending estimate invalidates that estimate and restarts the pool from the observed use. Shared replacement cooldowns use one pool per caster. Lines stop at pull end or the caster's next death; diamonds are not shown after death. Cooldowns are not reset by death. Marker/cast tooltips explain the timing basis; the inspector shows only a compact ready-again or charge-return time.

Unknown talent snapshots, unsupported dynamic recovery/reset effects, uncertain free/automatic activations, unvalidated mixed modifier stacking, Alter Time activation/return semantics, Holy Armaments alternation and consumable inventory/shared cooldowns do not receive readiness markers. Target lockouts, resources and suitability remain distinct from estimated cooldown recovery. These limitations are explicit in timing tooltips and report interpretation notes.

### Talent identity correction

The supplied research's `entry_id` values use trait-definition identifiers, whereas WCL combatant snapshots contain trait-node-entry identifiers. `defensive_catalog.selected_rank` now also matches the pinned `talent-entry-map.json`, requiring the entry, node, spell and research definition to agree. This fixes access, selected duration modifiers and damage-reduction modifiers as well as readiness. It never identifies a talent from node ID alone. The original research is preserved.

The map is extracted by `scripts/build_defensive_talent_map.py --source <trait_data.inc>` from the same [SimulationCraft 12.1.0.69875 export](https://github.com/simulationcraft/simc/blob/849a7bef306cc46d137106e372b95fdb0fdeb061/engine/dbc/generated/trait_data.inc) used by healer coverage. The output pins provenance and the source hash. No runtime talent database request is needed. Cache version 6 invalidates earlier defensive report calculations.

Readiness validation: 304 backend tests and three subtests passed; defensive UI interactions, focused ESLint and the frontend build passed. Refreshed all 25 pulls across both reports: 808 Sentinels and 1,597 Nymrissa estimates, including 206 and 372 charge replenishments; 3 and 11 contradicted predictions were withdrawn. Damage attribution remains within logged bounds and raid bins reconcile with player bins. Ghost, phase-damage and add-damage snapshots are unchanged. Chrome verified the clickable Sentinel diamond at 1:06.317 with Righteous Protector explaining its 60-second timer.

The defensive cast drawer omits methodology, evaluated-hit counts, the redundant contribution heading and the always-full contribution bar. Approximate values retain a compact approximation symbol; unsupported prevention is unavailable, not zero.

## Lorrgs comparison removed

The report no longer renders the Lorrgs comparison, its mechanic/occurrence controls, or the request-form opt-in. The service no longer fetches Lorrgs references, including for old callers passing `include_reference=True`; the legacy argument and empty `references` response field remain for compatibility. Cache version 7 prevents reuse of comparison-bearing report payloads. Across-pull alignment to the raid's own recorded mechanics remains available. 

Boss ability icon filters are shared across This pull and Across pulls. Selected spells persist when changing mode, player or pull. Across-pull icons count recorded casts in the displayed attempts, and All/None operate on visibility without changing mechanic alignment or actual cast timings. Hidden alignment mechanics still supply the alignment anchor.

Everyone player visibility: checked player lanes stay together on the common time axis. Unchecking a player moves them to the compact Hidden players section below all enabled lanes, where they can be re-enabled. Show all players and Hide all players provide quick comparison setup. Choices use report/actor identity and persist across pulls and individual inspection; players newly encountered default to shown. The top damage graph and death strip retain full raid context, while personal miniature scaling uses only enabled players. `DefensivePlayerVisibility` holds these controls and labels. UI regression checks cover two-mage comparison, re-enabling, persistence, all-hidden recovery and unchanged raid damage.


## Player health overlay

The default-off Player health toggle follows the user between This pull and Across pulls. A red line uses a separate, fixed 0-100% axis with labels on the right. Everyone keeps raid damage above and puts each enabled player's health in their own lane. Across pulls retains one shared legend and aligns health with the same actual mechanic offset as casts and damage.

`services/defensive_health.py` reads WCL health/max-health resource snapshots from the existing damage, healing and tracked-cast streams (`include_resources=True`). It uses `resourceActor` to attribute snapshots to source or target, accounts for changing maximum health, and retains first/minimum/maximum/last observations per 250ms bucket. Constant plateaus are compressed without losing their edges. Recorded deaths supply 0%; missing snapshots, gaps longer than five seconds, and returns from zero break the line. No initial full health or health after the final snapshot is invented. The time inspector reads the displayed line by interpolation only within connected observations. Missing historical payloads show no health line. Cache version 8 refreshes data for this feature.

WCL resource field reference: https://www.warcraftlogs.com/help/pins (Resources Fields). Health remains independent of two-second damage bins and adaptive spike clipping. Backend tests cover ownership, changing max HP, short dips, deaths, resurrections and missing data; UI checks cover toggling, independent axes, two-player comparison and across-pull persistence.


### Chart layer filters

The graph legend now provides checkboxes for health, damage taken, matched shields, other shields, reduction, immune hits and clipped-peak markers when those outcomes are present. The muted health stroke is 1.4px at 60% opacity. The timeline checkbox row has been removed; casts, durations, readiness, deaths and pressure shading remain visible. Existing boss icon selections and individual player visibility remain available.

`config/defensiveChartLayers.js` defines shared defaults; `utils/defensiveChartLayers.js` filters presentation data without mutating evidence. Visibility lives in the report parent and persists across player, pull and view changes. Hidden damage layers are removed before stacking and scaling, while health retains its fixed percentage axis. All-mitigation mode uses a separate all-shields toggle and preserves the default view's shield choices. Recorded counts and inspector values remain intact. Across pulls still renders just one shared filter legend. UI regression checks cover restacking, re-enabling, cross-view persistence and removal of the timeline filter row.

## Sharing and rendering performance

[Share Report](report-sharing.md) restores player/pull selection, Across pulls alignment, hidden players, boss filters, chart layers, scale, zoom, horizontal position, inspected time and open details.

`DefensiveTimeReadout` owns cursor updates so moving across a graph does not rebuild every player's SVG. `useDefensivePullData` prepares damage, scales, potion lanes, pressure shading and cast lists once per relevant data/filter change. Memoized tracks and stable callbacks prevent opening an inspector from rebuilding the timeline. Across-pulls row geometry and damage series are reused; numeric tooltips share one `Intl.NumberFormat` instance.

The September 24 optimization benchmark used the recorded 11-pull Sentinels page (290,365 health samples), React's development Profiler and JSDOM. Forty cursor updates per view gave these median render times:

| Interaction | Before | After |
| --- | ---: | ---: |
| Individual player cursor | 6.24 ms | 0.45 ms |
| Everyone cursor | 90.49 ms | 0.60 ms |
| Everyone cursor with health enabled | 89.53 ms | 0.70 ms |
| Open Across pulls with health enabled | 297.11 ms | 198.28 ms |

These measure local React rendering, not browser paint or Warcraft Logs/network latency. Backend replay of two recorded pulls took a median 0.47 seconds before changes; backend calculations and returned evidence were left unchanged. The existing bounded event-stream fetch pool and response compression remain in use.

To repeat the render benchmark: `cd frontend` then `node scripts/benchmark-defensives.mjs <saved-report-page.json>`. Without a path it uses the smaller committed fixture. Run `npm run test:defensives`, `npm run test:coverage`, `npm run test:sharing` and `npm run build` for behavior/build validation.
