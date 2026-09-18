# Vashnik mechanics UI

The primary table should answer who was involved and what happened. Timing sits beneath the set name; secondary totals and the full event sequence live in expanded details. No mechanic classification or inference confidence changes with the presentation.

| Subreport | Primary row | Expanded details |
| --- | --- | --- |
| Totems | Set/time/fountains, outcome bar | Counts and collapsible wave/fountain context; individual evidence in Totem details |
| Wave carriers | Wave/time, complete roster, associated/late clears | Release count, first release, each carrier's timing |
| Froth | Set/time, carriers, splash/wave hits | Early releases, splash-recipient bars, assignment and impact evidence |
| Exploding Infection | Set/time, infected players, dispel outcome bar | Explicit/unmatched counts, healer bars, target/timing/stack evidence |
| Stygian Infection | Set/time, infected players, resolution bar | Supported clear time, absorb healing, burst hits, healer bars and individual outcomes |
| Living Venom | Add/time, outcome, health/shield damage | Observed lifetime, raid damage, close explosions, player bars and lifecycle evidence |
| Bile | Set/time, participants, soak hits/missed bursts | Missed-soak damage, participation bars and impact timeline |

Unresolved outcomes use gray, not failure red. Received splash bars identify victims, not its cause. Bile hit counts and missed bursts do not form a part-to-whole bar: they measure different things. Totem credit remains group-associated or explicitly inferred.

## Reusable presentation

- `CompactTableModel` opts into container-width tables with at most three primary columns here. At narrow widths, cells reflow as labeled cards. Sort controls remain available.
- `heading` cells combine a row label with secondary timing/context; `metric_list` cells combine a few labeled values. Numeric values remain available alongside shortened display values.
- `RelativeBar` puts the name and value above a proportional fill. It has no minimum fill width, so zero and small values remain honest. It is used both in compact table cells and contribution grids.
- `CompactRowDetailsModel` shows selected metrics and contributions first. Native disclosure controls preserve complete event groups without rendering an expanded wall of text by default.
- `compact_mechanics_page` takes encounter-specific configuration and an optional row decorator. Existing report shapes and presentation remain unchanged unless they opt in.

Regression coverage checks column budgets, preserved evidence, uncertainty categories, time formatting, scoped recipient bars, and unchanged legacy report payloads. Server-rendered checks cover all six views, missing/zero values, and the removal of fixed minimum widths. Browser viewport verification requires a connected browser and was unavailable in this session.
