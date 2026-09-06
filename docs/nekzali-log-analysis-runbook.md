# Mythic Nek'zali Warcraft Logs analysis runbook

Version 3, 2026-09-06. This is an iterative raid-review process for Nek'zali, not a generic parse-ranking checklist. It is designed to separate throughput problems from assignment failures and cascading mechanics.

## Output contract

Every review should produce:

- a pull-by-pull table with the first decisive failure, the later cascade, confidence, and one correction;
- a benchmark cohort spanning fast, middle, and similar-duration kills, with at least one similar-item-level control when available;
- Drowned Echo cycle timing, inferred team identity, entrants, role composition, Soul Exhaustion state and remaining duration, damage, and interrupts;
- intermission duration, Jawae handoff time, Pyre soak count, Pyre/downstairs-team overlap, and Vessel damage;
- healing by dangerous event window, not just whole-fight HPS;
- avoidable-damage and first-death patterns;
- a short prioritized next-raid plan with measurable success criteria;
- explicit caveats for missing or ambiguous Warcraft Logs data.

Use a short subsection per pull rather than compressing multiple causal claims into one table cell. Each pull should state:

- **Pyre availability:** who was alive upstairs and who was unavailable downstairs;
- **Pyre attendance:** who actually soaked and, when the parity roster is known, which available assignees missed;
- **Corpses/Vessels:** estimated repossessed-corpse count, number of waves, damage, and immediate deaths;
- **Downstairs failure:** whether the problem was Drowned throughput, Swirling contact, healer coverage, early Exhaustion, wrong-team entry, or a recovery cascade;
- **Correction:** one change aimed at the first controllable failure.

Avoid vague phrases such as “the Swirling sequence collapsed the raid.” State that Swirling is downstairs-only avoidable line damage, name the hit count and affected players when useful, and distinguish the loss of a healer from the line contacts that killed that healer.

Never combine the three downstairs damage sources when assigning cause: Grasping Depths is raid-wide while the Drowned lives, Immortal Coil is baseline realm damage, and Swirling Spirit is a contact-applied stacking DoT. Soul Exhaustion amplifies Soulcoil Well and Immortal Coil according to the encounter tooltip; check its aura at entry, but do not attribute a Swirling event to Exhaustion without evidence of an undocumented interaction. Use successful entrants with zero Swirling ticks as the control proving that Swirling is avoidable.

## Reproduce the snapshot

The repository `.env` supplies `WCL_CLIENT_ID` and `WCL_CLIENT_SECRET`. Never print or commit them.

```powershell
python -m scripts.analyze_nekzali_pulls xK1bZJTLdrVhqHDg `
  --benchmark ah9tCqgG4BHvxbTz:7:world-fastest `
  --benchmark Kmpxk7vcRwbr39fq:15:fast `
  --benchmark dR6jcM732QnLbk9W:43:midrange `
  --benchmark Fg3v27qwmXt8DnNH:9:slower `
  --benchmark RdQGX4gchMDtBHTk:6:near-time `
  --benchmark yL37gwdHnWfvC2kD:12:same-ilvl `
  --output .local/nekzali/analysis.json
