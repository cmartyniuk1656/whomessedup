# Boss Manifest Scrape Playbook

Use this when extrapolating a new boss manifest from a Warcraft Logs report. The goal is not to perfectly reverse-engineer the encounter on the first pass; it is to create a useful manifest that is explicit, easy to correct, and safe for death and avoidable-damage reports.

## Start With Local Patterns

Before adding a manifest, read an existing one in the same tier, such as:

- `who_messed_up/services/manifests/midnight_season_1/vorasius.py`
- `who_messed_up/services/manifests/midnight_season_1/imperator_averzian.py`

Match the existing schema:

- `BossManifest` for boss ID, boss name, difficulty, targets, and abilities.
- `EncounterTargetConfig` for target metadata.
- `BossAbilityMetadata` for spell name, game ID, description, URL, tags, and `avoidable=True` when appropriate.

Register new manifests through:

- `who_messed_up/services/manifests/midnight_season_1/__init__.py`
- `who_messed_up/services/boss_manifests.py`
- `who_messed_up/service.py` if public re-export is useful.

## Pulling Report Data

For a new report, first identify the encounter pulls and IDs:

```powershell
@'
import os
import requests
from who_messed_up.env import load_env
from who_messed_up.api import fetch_fights, get_token_from_client

load_env()
token = get_token_from_client(os.getenv("WCL_CLIENT_ID"), os.getenv("WCL_CLIENT_SECRET"))
s = requests.Session()
fights, actor_names, actor_classes, actor_owners = fetch_fights(s, token, "REPORT_CODE")
for fight in fights:
    print(fight.id, fight.encounter_id, fight.name, fight.difficulty, fight.kill, round((fight.end - fight.start) / 1000, 1))
'@ | python -
```

Then aggregate `DamageTaken` events for player targets only. Important details:

- WCL event rows may only contain `abilityGameID`; use report `masterData.abilities` to resolve names.
- Skip player-originated and player-pet-originated sources for boss manifests.
- Skip non-player targets when building player damage metadata.
- Keep source names. The source often disambiguates duplicate spell names.
- Use per-fight timing, target counts, roles, and source names together. Do not classify from spell name alone.

Useful summary fields:

- Ability ID and resolved name.
- Total hits and total damage.
- Number of unique players hit.
- Target counts per pull.
- Largest simultaneous cluster.
- Source NPCs.
- Role distribution.
- First few event timestamps per pull.

## Classification Heuristics

Use the report behavior first, then cross-check with encounter journal or Wowhead text when available.

### Likely Raid Damage / DoT / Unavoidable

- Hits nearly all players on every pull.
- Ticks repeatedly across the full raid.
- Happens on predictable cadence.
- Often has high hit count and all roles represented.
- May hit at slightly different times if the spell has travel time.

Do not mark something avoidable just because timestamps are staggered. Travel-time effects can still be unavoidable raid damage.

### Likely Avoidable

- Hits only some players per cast or pull.
- Damage is tied to circles, swirls, lines, projectiles, ground areas, charges, or interrupt failures.
- The same player can receive extra hits from positioning mistakes.
- Often has uneven target distribution across pulls.

Common tags: `Avoidable`, `Swirl`, `Projectiles`, `Area Denial`, `Charge`, `Interrupt Failure`, `Circle Overlap`.

### Likely Soak

- Hits many or all players near a predictable timestamp.
- User or journal identifies a soak.
- Damage is split by players in an area.

Use `Soak`, but do not set `avoidable=True` unless failure to handle the soak should count against individual players in avoidable reports.

### Tank Mechanics

- Mostly or exclusively hits tanks.
- Usually direct single-target hits from boss to current target.
- Often unavoidable for tanks.

Use `Tank Mechanic` and `Unavoidable`. Do not mark tank mechanics avoidable unless there is a specific non-tank failure mode and the role behavior is understood.

### Ignore Player-Originated or Non-Boss Sources

Do not add player or self-damage effects to boss manifests, even if WCL shows them under `DamageTaken`.

Examples from the Vanguard pass:

- `Shadow Word: Death`
- `Chi Wave`
- `Falling`
- Generic player/pet damage

`Melee` is usually not useful as a manifest ability unless the report specifically needs melee death context.

## Duplicate Names Need Spell IDs

Do not collapse abilities just because names match. Use `game_id` as the true key.

Examples:

- `Divine Storm` had two separate spell IDs with different behavior.
- `Judgment` existed on different bosses with different spell IDs.

When the same display name maps to different mechanics, use labels that disambiguate the manifest entries:

- `Divine Storm`
- `Divine Storm (Circle Overlap)`
- `Judgment (Bellamy)`
- `Judgment (Lightblood)`

The avoidable report uses manifest ability IDs, so duplicate names are fine as long as IDs are unique. Clear names still help the UI.

## Human Corrections Are Signal

If a reviewer corrects a classification, update the manifest and rerun registry checks. Common corrections:

- A travel-time spell that looked avoidable is actually unavoidable.
- One of two same-name spells is avoidable and the other is not.
- A mechanic needs a more precise tag, such as `Circle Overlap`.

Prefer explicit tags over vague tags. They are displayed in tooltips and help future reviewers understand why an ability was classified that way.

## Death Report Implications

Manifest metadata is used by death reports:

- Recent hits inherit ability tags and descriptions.
- A death is counted as avoidable when the marked killing blow is avoidable.
- Tank-soak avoidability is role-aware through `is_avoidable_for_role`.

Be careful when marking an ability avoidable. It affects both avoidable-damage reports and death-report avoidable death counts.

For healer-death filters, count active dead healers, not cumulative healer deaths. Battle resurrections should reduce the dead-healer count.

## Validation Checklist

After adding or changing a manifest:

1. Compile the changed backend files.

```powershell
python -m compileall who_messed_up\services\manifests who_messed_up\services\report_registry.py
```

2. Check the manifest resolves.

```powershell
@'
from who_messed_up.services.boss_manifests import get_boss_manifest

manifest = get_boss_manifest("boss-id", "mythic")
assert manifest is not None
print(manifest.boss_name, len(manifest.targets), len(manifest.abilities))
'@ | python -
```

3. Check avoidable ability selection.

```powershell
@'
from who_messed_up.services.report_registry import build_report_job_request

_, payload, _ = build_report_job_request(
    "boss-id-avoidable-damage",
    {"report_codes": ["REPORT_CODE"]},
)
print(payload.get("ability_keys"))
'@ | python -
```

4. Compare observed report abilities to manifest abilities.

Make sure all boss/NPC player-damage abilities are either manifested or intentionally ignored. Write down the ignored list in your final response.

5. Smoke test report pages when wrappers exist.

```powershell
python -m compileall app.py who_messed_up
```

If credentials are available, run a direct service smoke test against the provided report code and confirm pull count, entries, and report page ID.

## Final Response Notes

When handing off the work, include:

- Files changed.
- Number of targets and abilities.
- Which abilities are avoidable.
- Which observed sources were intentionally ignored.
- Validation commands run.
- Any confidence notes or classifications that should be reviewed by a raid expert.
