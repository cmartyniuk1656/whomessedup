# Mythic Nek'zali progression review — xK1bZJTLdrVhqHDg

Analyzed 2026-09-05. This review covers all eight Mythic pulls in the report, compares them with six independently discovered kills, and uses the repository encounter manifest plus public encounter guides to interpret the log events.

## Executive diagnosis

The raid has enough throughput to kill this boss. Pulls 5 and 8 reached 4.55% and 4.90% at roughly the duration of a successful same-item-level kill. The strongest evidence points to two different progression blockers:

1. **Pulls 2, 3, 6, and 7 are primarily intermission execution losses.** Failed corpse cleanup produced 20.8–30.9M Vessel of Awakening damage, often immediately followed by multiple deaths. Undersized Hungering Pyre soaks and Swirling Spirit hits compound the problem.
2. **Pulls 5 and 8 are late-fight downstairs-rotation failures.** Clean Drowned Echo cycles are not generally slow: the raid's median was 30.0s on pull 5 and 28.0s on pull 8, versus 27.5s for the successful cohort and 34.0s for a 9:23 kill. However, with only two teams, 28–35-second kills leave just 51–57 seconds between receiving Soul Exhaustion and the next same-team entry during the compressed late cadence. The failures begin when players enter a few seconds before expiry or the wrong team answers the call.

The proposed explanation—slow Echo kills leaving the downstairs debuff active too long—is **mechanically true but not evidence of abnormally low Drowned throughput**. Faster kills start the one-minute Soul Exhaustion clock earlier, but the raid's 28–30-second medians are close to the successful cohort's 27.5 seconds and faster than the 9:23 kill's 34 seconds. They are only too slow for a two-team plan that assumes immediate, never-exhausted entry during the late roughly 40-second spawn cadence. At the problematic entries players needed another 0–10 seconds; measured from Grasp onset, the returning team did not become fully clean for roughly 12–14 seconds. The same-item-level control handled this by waiting. The primary strategy fix is an explicit hold, a third team, and per-player assignment discipline; burst is useful insurance, not the sole answer.

### Did Soul Exhaustion cause the wipes?

Soul Exhaustion does not prevent entry; it makes Soulcoil Well and Immortal Coil damage four times normal. Across the eight pulls it was a primary factor in two wipes, a recovery symptom in two, and not material in four:

| Pull | Exhaustion evidence | Role in the wipe |
|---|---|---|
| 1 | Two slightly early entrants on an earlier cycle; that Drowned still died. Final group was clean. | Not causal; fatal Pyre, missed Curse, and Swirling drove the wipe. |
| 2 | No exhausted entries. | Not causal; Vessel/corpse failure. |
| 3 | No exhausted entries. | Not causal; Vessel attrition and final Pyre. |
| 4 | Denrukhan entered a failed rescue with 33.5 seconds remaining. | Symptom; clean players failed to enter and the first Curse had already completed. |
| 5 | Terminal Team 2 entered 3–6 seconds early and died rapidly to Immortal Coil; Team 1 rescue entrants had 3–10 seconds remaining. | Primary factor. This is the clearest debuff-driven wipe. |
| 6 | Three mixed rescue entrants had 1–3.6 seconds remaining. | Symptom/amplifier; Huntâbow's Swirling death and the missed Curse had already stranded the Drowned. |
| 7 | No exhausted entries. | Not causal; Vessel/corpse failure. |
| 8 | Hildifonz made a wrong-team entry with 28 seconds remaining; Team 1 then repeated 0–4.4 seconds early. On the terminal cycle four entered 2–6 seconds early. | Primary rotation/setup factor, compounded by a missed terminal Curse. |

The concise conclusion is: **the raid was not generally unable to kill Drowned Echoes fast enough.** Pulls 5 and 8 exposed an under-specified two-team strategy; pulls 4 and 6 became exhaustion problems only after assignment, Swirling, or interrupt failures forced rescues.

Healing throughput is not the global constraint. Pull 8 averaged 1.359M HPS, compared with 1.329M for the same-item-level 9:34 kill and 1.320M for the 9:23 kill. The raid is instead asking healers to cover substantially more late Grasping Depths and Immortal Coil damage after the rotation breaks. A proactive cooldown on the terminal Grasp will help, but preventing the overlap is higher leverage.

## Comparison cohort

The public speed ranking supplied the fast and midrange examples. Slower kills were discovered through Warcraft Logs' zone-report index because encounter rankings only expose the ranked tail, not arbitrary kill times.

