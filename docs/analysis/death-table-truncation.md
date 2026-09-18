# Death-table truncation: X6FGCJm3pqjQMNdv

The selected Mythic Vashnik fights are 21, 22, 23, 25, 26, 27, 30, 35, 37, 41, 43, 45, 47, 50, 52, 55, and 57. These are 17 boss pulls; the intervening report fights include trash and short non-encounter segments.

The combined WCL `Deaths` table contains exactly 200 entries, ending six deaths into pull 11 (fight 43). The paginated `Deaths` event stream contains 324 deaths. There is no continuation field in the table response, and the WCL `Report.table` GraphQL arguments expose no limit or pagination parameter.

| Pull | Fight | Old table | Raw events / corrected report |
| --- | --- | --- | --- |
| 1–10 | 21–41, selected boss fights | 194 | 194 |
| 11 | 43 | 6 | 20 |
| 12 | 45 | 0 | 22 |
| 13 | 47 | 0 | 21 |
| 14 | 50 | 0 | 20 |
| 15 | 52 | 0 | 20 |
| 16 | 55 | 0 | 20 |
| 17 | 57 | 0 | 7 |
| Total | | 200 | 324 |

`fetch_complete_death_table` now splits requests reaching 200 entries into disjoint groups of fights and retries recursively. Full fight time bounds preserve the damage recap and killing-blow metadata. Unsaturated reports retain the single-request path; exactly 200 entries are conservatively rechecked. A saturated single fight raises an explicit completeness error instead of silently truncating. Death/healer cutoffs are applied only after complete entries have been collected.

The fix is shared by all boss death reports. Existing saved/cached jobs are immutable results of their earlier run; force a fresh report after updating the backend. The regression case `vashnik_mythic_deaths_long_session` reproduces the affected session. Research captures are under `.local/death-audit/`.
