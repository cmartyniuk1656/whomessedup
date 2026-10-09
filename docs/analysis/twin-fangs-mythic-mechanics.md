# Mythic Twin Fangs mechanics

Verified 2026-10-08 using `docs/boss-manifest-scrape-playbook.md` and
[Mythic Trap](https://www.mythictrap.com/en/venomous-abyss/the-twin-fangs/mythic).
The user identified the critical distinction: touching a wave applies Eternal
Venom immediately, while wave damage requires remaining in it for one second.

## Evidence

Primary report: [XAYPC7qxRHkQVjT4](https://www.warcraftlogs.com/reports/XAYPC7qxRHkQVjT4),
Mythic encounter 3421, fights 28–33 (five wipes and one kill).

- 390 direct Caustic Globule impacts, spell **1289201**, including seven immune
  impacts. These identify pickups, even when immunity prevents a venom stack.
- 62 Stir the Depths **applydebuff** events, spell **1292807**, paired with 62
  removals. **54 contacts had no damage event during the recorded aura lifetime.**
  Damage-event counting would miss most wave contacts in this sample.
- 879,408,176 effective player/pet damage across 287 observed add lifetimes for
  **Spawn of Vexhul** and **Broodling of Ithraz**. Pet damage is credited to owners;
  absorbed damage and overkill are excluded. Broodlings can disappear after
  interruption, so missing death events are not labeled kills or assigned a
  guessed lifetime duration.
- 218 explicit successful interrupts of **Visceral Burst (1308385)**. Every
  interrupt includes `targetID=243` and a `targetInstance`, so individual
  Broodlings are distinguishable despite sharing a name. Instance numbers are
  scoped to the pull and do not indicate positions or assigned raid markers.
- 356 removals of **Barbed Bulwark (1303378)** from the **Barbed Bulwark** actor
  (NPC 269194). The shield actor is separate from the environment-sourced
  Caustic Globule pickup impact. All removals follow an observed control aura
  on the same instance: 353 have one attributable player, and three have
  competing players (two on fight 30, one on fight 33). The 353 single-player
  matches occur 0–47ms after the CC application.

Shield credit requires the shield application to have been logged, a nonzero
target instance, positive remaining absorb on removal, and an applied verified
control aura in the preceding 100ms. Duplicate shield applications are absorb
updates, not new shields. One area CC can receive credit for multiple shields.
Multiple qualifying auras from one player award that player one shield; competing
players award neither and appear in the evidence table. Pet/totem owners receive
credit. Unsupported removals remain visible without being called successful CCs.
This is timing-based attribution, not a direct player-owned shield-break event.

`SHIELD_CC_ABILITIES` lists control aura IDs verified in this sample, including
stuns, fears, disorients, and incapacitations. Unknown control spells are not
guessed from nearby casts or damage. Extend this list from new log evidence;
unsupported removals provide a visible audit trail. Slow, damage, and vulnerability
auras on Bulwarks are intentionally excluded. Interrupt attribution does not
depend on a spell allowlist: any explicit successful interrupt against a configured
add counts; known ability labels improve the evidence text.

Secondary report `yCHTdpBrV19zDLvg`, fights 31–53, supplies 23 Mythic wipes and
confirms both add names and the same pickup/debuff spell IDs. The existing
Heroic sample `6CqvafhpjRc9nrAX` was used only to cross-check the common spell IDs.

The report deliberately excludes boss damage, non-player damage contributions,
unsoaked Globule ruptures (**1290338**), raid-wide Stir the Depths pulses
(**1292806**), and generic Eternal Venom applications. These cannot substitute
for an individual pickup or wave contact. Wave damage ticks, aura refreshes,
stack changes, and removals do not create extra contact rows. All observations
are scoped to the selected fight and report before aggregation.

## Structure and UI

`the_twin_fangs_mechanics.py` fetches narrowly filtered streams through the shared
event-stream pool. `the_twin_fangs_mechanics_events.py` calculates add lifetimes
and individual contacts; `the_twin_fangs_mechanics_control.py` handles successful
interrupts and conservative CC/shield attribution. Vocabulary lives in `the_twin_fangs_mechanics_models.py`;
the view-model module configures shared compact mechanics components.

The Mythic tile offers **Add damage**, **Orb pickups**, **Wave contacts**,
**Orb shield CCs**, and **Add interrupts**,
each with player bars and expandable evidence rows, aggregate/pull selection,
class colors, and existing CSV/report controls. Counts describe observed actions;
they do not infer intent or reconstruct total venom stacks. Heroic report logic
and manifests are unchanged.

## Regression coverage

- `tests/fixtures/twin_fangs_mythic_observed.json` retains fight 28's complete
  pickup/debuff streams and damage/lifecycle evidence for the first observed
  instance of each add type. Its snapshot expects 30 pickups, eight contacts,
  and 13,190,990 damage across those two sampled add instances.
- Synthetic tests cover damage-free wave contacts, re-entry, immune/absorbed
  pickups, non-player exclusions, pet attribution, instance separation,
  post-death packets, empty pulls, and reused fight IDs across reports.
- `tests/fixtures/twin_fangs_mythic_control.json` preserves shield application,
  removal, verified control auras, and interrupt evidence from all six pulls.
  Its regression expects 353 attributed breaks, three ambiguous removals, and
  218 successful interrupts. Additional tests exclude failed casts, wrong
  instances, non-control debuffs, depleted shields, unsupported players, and
  out-of-window CCs; they verify area CC and pet/totem attribution.
- The mechanics cache version is 2 so earlier three-subreport results cannot
  hide the new CC and interrupt views.
- `scripts/capture_regressions.py --case twin_fangs_mythic_mechanics` captures
  the complete primary report through the registered API job.
- The ghosts, Nexus phase-damage, and Dimensius add-damage captures matched the
  existing `regression_snapshots_current` baselines. Older files in
  `regression_snapshots` predate unrelated existing changes.
- The frontend production build and rendering of all six bar/evidence views
  passed against the primary log's generated page.
- The control extension passes 117 focused tests (plus three subtests), the
  frontend build, and rendering of all four new bar/evidence views through the
  indexed API response. A fresh API capture preserves the original three
  subreport totals and reproduces the control fixture's 353/3/218 results.

The complete pre-deployment backend suite passes 341 tests plus three subtests.
Deployment and production verification are recorded in the VPS operations runbook.