| Label | Kill | Raid ilvl | Intermission | Real Drowned cycles | Median clear | Exhausted entries | Vessel damage |
|---|---:|---:|---:|---:|---:|---:|---:|
| [World-fastest outlier](https://www.warcraftlogs.com/reports/ah9tCqgG4BHvxbTz#fight=7) | 4:51 | 317.35 | n/a | 2 | 28.0s | 0 | 0 |
| [Fast](https://www.warcraftlogs.com/reports/Kmpxk7vcRwbr39fq#fight=15) | 6:31 | 319.05 | 2:14 | 4 | 22.5s | 0 | 0 |
| [Midrange](https://www.warcraftlogs.com/reports/dR6jcM732QnLbk9W#fight=43) | 7:33 | 316.15 | 2:15 | 4 | 38.0s | 0 | 0 |
| [Slower](https://www.warcraftlogs.com/reports/Fg3v27qwmXt8DnNH#fight=9) | 8:42 | 317.80 | 2:56 | 7 | 27.0s | 5 | 14.9M |
| [Near-time](https://www.warcraftlogs.com/reports/RdQGX4gchMDtBHTk#fight=6) | 9:23 | 317.85 | 3:00 | 7 | 34.0s | 0 | 6.8M |
| [Same-ilvl](https://www.warcraftlogs.com/reports/yL37gwdHnWfvC2kD#fight=12) | 9:35 | 315.50 | 3:12 | 8 | 27.5s | 1 | 6.3M |
| **Guild pull 5** | 9:32 | 315.45 | 3:07 | 7 | 30.0s | 11 | 0 |
| **Guild pull 8** | 9:36 | 315.45 | 3:27 | 7 | 28.0s | 10 | 8.4M |

“Real Drowned cycle” means a Grasping Depths window with at least 5M damage to a Drowned Echo. Warcraft Logs emits short transition clusters and sometimes omits phased-target streams; treating every cluster as a kill would distort the comparison.

The 4:51 log skips the normal intermission/Echo-of-Jawae sequence and is retained only as an outlier. It is not used as the strategic baseline. The most useful controls are the 9:23 and 9:35 kills.

## Pull-by-pull review

Pull numbers below map to fight IDs 10–17 in [the guild report](https://www.warcraftlogs.com/reports/xK1bZJTLdrVhqHDg).

Each pull now separates assignment capacity from actual participation. “Missed corpses” below is the estimated number of distinct Vessel source instances that were repossessed; it is more actionable than damage alone.

### Pull 1 / fight 10 — 7:24, 27.58% (high confidence)

- **Pyre availability:** The fatal Pyre at 4:08.9 overlapped a downstairs group of Chocolate, Deimortus, Inferniö, Pumpy, Taisuwu, and the extra entrant Yoseki. All 20 players were alive, so 14 remained upstairs.
- **Pyre attendance:** Only Athenä, Huntâbow, and Krous soaked; Huntâbow and Krous died. Downstairs overlap contributed, but cannot fully explain a three-person soak: even if all six downstairs players belonged to the scheduled ten-player parity cohort, at least four assigned soakers were available. Under the inferred parity membership, six were available and Crassberry, Fyxxie, and Scootoot were the likely missing assigned soakers. Confirm those three against the raid note.
- **Corpses/Vessels:** Two missed corpses were repossessed at 3:49–3:54, producing 15.0M Vessel damage. This occurred before the fatal Pyre and increased the healing burden.
- **Downstairs failure:** The final Grasp began at 6:16. Soulcoiler's Curse completed at 6:44.7 after the initial group missed its interrupt. Hipsóppel, Owneege, and Taisuwu were ejected and received Soulcoiled at 6:52.2; all three subsequently died as the debuff ended. A mixed rescue group then entered. Between 7:03 and 7:20, Chocolate, Deimortus, Denrukhan, Inferniö, and Krous took 28 direct Swirling Spirit ticks for 1.92M and all five died with Swirling as the logged killing ability. None of those five had Soul Exhaustion active when entering this Grasp, so this damage was not the 300%-amplified baseline Immortal Coil tick. The rescue also lacked a stable healer because Taisuwu was lost to the Curse sequence and Denrukhan entered late and died to Swirling.
- **Correction:** Protect the Pyre count despite the active downstairs team, burn both corpses, and do not improvise a mixed rescue team. Downstairs players should stop casts to avoid Swirling lines.

### Pull 2 / fight 11 — 4:40, 45.71% (high confidence)

- **Pyre availability/attendance:** The first Pyre had 10 soakers. The second occurred while the five-person Team 1 was downstairs; 15 players remained upstairs, but only five soaked and Taisuwu died. Downstairs overlap contributed, but there were additional upstairs non-participants.
- **Corpses/Vessels:** Four missed corpses were repossessed in two waves of two, producing 26.1M damage. The second wave killed 10 players at 4:12–4:17.
- **Downstairs failure:** Huntâbow died during the contemporaneous Grasp after the healer loss; the subsequent Vessel wave ended the pull.
- **Correction:** Fix both the parity/downstairs overlap and corpse ownership. Do not begin the next soak with intact bodies or an unfilled flex-soak requirement.

### Pull 3 / fight 12 — 6:36, 47.39% (high confidence)

- **Pyre availability/attendance:** Soak counts were 9, 8, 9, 7, and 5. The final hit landed at 6:19.5. Using the inferred first/third/fifth-Pyre cohort, six of ten assigned soakers were already dead: Pilgrimm, Owneege, and Deimortus died directly to Vessel; Denrukhan and Chocolate died to continuing Grasp during/after that cascade; and Hildifonz had died earlier to Slithering Flame. Four assigned soakers remained alive—Hipsóppel, Monkorith, Skelli, and Vodnar—but only Hipsóppel and Monkorith soaked. Athenä, Crassberry, and Taisuwu flexed from the opposite cohort to produce the five-person soak. Vodnar remained out, received Slithering Flame, and died at 6:22.4; Skelli was alive and had been clear of Soul Exhaustion since 6:01.1. Pumpy was also active again and received Slithering Flame, making a potential eighth emergency soaker if not required for corpse duty. Therefore the low count was primarily post-Vessel attrition, but two surviving scheduled soakers also failed to enter or were retained for another assignment. If both had soaked, the count would have reached seven. The five-person hit killed Crassberry, Hipsóppel, and Taisuwu.
- **Corpses/Vessels:** Four missed corpses were repossessed in two waves of two, producing 30.9M damage. The second wave killed eight players at 6:00–6:04.
- **Downstairs failure:** Krous died to Swirling Spirit around 5:05. The second Jawae never finished after the Vessel deaths.
- **Correction:** Assign second-wave corpse burners explicitly. After mass attrition, cancel optional flame-runner roles and call every living scheduled soaker plus named flex players until the raid confirms at least seven. Prioritize Swirling avoidance over finishing a cast.

### Pull 4 / fight 13 — 5:12, 46.83% (medium confidence)

- **Pyre availability/attendance:** The three Pyres had 9, 8, and 10 soakers with no direct Pyre deaths. Pyre coverage was not the root failure.
- **Corpses/Vessels:** One missed corpse was repossessed, producing 9.0M damage. It was recoverable by itself.
- **Downstairs/intermission failure:** Four-player throughput was not the problem: the opening four-player group killed its Drowned in 27.6 seconds. At 3:53, that same four-player core entered with Krous and Taisuwu added, creating a six-player group. All six exited and received Soul Exhaustion at 4:27.5. The next Grasp began at 4:28.0, so borrowing Krous and Taisuwu—the next group's healer—left Huntâbow, Crassberry, Pilgrimm, and Pumpy as four clean DPS with no clean assigned healer. Only Huntâbow actually entered at 4:35.6 and dealt 1.20M to the Drowned; the other three clean players did not enter. Soulcoiler's Curse completed at 4:44.7 with no interrupt, ejecting Huntâbow and subsequently applying Soulcoiled. Denrukhan attempted a rescue at 4:53.9 with 33.5 seconds of Exhaustion remaining, but a second uninterrupted Curse completed at 4:55.7 and ejected/coiled Denrukhan. A third Curse completed at 5:06.7 while the Drowned still had about 8.09M health. Pumpy died to the continuing Grasp at 5:11.1, and the second Jawae remained alive when the pull ended.
- **Correction:** Treat this as next-team starvation plus a missed entry/call and missed interrupts, not insufficient four-player damage. Do not enlarge one group with members of the immediately following group, especially its healer. If a group needs a fifth, use a named backup who does not break the next rotation. On the failed spawn, the clean residual players needed either to enter together with a clean backup healer or make an explicit hold/reassignment call; sending Huntâbow alone and then an exhausted healer could not recover it.

### Pull 5 / fight 14 — 9:32, 4.55% (high confidence)

- **Pyre availability/attendance:** Soak counts were 10, 9, 8, and 5. On the fourth Pyre, all five remaining members of the scheduled parity cohort soaked while the other five were downstairs; Scootoot died. This was a structural assignment collision, not missed attendance.
- **Corpses/Vessels:** Zero missed corpses and zero Vessel damage—the night's cleanest corpse execution.
- **Downstairs failure:** Huntâbow entered a correct Team 2 turn with 3.2s of Exhaustion left. On the terminal cycle, Team 2 entered 3–6s early and failed; Team 1 then attempted a rescue with 3–10s remaining.
- **Correction:** Split kill teams across Pyre parity cohorts, display the Exhaustion countdown, and wait the few seconds rather than sending an exhausted rescue team.

### Pull 6 / fight 15 — 5:36, 46.50% (high confidence)

- **Pyre availability/attendance:** Soak counts were 10, 6, and 9. The six-person soak survived, but it left little margin while Team 1 was downstairs.
- **Corpses/Vessels:** Three missed corpses were repossessed as a two-add wave and a one-add wave, producing 20.8M damage. The first wave at 3:56.6–4:02.1 dealt 13.9M and killed Inferniö and Taisuwu; Pumpy died to the concurrent Grasp. Taisuwu was subsequently resurrected, cast Rewind at 4:17.0, and was active for the later Pyre/rescue, so this was not a permanent three-player loss. The later single Vessel dealt another 6.9M at 5:06.3–5:10.3 but caused no direct deaths.
- **Downstairs failure:** The terminal Grasp began at 4:25.6. Huntâbow, Krous, and Crassberry entered; the resurrected Taisuwu remained upstairs, while Skelli arrived as the replacement healer only as the first Curse was completing. Huntâbow contacted Swirling immediately and died at 4:38.9. No one interrupted the Curse begun at 4:34.2; it completed at 4:44.2 and ejected/coiled Krous, Crassberry, and Skelli. A second Curse completed at 4:55.2 while the realm was effectively empty. That initial group dealt only 1.17M, leaving the Drowned at about 87.4% health. Krous and Crassberry died at 5:09.3 and 5:13.2 after the Soulcoiled sequence.
- **Terminal cascade:** Grasp remained active for 65.0 seconds and dealt 34.1M raid damage in this final window. A seven-player mixed rescue entered at 5:16.0–5:23.3. Chocolate, Hipsóppel, and Denrukhan entered 1.0–3.6 seconds before Exhaustion expired; Chocolate and Denrukhan died to Immortal Coil almost immediately, while Hipsóppel died to Swirling. The clean rescue entrants also died to Immortal Coil as healing collapsed. Upstairs, eight players died directly to the continuing Grasp. From 5:17.7 through the end, 15 additional death events completed the wipe: eight to Grasp, six to Immortal Coil, and one to Swirling. The rescue recorded one Curse interrupt but no meaningful Drowned damage. No major raid-healing cooldown is logged after the terminal Grasp began.
- **Correction:** Eliminate the initial two-corpse reanimation, but also give the replacement group an explicit healer and interrupt owner. If Huntâbow dies, Krous or Crassberry must still stop the active Curse. After a completed Curse, do not drip-feed an exhausted mixed rescue: either wait the remaining few seconds and send a clean group together or call a clean third team, with a raid cooldown covering Grasp.

### Pull 7 / fight 16 — 4:51, 47.40% (high confidence)

- **Pyre availability/attendance:** Both Pyres were survived with 10 and 6 soakers. Pyre was not the direct killer.
- **Corpses/Vessels:** Four missed corpses were repossessed: first a three-add wave, then one more. They produced 25.5M damage; the first wave killed five players and the second killed four.
- **Downstairs failure:** Denrukhan died to Swirling after the first Vessel wave. The remaining realm entries were recovery attempts, not a functional kill team.
- **Correction:** This is primarily a corpse-burning wipe. Prevent the three-corpse wave before evaluating later downstairs throughput.

### Pull 8 / fight 17 — 9:36, 4.90% (high confidence)

- **Pyre availability/attendance:** All four Pyres were healthy at 9, 9, 10, and 11 soakers. Their timing overlapped the opposite kill team, so the parity collision did not occur.
- **Corpses/Vessels:** One missed corpse was repossessed, producing 8.4M damage; the raid survived it.
- **How Team 1 repeated:** This was not caused by deaths—the first death of the pull did not occur until 8:25.2. On the 5:20 Grasp, the normal Team 1 core of Chocolate, Denrukhan, Pilgrimm, and Vodnar entered, but the alive/clean Owneege stayed out. Hildifonz came from Team 2 instead, entering at 5:34.8 with 28.0 seconds of Exhaustion remaining. That unnecessary or accidental substitution desynchronized both rosters: Owneege remained clean, while Hildifonz refreshed his Exhaustion through 6:58.1.
- **6:47 repeat:** Four Team 2 members—Huntâbow, Krous, Pumpy, and healer Taisuwu—had been clean since 6:02.8; only Hildifonz still had about 11 seconds remaining when Grasp began. Team 1 was in the opposite state: only Owneege was clean, while Chocolate, Denrukhan, Vodnar, and Pilgrimm were exhausted until 6:58.1. Nevertheless Team 1 entered at 6:53.7–6:58.0. Chocolate had 4.4 seconds remaining, Denrukhan 3.5, Vodnar 1.2, and Pilgrimm 0.1; Owneege was clean. They survived and killed the Drowned, but their exit reapplied Exhaustion at 7:20.7.
- **Terminal consequence:** Team 2 then completed the 7:27 cycle cleanly and received Exhaustion at 8:07.4, immediately before the terminal 8:07 Grasp. The erroneous 6:47 Team 1 turn meant both teams were now unavailable: Team 2 had nearly a full minute remaining and Team 1 still had 13.6 seconds. Vodnar, Chocolate, Owneege, and Denrukhan entered 2.1–6.0 seconds early; Pilgrimm joined clean later. The initial group was caught by an uninterrupted Curse sequence, later entries were piecemeal, and the Drowned took only 3.76M.
- **Correction:** Track readiness per player, not only by the last announced team label. At 6:47 the clean solution was to hold roughly 11 seconds and send Team 2 together, send its four clean members as a three-DPS/one-healer group, or use a clean DPS substitute for Hildifonz. Any of those choices preserves a fully clean Team 1 for the terminal cycle. Start the terminal healing cooldown before the first death if recovery is still required.

## Downstairs rotation: the highest-leverage fix

### What the logs show

### Inferred kill teams

Warcraft Logs does not expose the raid-note assignment, so these are inferred from repeated five-player Immortal Coil participation. Confidence is high where the same five repeat and lower on pull 4, where the groups drifted.

| Pulls | Kill team 1 | Kill team 2 | Notes |
|---|---|---|---|
| 1 | Denrukhan; Hipsóppel; Krous; Owneege; Pilgrimm | Taisuwu; Chocolate; Deimortus; Inferniö; Pumpy | Team 2 gained Yoseki on its intermission turn; later groups became mixed. |
| 2 | Denrukhan; Hipsóppel; Krous; Owneege; Pilgrimm | Taisuwu; Chocolate; Crassberry; Inferniö; Pumpy | Both opening groups are clear. |
| 3 | Denrukhan; Chocolate; Hipsóppel; Owneege; Pilgrimm | Taisuwu; Crassberry; Huntâbow; Krous; Pumpy | This becomes the stable roster. |
| 4 | Denrukhan; Chocolate; Hipsóppel; Owneege; **fifth unclear** | Taisuwu; Crassberry; Huntâbow; Krous; Pumpy; **Pilgrimm also entered** | Four/six split indicates assignment drift or an unlogged/missed entrant. |
| 5–7 | Denrukhan; Chocolate; Hipsóppel; Owneege; Pilgrimm | Taisuwu; Crassberry; Huntâbow; Krous; Pumpy | Stable four-DPS/one-healer teams. |
| 8 | Denrukhan; Chocolate; Owneege; Pilgrimm; Vodnar | Taisuwu; Hildifonz; Huntâbow; Krous; Pumpy | Vodnar replaces Hipsóppel; Hildifonz replaces Crassberry. |

On pull 8, the clean groups are therefore:

- **Team A:** Chocolate, Owneege, Pilgrimm, Vodnar, Denrukhan.
- **Team B:** Hildifonz, Huntâbow, Krous, Pumpy, Taisuwu.

Their early clear times are 24–32 seconds, which is adequate for this kill-time band. The successful 9:23 control actually has a slower 34.0-second median while recording no exhausted entries on its real cycles.

The pull-8 sequence then changes:

| Grasp start | Duration | Entrants | Rotation state |
|---:|---:|---|---|
| 0:43 | 24.0s | Team A | Clean |
| 1:55 | 24.0s | Team B | Clean |
| 3:52 | 28.0s | Team A | Clean |
| 4:27 | 30.0s | Team B | Clean |
| 5:20 | 32.0s | Team A with Hildifonz replacing Owneege | Wrong-team substitution; Hildifonz has ~28s left |
| 6:47 | 28.0s | Team A again | Wrong team in the 1/2 alternation; four have 0–4.4s left |
| 7:27 | 35.0s | Team B | Clean |
| 8:07 | 89.0s to wipe | Team A, then piecemeal rescue entries | Correct turn, but four enter 0–6s early and fail; Drowned survives |

Pull 5 is more purely a cadence problem. At 6:21, one Team 2 player enters 3.2s before expiry. The next Team 1 cycle is clean. At the terminal cycle, Team 2's five players enter with roughly 3–6s left; after they fail, Team 1 tries to rescue with roughly 3–10s left. Those are players following the intended alternating turn slightly too early, followed by a recovery cascade—not ten people simultaneously deciding to use the wrong squad.

### Confusion versus timing

- **Timing/cadence:** pull 5's 6:21 and terminal Team 2 entries; pull 8's terminal Team 1 entry. These are the designated teams, but the one-minute debuff has a few seconds remaining because late Drowned spawns are about 40 seconds apart and clean kills take 28–35 seconds.
- **Assignment/call error:** pull 8 at 5:20 uses Hildifonz from Team 2 as a Team 1 substitute while he has ~28 seconds left. At 6:47 Team 1 goes twice in the A/B sequence even though Team 2 is clean and available.
- **Recovery cascade:** after the first exhausted team fails, members of the other team enter piecemeal while also exhausted. These later entries are symptoms, not the original error.

### Swirling Spirit versus baseline realm damage

These must be kept separate in the review:

- **Immortal Coil (1308227)** is the unavoidable periodic damage from being downstairs.
- **Swirling Spirit (1300239)** is a separate five-second DoT applied on contact with a moving spirit line; repeated contacts stack it.
- **Soul Exhaustion (1300235)** increases Soulcoil Well and Immortal Coil damage by 300%. Its tooltip does not list Swirling Spirit as amplified.

It is possible to take zero Swirling damage downstairs. In the same-item-level successful kill, two complete five-player Drowned groups recorded zero Swirling ticks; the slower 8:42 control also had two complete groups with zero. Therefore a Swirling damage event is evidence of line contact, not an automatic realm tick.

For pull 1's terminal cluster:

| Player | Swirling ticks | Damage | Largest tick | Exhausted at entry? |
|---|---:|---:|---:|---|
| Denrukhan | 6 | 551k | 121k | No |
| Chocolate | 6 | 497k | 116k | No |
| Deimortus | 7 | 393k | 104k | No |
| Inferniö | 6 | 328k | 57k | No |
| Krous | 3 | 149k | 65k | No |

The raw aura stream confirms repeated contact: Deimortus reached two stacks at 7:08, Denrukhan reached two at 7:11, and Chocolate reached two at 7:16. Inferniö and Krous each received a one-stack application. None had Soul Exhaustion during this interval: Chocolate, Inferniö, Krous, and Denrukhan had their previous applications removed at 6:34.3, roughly 29 seconds before the first late Swirling contact, while Deimortus's expired at 5:17.5. No new Soul Exhaustion application occurred between 7:03 and 7:20. Healing coverage deteriorated during the failed rescue, but the avoidable contacts—not Soul Exhaustion—generated these specific Swirling events.

### Soulcoiler's Curse completion

Soulcoiler's Curse is the Drowned Echo's required interrupt. If it completes, it coils every player currently in the well, ejects them from Immortal Coil, and applies Soulcoiled. Soulcoiled compels the affected players back toward the Soulcoil Well; a player who reaches it is sacrificed and triggers Soulcoil Rite. The cast does not simply add another damage tick: it removes the active kill group, leaves the Drowned alive so Grasping Depths continues, and can convert each affected player into an additional Rite/death failure.

On pull 1, the completed 6:44.7 cast affected Hipsóppel, Owneege, and Taisuwu. Their Soulcoiled applications appear at 6:52.2, and they died at 7:04.3, 7:07.0, and 7:00.5 respectively. The later mixed rescue group and its Swirling deaths were therefore consequences of a missed Curse interrupt as well as the earlier Pyre losses.

### Throughput sanity check

Pull 8 and the same-ilvl control lasted almost exactly the same time. Pull 8 dealt 663.0M boss damage versus the kill's 697.1M, leaving about 34.2M boss health. It dealt the same 198.9M to the two Jawae, 68.8M versus 74.4M to Drowned Echoes, and 264.5M versus 255.8M to Amani. The total priority-target difference is only about 31M and is dominated by the unfinished terminal Drowned/boss. There is no large, unexplained gear-scale damage gap.

### Recommended assignment model

The current two-team plan can work, but it needs an explicit **wait-until-clean** rule. In these logs the dangerous turns need only about 4–8 seconds of patience. A visible Soul Exhaustion countdown is more reliable than judging readiness from the spawn. If the raid cannot safely hold Grasp for that wait, a third four-DPS/one-healer team removes the cadence collision and matches the common Mythic strategy.

#### How long can the team wait?

There is no separate failure caused merely by leaving the well empty. While the Drowned remains alive, however, **Grasping Depths continues to damage and pull the whole raid**, and the Drowned continues beginning Soulcoiler's Curse casts. A Curse that completes while the well is empty has nobody to eject or Soulcoil; once players enter, the current cast must be interrupted immediately.

Pull 8's terminal cycle shows the trade clearly. Grasp began at 8:07.1. The first Curse completed at 8:16.3, while Vodnar, Chocolate, and Owneege had entered with roughly 4–6 seconds of Exhaustion remaining; all three were subsequently Soulcoiled. The latest of the intended early entrants would have become clean at about 8:20.7. Had the squad remained upstairs until then, the first Curse would have resolved into an empty well and the next was not due to complete until 8:27.3, leaving about 6.6 seconds to enter and interrupt. Instead, Pilgrimm entered clean at 8:26.4 but the second cast was not stopped; Pilgrimm was then Soulcoiled as well. Waiting is therefore safe only when paired with a rehearsed **enter together, kick immediately** call.

The observed cost of holding from 8:07.1 through 8:21.0 was 2.77M Grasping Depths damage over 13.9 seconds, about 199k raid damage per second. Relative to the squad's actual early entries, waiting the remaining 4–6 seconds would have added roughly 0.8–1.2M raid damage. That is meaningful healing pressure, but it is preferable to sending several players into Immortal Coil with its damage multiplied by Soul Exhaustion and risking the entire kill group.

The successful controls provide direct evidence that groups do wait. In the 9:35 same-item-level kill, the terminal Grasp began at 8:03.7 while all five members of the returning team remained exhausted until 8:16.7. The entire team stayed upstairs: they entered together at 8:22.4–8:23.9, 5.7–7.3 seconds after the debuffs disappeared and 18.7–20.2 seconds after Grasp began. They interrupted at 8:30.0 and 8:38.7, killed the Drowned at 8:41.7, and subsequently killed the boss. The same kill has an earlier partial example: one player entered 1.8 seconds early, while the other four waited until 6.3–7.5 seconds after their debuffs expired.

That control uses exactly two stable five-player squads across all eight real Drowned cycles, alternating without substitutions. Team A is Pawwonni, Stabeezak, Criticus, Erevor, and healer Laraen. Team B is Cavemann, Økagi, Aiyuria, Gitt, and healer Greatgrays. The short empty Grasp clusters in the raw event stream are transitions, not a hidden third team. They enter normally when already clean and hold only when the returning squad's debuffs overlap the next spawn.

The 8:42 kill also delayed its final returning team for 8.6–11.4 seconds after Grasp began, apparently trying to reach expiry, but all five entered 0.4–3.2 seconds early. It succeeded despite the brief amplified exposure; it is evidence of a hold call, but not of a perfectly clean wait. The other four controls either did not reuse a team while Exhaustion was relevant or had already-cleared debuffs, so they cannot answer the waiting question.

#### Damage budget and secondary cost

Pull 8's returning group became fully clean 13.581 seconds after the terminal Grasp began. The exact Grasping Depths damage through that expiry was **2.768M**, averaging about 138k per player across 20. The first entrant actually went down at 7.584 seconds, after 1.144M Grasp damage; holding from that point until everyone was clean would therefore have added **1.624M**.

The 9:35 same-item-level control became clean 12.944 seconds after its terminal Grasp began and took **3.274M** Grasp damage through expiry, averaging about 164k per player. It deliberately waited another 5.767 seconds to assemble/enter, reaching **5.892M total Grasp damage before the first entry**. Its Drowned then died after roughly 24 seconds of active damage. A practical healing budget is therefore about **2.8–3.3M Grasp damage to wait only for expiry**, or as much as **5.9M before entry** when the group also uses a post-expiry formation buffer. Concurrent encounter damage is additional; absorbs are included in these incoming-damage figures.

Extra Grasp damage is the main direct penalty, but it is not the only operational downside:

- Drowned death and realm exit occur later, so Soul Exhaustion is applied later. With only two teams, that can make the next same-team turn tight again; a third team breaks this feedback loop.
- The continuing pull disrupts positioning and can make adds, Pyre assignments, Essence Rend, or phase-two mechanics harder. Delaying entry may improve the current Pyre's upstairs headcount while moving the downstairs absence into a later Pyre.
- The hold consumes healer mana and often a raid cooldown that may otherwise be needed for Invoke or another late overlap. The team must enter healthy enough to survive Immortal Coil.
- A Curse may already be casting when the group enters. Empty-well completions have no recipient, but entering late in a cast creates a short interrupt reaction window.
- The five players can continue damaging upstairs targets during the hold, so the wait is not automatically five-player downtime. Nevertheless, the Drowned kill and return to the boss happen later, which can matter near the boss's energy enrage.

Use this decision rule for this roster and tuning:

- **Up to roughly 15 seconds remaining:** a wait-until-clean call is demonstrably viable, provided Grasp is assigned a healing cooldown. The same-item-level control successfully held through about 13 seconds remaining.
- **Longer waits:** prefer a clean alternate/third team, but treat this as a healing-budget decision rather than a hard encounter timer. Measure current raid health, cooldowns, and phase-two rot before committing.
- **Curse already casting:** note its completion time. It may finish harmlessly while the well is empty, but after the squad enters, its current or next cast becomes the first priority.

Operational rules:

- Only the called group positions to be pulled into the well. Everyone else pre-positions away and uses movement/knockback tools as planned.
- The call includes the group name, whether its healer is alive, and the longest remaining debuff: “Team 1 next, six seconds—hold.”
- A dead or exhausted assignee triggers a named backup, never a free-for-all.
- Track the Drowned's health. If it remains alive past the expected 30–35-second window, call targeted burst, personal defensives, and the recovery healing cooldown. Do not send the other exhausted team to rescue it.
- Preserve interrupts. Pull 8's terminal Drowned records only one late interrupt while previous cycles commonly have two.

## Intermission and corpse control

### What “Vessel burst” means

When a Restless Amani dies, its body remains as a **Vessel of Awakening**. Hungering Pyre, Slithering Flame, or Cremation must burn that body. During Ritual of Awakening, an Amani spirit can repossess an intact corpse; that empowered Amani then pulses Vessel of Awakening damage for roughly five seconds. Therefore the damage is evidence of **an unburned corpse that was successfully repossessed**, not merely the passive existence of a corpse and not the normal energy event from an add reaching the well.

“Burst” in the first version of this review meant a time-cluster of those one-second raid-wide pulses, not a corpse exploding once. Counting distinct hostile source instances inside each cluster gives the following estimate:

| Pull | Empowered Amani waves | Vessel damage | Consequence |
|---|---|---:|---|
| 1 | 2 | 15.0M | Heavy pressure, no immediate logged Vessel deaths |
| 2 | 2, then 2 | 26.1M | Second wave killed 10 players |
| 3 | 2, then 2 | 30.9M | Second wave killed 8 players |
| 4 | 1 | 9.0M | Recoverable by itself, but added intermission pressure |
| 5 | 0 | 0 | Corpse cleanup succeeded |
| 6 | 2, then 1 | 20.8M | First wave killed Inferniö and Taisuwu |
| 7 | 3, then 1 | 25.5M | First wave killed 5; second killed 4 |
| 8 | 1 | 8.4M | Survived |

This makes the corpse target concrete: zero remaining corpses is ideal, one reanimation is survivable in the deepest pull, and two or more simultaneous empowered Amani repeatedly become lethal.

The encounter makes Hungering Pyre both a split soak and a corpse-burning tool. Four pulls incurred more than 20M Vessel damage, while the clean pull 5 incurred none. Successful controls ranged from 0 to 14.9M, with the two similar-time kills at 6.3M and 6.8M. This is the clearest improvement opportunity before optimizing boss damage.

### Pyre parity versus kill-team overlap

The soak pattern reveals two alternating ten-player cohorts. On pull 5, the inferred first/third-Pyre cohort was Chocolate, Deimortus, Denrukhan, Hildifonz, Hipsóppel, Monkorith, Owneege, Pilgrimm, Skelli, and Vodnar. The complementary second/fourth cohort was Athenä, Crassberry, Fyxxie, Huntâbow, Inferniö, Krous, Pumpy, Scootoot, Taisuwu, and Yoseki. The exact “odd/even” label should be checked against the raid note, but the membership inference is strong.

This exposes a structural problem: **all five members of kill team 1 are in the first/third cohort, and all five members of kill team 2 are in the second/fourth cohort.** On pull 5's fourth Pyre at 5:23, kill team 2 was downstairs. The five remaining players from the scheduled Pyre cohort—Athenä, Fyxxie, Inferniö, Scootoot, and Yoseki—all soaked. Nobody from that cohort missed the soak, yet it was only a five-player hit and Scootoot died. Perfect execution of the written overlap still produced an unsafe soak for this raid.

Pull 8 did not suffer the same collision because its Pyre timing overlapped the opposite kill team; its four soaks had 9, 9, 10, and 11 players. That makes the current arrangement timing-dependent rather than robust.

Successful controls had minimum Pyre counts of 7 for the same-item-level kill, 5 for two higher-item-level slow kills, and 8–13 for the faster controls. Your raid sometimes survived six or seven but lost players on all observed three- and five-person samples. Use **seven as a hard planning floor and eight as the preferred target** at the current gear/health level.

Two viable redesigns:

1. **Keep alternating cohorts:** distribute each five-player kill team 2/3 across the two Pyre cohorts. A downstairs team then removes at most three assigned soakers, leaving seven. Add one or two named opposite-cohort flex soakers to reach eight whenever the caller sees a collision.
2. **Use an upstairs rule:** every healthy upstairs player soaks except two or three named mobile Slithering Flame corpse burners. This automatically adapts to the active downstairs team, but requires disciplined flame assignments.

The first option is materially safer than the current arrangement. Because five cannot divide evenly, make one kill team three odd/two even and the other two odd/three even. The invariant is: **no kill team may contain more than three players from either Pyre cohort.** Then:

| Active downstairs team | Odd cohort left upstairs | Even cohort left upstairs |
|---|---:|---:|
| Three odd / two even | 7 | 8 |
| Two odd / three even | 8 | 7 |

For pull 8, the Pyre participation suggests Hildifonz had moved to the even cohort and Inferniö to the odd cohort; verify that swap against the raid frames. Under that inferred pull-8 roster, one layout-safe example would be:

- **Team 1:** Denrukhan, Chocolate, Owneege, Huntâbow, Krous — three odd and two even under the inferred parity roster.
- **Team 2:** Taisuwu, Hildifonz, Pumpy, Pilgrimm, Vodnar — two odd and three even.

That example is intended to demonstrate parity safety, not to claim the best possible burst or interrupt balance. The DPS pairs can be swapped differently as long as each team remains four DPS plus one healer and satisfies the 3/2 split. When the active team removes three members of the scheduled Pyre cohort, one named flex player from the opposite cohort raises the soak from seven to the preferred eight.

Recommended runbook for the room:

1. Mark corpse piles and assign each Slithering Flame/Cremation carrier a pile before the pull.
2. Move the active Jawae so Hungering Pyre covers a planned pile without making the soak unsafe.
3. Use an empirical target of **8+ healthy soakers**, with seven as the hard floor. This is raid-specific, not a universal spell minimum.
4. Call both the active kill team and projected soak count: “Team 2 down; odd soak has eight.” Activate flex soakers before impact if the count is lower.
5. Confirm “corpses clear” before moving the raid's attention to the next Jawae or Drowned cycle.

Pull 8's Jawae intermission took 3:27, 15 seconds longer than the same-ilvl kill and 27–31 seconds longer than the other similar-time controls. Most of that difference is a 12.5-second gap between the two Jawae target windows versus 1.7 seconds in the same-ilvl kill. Tighten the retarget/reposition handoff after the first Jawae dies; the active kill times themselves differ by only about five seconds.

## Healing plan

The log does not support adding a healer or demanding universally higher HPS. Pull 8 already matches or exceeds similar-time successful totals. The correct change is event-based cooldown placement:

- Assign a major raid cooldown to every expected late Grasping Depths/Invoke overlap, especially the terminal group.
- On pull 8, terminal Grasp begins at 8:07 and the first death is at 8:25. Ascendance appears at about 8:29, after the tank is dead. Move that coverage to the start of the Grasp or the first dangerous overlap.
- Protect the assigned downstairs healer before entry and define an external/rescue if that healer is dead from the preceding Pyre.
- Do not measure success by raw HPS alone. Pull 8 took 142.9M Grasping Depths damage versus 98.8M in the same-ilvl kill, and 44.5M Immortal Coil versus 37.2M. The extra demand is produced by the broken cycle.

Suggested first-pass event plan:

| Event | Coverage goal |
|---|---|
| Intermission Ignition / high Rite stacks | One planned raid cooldown; preserve one for Pyre recovery |
| First phase-two Grasp + Invoke | Medium raid cooldown plus downstairs personals |
| Penultimate planned Grasp | Major throughput cooldown |
| Terminal Grasp around 8:05–8:35 | Strongest remaining raid cooldown at onset; tank external ready |
| Drowned exceeds 35s | Recovery call: burst, healthstones/personals, second cooldown; stop pretending it is a normal cycle |

## Personal execution themes

These are coaching patterns, not blame assignments:

- **Swirling Spirit:** repeated fatal or near-fatal line contacts appear across the night. Fatal examples include Krous (pulls 1 and 3), Huntâbow (pull 6), Denrukhan (pull 7), and multiple players in pull 1's final collapse. Downstairs groups should prioritize avoiding lines over finishing a cast.
- **Hungering Pyre attendance:** the raid's successful-looking soaks usually include 8–12 players; 3- and 5-player soaks repeatedly kill people, including healers. This needs positional ownership rather than individual improvisation.
- **Soul Transfer / Latent Cultist:** pull 4 includes a Soul Transfer hit and late pulls contain avoidable Latent damage. Set a single movement direction and delay returning until the blast/manifestation is resolved.
- **Possession Barrage:** pull 8's late barrage hits 16 players for about 6.3M during the collapse. Keep the tank far from the boss and the raid behind the boss even while recovering a Drowned failure.

## Next raid priorities

In order:

1. Restore strict Team 1/Team 2 alternation and add an expiry countdown/wait rule; late returning teams may need roughly 12–14 seconds from Grasp onset before everyone is clean. Use a third team if the raid cannot safely hold that interval.
2. Rehearse corpse-pile ownership and require the “corpses clear” call.
3. Break the one-to-one mapping between kill teams and Pyre parity groups, with at least seven guaranteed and eight preferred upstairs soakers.
4. Bind healing cooldowns to late Grasp/Invoke events, with the terminal cooldown starting before deaths.
5. Only then rebalance burst inside a group. If a clean group repeatedly exceeds 35 seconds, move one on-demand-burst DPS into it while preserving four DPS plus one healer.

### Success criteria for the next log

- No entrant has Soul Exhaustion at a real Drowned cycle.
- Every real cycle has exactly the assigned four DPS and one healer, except a documented backup substitution.
- Median Drowned duration at or below 32 seconds; no cycle above 38 seconds.
- No Vessel sequence over 10M total damage; stretch goal zero.
- No Pyre with fewer than seven healthy soakers; target eight or more.
- Both Jawae target windows separated by under five seconds.
- Terminal Grasp has a raid cooldown active before the first lethal damage cluster.

## Sources and limitations

- Local encounter model: `who_messed_up/services/manifests/midnight_season_2/nek_zali_the_soulcoiler.py`.
- Strategy cross-checks: [Mythic Trap](https://www.mythictrap.com/en/venomous-abyss/nekzali-the-soulcoiler) and [Icy Veins](https://www.icy-veins.com/wow/nekzali-raid-guide/).
- Benchmark source: Warcraft Logs GraphQL API using the repository credentials. No client secret is included in this output.
- Lorrgs was evaluated, but its Nek'zali composition endpoint returned no reports as of the analysis date. It was not used to manufacture cooldown conclusions.

Warcraft Logs can omit phased target streams and reuse actor instance IDs. Grasping Depths windows, realm entry/exit auras, damage-to-target, and Soul Exhaustion were therefore cross-checked rather than joined by position. Death “killing ability” can also be misleading during simultaneous wipe damage; the review prioritizes the first causal mechanic cluster over the last event attached to a death.