```

The output intentionally contains derived metrics rather than a full raw-event dump. `.local` is disposable working data; the reviewed conclusions belong in `docs/analysis/`.

The current `.env` has a non-key/value line that produces a `python-dotenv` parse warning. Authentication still succeeds. Do not “clean up” the file during analysis because it may contain user-managed configuration.

## 1. Establish encounter facts

Read the local boss manifest first. It defines the IDs and which mechanics are avoidable, raid-wide, or assignment-based. Cross-check against current public Mythic guides because strategy context is not fully inferable from damage events.

For Nek'zali, the critical causal chain is:

```text
corpse not burned -> Amani spirit repossesses Vessel -> empowered add pulses Vessel damage
undersized Pyre -> player/healer death -> assignments degrade
wrong/exhausted players enter -> Drowned lives -> Grasp + Immortal continue
continued Grasp -> healing deficit appears -> boss mechanics overlap -> wipe
```

Do not label the final high-damage event as the root cause without reconstructing the chain.

## 2. Select comparison kills

Use two discovery paths:

1. `Encounter.fightRankings(difficulty: 5, metric: speed)` for ranked fast/midrange examples.
2. `reportData.reports(zoneID: 53)` followed by report fight metadata for slower and similar-duration kills that fall outside the ranked result set.

Build a cohort with:

- one fast kill;
- one midrange kill;
- two or more kills within roughly ±60 seconds of the guild's projected kill;
- one control within about two average item levels, if possible;
- unique reports/guilds where possible, excluding duplicate uploads.

Record report code, fight ID, kill time, average item level, region if relevant, and discovery date. Ranking populations change; do not silently reuse a stale cohort forever.

Outlier rule: retain exotic kills as labeled context, but exclude them from medians if they skip a normal phase or do not expose the expected encounter events.

## 3. Fetch and normalize

Collect these streams for every selected fight:

- fight metadata and phase transitions;
- player roster, specs, and inferred roles;
- hostile casts and interrupts;
- buffs/debuffs for realm entry, exit, and Soul Exhaustion;
- completed Soulcoiler's Curse casts and the resulting Soulcoiled recipients;
- damage done to Nek'zali, Restless Amani, Echo of Jawae, and Drowned Echo;
- damage taken for Rite, Corpse Blight, Vessel, Grasp, Immortal Coil, Swirling Spirit, Pyre, Soul Transfer, Latent Cultist, Anguished Echoes, Well, and Barrage;
- deaths and the 15–25 seconds preceding each early death;
- healing tables for the full fight and event windows;
- raid cooldown casts.

Normalize all timestamps to seconds from fight start. Keep absolute WCL timestamps only inside the fetch layer.

## 4. Reconstruct Drowned cycles safely

### What works

- Use Grasping Depths periodic-damage windows as the primary cycle clock.
- Join realm-entry/exit auras by time overlap, not by list position.
- Mark an entrant exhausted if Soul Exhaustion is active at the entry timestamp.
- Record the seconds remaining, then classify the entry as the correct team entering early, the wrong team/substitute, or a later recovery attempt.
- Infer the two intended teams from repeated five-player participation across clean cycles and track roster changes pull by pull.
- Sum Drowned damage and interrupts within the same time window.
- Treat a window as a real kill attempt only when it lasts at least five seconds and includes at least 5M Drowned damage. Keep excluded windows visible for diagnostics.

### What did not work

- Pairing the nth Grasp window with the nth Drowned target stream. Warcraft Logs can omit phased-target data.
- Treating actor `instanceID` as globally unique. Warcraft Logs recycles instance IDs; split a target stream after a meaningful inactivity gap.
- Counting every tiny Grasp cluster as a Drowned kill. Transition artifacts skew medians and invent extra groups.
- Comparing only raw clear time. A slow but clean group can succeed; exhausted entrants and wrong role composition are often more predictive.
- Applying wide grace periods to adjacent Grasp windows. When windows are close, split the gap at its midpoint so realm ticks are not counted in both cycles.
- Describing everyone observed during a long failed Grasp as a simultaneous group. Preserve individual entry timestamps so the review distinguishes the initial team from piecemeal rescue attempts.

Report each cycle as:

| Field | Meaning |
|---|---|
| start/end/duration | Authoritative Grasp window |
| entrants/exits | Players observed in Immortal Coil |
| entered exhausted | Assignment breach |
| role count | Expect four DPS and one healer under the standard plan |
| Drowned damage/share | Whether the intended damage group actually connected |
| interrupts | Coverage of the Drowned's interruptible cast |
| confidence | High when aura, damage, and Grasp agree; lower when a stream is missing |

For a two-team plan, compare the time from realm exit/Soul Exhaustion application to the next same-team entry. If the correct team enters with only a few seconds remaining, that is a cadence problem; if a player from the other team enters with most of the minute remaining, that is an assignment/substitution problem.

A cross-team substitute changes the readiness of **both** rosters: the borrowed player may be unavailable on the next nominal turn, while the player replaced remains clean. After every substitution, recompute each player's expiry for the next two Drowned spawns instead of continuing the alternating team labels mechanically. State whether the substitution was required by a death; if everyone was alive, classify it as an execution/positioning or call issue rather than casualty recovery unless communications prove otherwise.

When a cycle has too many entrants, project the effect onto the very next cycle. Identify whether the extras belong to the next team, record when their new Exhaustion begins, and recalculate the next team's remaining role composition. Borrowing a DPS can reduce throughput; borrowing the next healer can leave several clean DPS with no viable realm healer. Do not describe the later failure as a generic four-player group if only one of those four actually entered.

Quantify whether a **wait-until-clean** call is viable instead of treating immediate entry as mandatory. Measure the remaining Exhaustion on every intended entrant, Grasping Depths raid damage per second during the proposed hold, and the Drowned's active/next Curse completion time. A completed Curse has no recipient when the well is empty, but the first cast after entry must be interrupted immediately. Never drip-feed the group as individual debuffs expire.

Do not invent a universal wait cap. In `xK1bZJTLdrVhqHDg`, the required hold was only 4–8 seconds. A same-item-level successful control proves that a team can wait through about 13 seconds of remaining Exhaustion and enter 19–20 seconds after Grasp starts, provided the raid sustains the extra Grasp damage and the entrants immediately establish interrupt coverage. Use a clean alternate/third team for longer waits when available, but label that as risk management rather than a hard encounter rule.

For each hold, persist seconds from Grasp start to first entry, Grasp damage before first entry, and Grasp DPS during that interval. Report both the target raid's rate and a comparable kill's rate; late-fight tuning and mitigation can produce a broad range. Also record the non-damage costs: delayed Exhaustion application/next-team readiness, shifted Pyre or boss-mechanic overlaps, healing cooldown and mana expenditure, positioning disruption, and the remaining reaction time on the first Curse after entry.

Treat a completed Soulcoiler's Curse as a primary failure: record the completion time, players currently in Immortal Coil, subsequent Soulcoiled applications, and any Rite/death consequences. The cast ejects the active team and leaves the Drowned alive, so later mixed entries are normally rescue symptoms rather than the original failure.

## 5. Analyze the intermission

Measure:

- transition start and phase-two start;
- first and second Jawae active target spans;
- dead time between Jawae target windows;
- every Hungering Pyre's soaker count, total damage, max hit, and deaths;
- Vessel damage clusters and deaths within five seconds;
- distinct hostile Vessel source instances per cluster, as an estimate of how many corpses were repossessed together;
- the inferred odd/even Pyre cohorts and their intersection with each five-player Drowned team;
- corpse-clearing debuff destinations when position data is available;
- Soul Transfer and Latent Cultist hits.

Separate “Jawae DPS was low” from “the raid spent time retargeting/repositioning.” They have different fixes.

Vessel damage is not simply “an add reached the well.” It means an intact Amani corpse was repossessed during Ritual of Awakening and the empowered Amani pulsed raid damage. Report it as evidence of failed corpse burning/repositioning unless the event model changes.

Do not invent a universal minimum Pyre soak count from one report. Derive an empirical floor from the raid's own stable and lethal samples, then label it as raid-specific. Also simulate the written assignments: if a ten-player Pyre cohort contains all five members of one kill team, perfect execution leaves only five assigned soakers whenever that team is downstairs. That is a plan defect, not missed attendance.

For every undersized Pyre, reconstruct the assigned cohort at impact and classify each member as **soaked, dead, downstairs, or alive-but-absent**. Attribute deaths by direct killing ability and timing: distinguish players killed directly by Vessel from players who subsequently died to Grasp or another overlap while depleted. Count opposite-cohort flex soakers separately. This prevents post-Vessel attrition from hiding surviving assigned players who could still have raised the soak above the raid-specific floor.

When an early summary names only the first few deaths, continue the causal timeline through the wipe. For an unfinished Drowned, report: the functional roles lost before entry, each entrant and arrival time, first avoidable contact, completed Curse and recipients, remaining Drowned health, duration and total damage of the terminal Grasp, rescue-group Exhaustion state, and the final split of deaths to Grasp, Immortal Coil, and Swirling. Initial attrition is the setup; the completed cast or failed recovery may be the actual point of no return.

Classify every exhausted entry as **primary cause, setup factor, or recovery symptom**. An exhausted player appearing late in a wipe does not prove that Drowned throughput caused the wipe. Compare clean Drowned kill medians with successful controls, then model the planned team cadence: a kill can be normal by benchmark standards yet incompatible with a two-team, zero-wait rotation. Report both facts explicitly.

For two alternating ten-player Pyre cohorts and five-player Drowned teams, enforce a 3/2 parity split in each kill team. No kill team should intersect either Pyre cohort in more than three players. This guarantees seven scheduled soakers remain upstairs; assign an opposite-cohort flex player whenever eight is the raid-specific target.

## 6. Analyze healing causally

Whole-fight HPS is a screening metric, not a diagnosis. Compare effective HPS and cooldown coverage during:

- each Soulcoil Ignition;
- every real Grasping Depths window;
- Invoke/Rite overlaps;
- Vessel failure clusters;
- the final 30–45 seconds before the first terminal death.

Questions to answer:

1. Was incoming damage comparable to successful controls?
2. Was a major cooldown active before the dangerous event, or only after deaths began?
3. Did the assigned downstairs healer survive and enter?
4. Is apparent low HPS caused by dead healers, out-of-range realms, or lack of cooldown coverage?

Recommend more throughput only after controlling for extra avoidable damage and failed assignments.

## 7. Determine each pull's root cause

Use a causal timeline:

1. Find the first death or unrecoverable mechanic breach.
2. Inspect the preceding 20 seconds.
3. Identify whether it is a cause (bad soak, active Vessel, exhausted entry) or a symptom (Rite tick after the raid is already dead).
4. Follow subsequent assignment and damage consequences.
5. Assign confidence:
   - **High:** cast, aura, damage, and death timing agree.
   - **Medium:** the timeline agrees but a phased stream or position is absent.
   - **Low:** only the final killing event or aggregate table supports it.

Use team/process language. Name a player only when the observation enables specific coaching, and distinguish a repeated pattern from a one-off.

## 8. Evaluate external analysis sources

Lorrgs can provide aggregated composition and cooldown timing for supported bosses. Query its public composition-ranking endpoint by boss slug and optional kill-time range before relying on it. As of 2026-09-05, the Nek'zali endpoint recognized the slug but returned an empty report list, so it added no evidence to this review.

When Lorrgs is populated:

- use it to identify common cooldown timing bands by spec;
- filter to a relevant kill-time range;
- validate recommendations against actual encounter events and the guild roster;
- do not turn “top logs commonly do X” into a universal requirement without a causal reason.

## 9. Review checklist

Before publishing:

- [ ] Every pull has a cause, cascade, confidence, and actionable correction.
- [ ] At least two controls are close to expected kill time.
- [ ] Item-level mismatch is disclosed.
- [ ] Outliers are labeled and excluded where appropriate.
- [ ] Drowned cycles are reconstructed by time overlap, not ordinal index.
- [ ] Exhaustion is checked at entry time.
- [ ] Each exhausted entry is classified as early correct-team, wrong-team/substitution, or recovery cascade.
- [ ] Pyre/Vessel and Jawae handoff are analyzed separately.
- [ ] Pyre cohorts are intersected with the active kill team to calculate guaranteed upstairs coverage.
- [ ] Healing conclusions compare both incoming damage and cooldown timing.
- [ ] No credential, raw token, or private `.env` content is published.
- [ ] Claims based on inference are labeled.
- [ ] Success criteria are measurable in the next report.

## Iteration log

### Version 1 — xK1bZJTLdrVhqHDg

Worked well:

- combining ranked discovery with zone-report discovery found relevant 8:42–9:35 controls without user-supplied sample reports;
- using a same-item-level kill prevented gear from being mistaken for execution;
- cross-checking Grasp, realm auras, exhaustion, target damage, and interrupts exposed rotation contamination;
- event-window HPS prevented a misleading “healers need more HPS” conclusion;
- grouping Vessel and Pyre damage around deaths identified earlier intermission blockers.

### Version 2 — assignment-overlap follow-up

Corrections and additions:

- clarified that a “Vessel burst” is a cluster of periodic pulses from one or more empowered Amani after intact corpses are repossessed, not a one-time corpse explosion;
- capped grace periods between adjacent Grasp windows so the same Immortal Coil tick cannot invent simultaneous entrants in both cycles;
- preserved individual entry timestamps, distinguishing a correct team entering 3–6 seconds early from a wrong-team substitution with 28 seconds remaining;
- intersected inferred Pyre cohorts with kill teams, exposing a five-soaker assignment floor even when every available assigned player soaked.

### Version 3 — Swirling validation

- Added Swirling Spirit aura applications and stack changes to the derived snapshot.
- Verified against successful kills that a complete downstairs group can record zero Swirling ticks.
- Separated unavoidable Immortal Coil damage, Exhaustion-amplified Immortal Coil damage, and contact-applied Swirling Spirit damage.
- Replaced the generic pull-1 “Swirling collapse” description with player-level tick, damage, stack, and Exhaustion evidence.

Needs improvement next iteration:

- add position data to verify corpse-pile placement and unassigned players' distance from the well;
- ingest raid-note or MRT assignment text when available so inferred team/parity membership can be confirmed rather than reconstructed only from events;
- record role counts and confidence directly in the generated JSON rather than deriving them during review;
- add player-level avoidable-hit counts and defensives used during each downstairs window;
- detect duplicate public uploads more robustly than report-code uniqueness;
- revisit Lorrgs once it contains Nek'zali data;
- compare the next raid against this report's explicit success criteria rather than rebuilding every baseline.
