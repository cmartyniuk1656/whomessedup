# Mythic Nymrissa: orb pops during Abyssal Rain

Report: `nymrissa-wavecaller-mythic-mechanics`. Sample: [fCqgJN7QMWA2vFbT](https://www.warcraftlogs.com/reports/fCqgJN7QMWA2vFbT), Mythic encounter 3379, fights 15–19 (five wipes). The query includes every matching pull and can merge multiple reports without mixing their actor/fight IDs.

## Requested timing rule

Flag a player orb pop during **raid damage from Abyssal Rain, including its lingering DoT**, plus **one second before and after**, inclusive. The rule follows the user's clarification; it does not stop when the boss finishes channeling.

Windows use actual player-targeted damage events for `1260843`. Consecutive hits no more than 2.5 seconds apart form one window, allowing jitter around the two-second DoT cadence. The first and last observed hits determine its endpoints. No scripted boss offsets or assumed full DoT duration are substituted. Missing data, deaths and wipe truncation can shorten observed windows. The report explains that being outside a recorded window is not proof of safe timing.

`1313448` non-periodic Frost Orb impacts identify soakers, including immune and fully absorbed impacts. Periodic `tick: true` rows do not represent new pops. Two separate impacts on the same player two milliseconds apart remain two pops. Debuff applications corroborate contacts but are insufficient alone: immune players can trigger raid bursts without gaining the debuff. Aura stacks and refreshes must not be counted again.

`1313450` Frost Burst is raid-wide damage caused by soaking. Its victims are not soakers. `1313456` Shatter represents unattended orbs and receives no individual pop attribution. The large central bubble's `1266340`/`1258154` Pop! is a different mechanic.

## Observed results

| Fight | Rain damage windows | Orb pops | Flagged pops |
| --- | ---: | ---: | ---: |
| 15 | 3 | 17 | 16 |
| 16 | 3 | 17 | 17 |
| 17 | 4 | 17 | 16 |
| 18 | 7 | 54 | 53 |
| 19 | 7 | 46 | 45 |
| Total | 24 | 151 | 147 |

146 flagged pops are inside observed damage windows and one is within the preceding one-second buffer. None fall only in the following buffer. These are timing review flags, not automatic fault scores.

The sample has 601 Frost Orb damage events: 151 initial impacts and 450 periodic ticks. Forty-two initial impacts have immune/miss hit type 0. All 102 observed debuff applications/stack increases have a matching initial impact within 100 ms. All raid Frost Burst hits have an initial orb impact within 150 ms; that proximity validates attribution in this sample but is not used to merge distinct contacts.

## Manifest audit

Four actionable targets: Nymrissa, Bubblefin Frostscale, Bubblefin Shorerunner and Bubblefin Berserker. Twelve player-damage ability IDs are manifested:

| ID | Ability | Classification |
| --- | --- | --- |
| 1260843 | Abyssal Rain | Raid damage / lingering DoT |
| 1313448 | Frost Orb | Intentional soak and DoT; contextual timing |
| 1313450 | Frost Burst | Raid damage; no individual victim blame |
| 1313456 | Shatter | Missed-orb raid damage; no individual victim blame |
| 1257654 | Lingering Frost | Avoidable ground damage |
| 1313393 | Chilling Frost | Targeted DoT |
| 1271458 | Water Jet | Tank frontal; conservative non-avoidable classification |
| 1258677 | Swirling Whirlpools | Avoidable moving hazard |
| 1266340 | Pop! (Central Bubble) | Raid damage / knockback |
| 1258154 | Pop! (Knockback) | Zero-damage knockback |
| 1271380 | Pulsing Tides | Empowered-add raid damage |
| 1265425 | Wild Bite | Avoidable water exposure / shark bleed |

Excluded observed damage IDs: generic Melee (`1`) and player-originated Shadow Word: Death (`32409`, logged as Environment). Player and owned-pet sources are excluded from the audit. Environmental damage is otherwise retained: whirlpools and central-bubble Pop! can have Environment as their source. Shark is retained as the source of Wild Bite, but is not offered as an actionable damage target. Bubble Stalker is an encounter helper, not an actionable add target.

Water Jet can hit non-tanks, but tank participation and clearing ice are expected; a future positional/role analysis should establish blame before adding blanket avoidable scoring. Other unobserved journal abilities are not guessed into this sample manifest. This change registers metadata and the focused mechanics report, without introducing separate damage/death report wrappers.

## Sources and confidence

The [Mythic Trap guide](https://www.mythictrap.com/en/venomous-abyss/nymrissa-wavecaller/mythic) distinguishes player orb soaks from central-bubble bursts and describes the extra Mythic raid damage. Spell records support the [Rain DoT](https://www.wowhead.com/spell=1260843/abyssal-rain), [initial orb contact and subsequent DoT](https://www.wowhead.com/spell=1313448/frost-orb), [unattended-orb Shatter](https://www.wowhead.com/spell=1313456/shatter), [Water Jet](https://www.wowhead.com/spell=1271458/water-jet), and [water-exposure Wild Bite](https://www.wowhead.com/spell=1265425/wild-bite). Attribution and counts above come from the supplied WCL events. Classification confidence is high for orb/Rain spell IDs in this sample; broader encounter coverage should be reviewed against additional kills and strategy variations.

## Implementation and validation

- `services/nymrissa_mechanics.py`: bounded, paginated event fetching and multi-report merge.
- `services/nymrissa_mechanics_orbs.py`: pure per-pull damage-window and contact analysis.
- `services/nymrissa_mechanics_models.py`: spell IDs, timing constants and report vocabulary.
- `services/view_models/nymrissa_mechanics.py`: compact shared tables, player bars, pull selection and expanded timing evidence. The API indexes serialized rows using the existing transport helper.
- `services/manifests/midnight_season_2/nymrissa_wavecaller.py`: audited boss metadata, registered through the season and central manifest registries.
- `app.py`, `services/report_registry.py`, `service.py`: catalog/job integration and public service exports.
- `tests/test_nymrissa_mechanics.py` and `tests/fixtures/nymrissa_orb_rain.json`: exact buffer boundaries, periodic/immune attribution, repeated impacts, source/pull isolation, recorded pull and rendering contracts. The fixture anonymizes players and retains real Rain boundary/tick samples plus every Frost Orb event from fight 15.
- `scripts/capture_regressions.py --case nymrissa_mythic_mechanics`: fresh API smoke test against the supplied report. Also compare `ghosts_first_per_set`, `nexus_phase_damage_full` and `dimensius_add_damage_default` with their baselines.

Validation commands: `.venv/Scripts/python.exe -m compileall -q app.py who_messed_up`; focused pytest for Nymrissa, manifests, existing mechanics and cooldown coverage; `npm run build` in `frontend`; the regression captures above.

Validated locally on 2026-09-22: 96 focused tests passed; compilation and frontend build passed. A fresh WCL API job exactly matched the researched page after row indexing. All three legacy regression snapshots matched their pre-change baselines. SSR/DOM checks exercised expanded evidence, player bars, pull selection, Rain windows and all-pop views. Changes have not been deployed.
