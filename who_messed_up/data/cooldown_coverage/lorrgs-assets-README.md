# Lorrgs icon and boss ability package

Includes 24 healing cooldown entries and 68 boss ability entries across 9 bosses in the current Midnight Season 2 raid selection: The Venomous Abyss and The Tidebound Grotto. There are 88 unique original image files; repeated assets are intentionally shared.

- `midnight-12.1-healing-cooldowns.json`: the previous cooldown research, now with an `icon` object on each ability. Existing timing and talent research is preserved.
- `midnight-12.1-boss-abilities.json`: raid → boss → ability records, descriptions, icon paths and source metadata.
- `lorrgs-icon-manifest.json`: unique asset inventory, checksums, dimensions, source URLs and mappings for all abilities.
- `lorrgs-icon-catalogue.html`: a browsable visual catalogue. Open locally after extracting the archive.
- `icons/lorrgs/spells/`: original Lorrgs downloads, unchanged.

## Using the paths

Resolve `ability.icon.file` relative to the JSON file's directory. Keep the `icons` directory beside the JSON files. For example, Invoke Yu'lon (322118) maps to `icons/lorrgs/spells/ability_monk_dragonkick.jpg`. `ability.icon.source_url` is the original remote URL.

Restoral (388615) is a variation of Revival (115310) in Lorrgs and therefore maps to `spell_monk_revival.jpg`. The JSON explicitly records this parent mapping rather than substituting another website's Restoral artwork.

## Boss descriptions and coverage

All 68 entries returned by Lorrgs are included, even if `shown_by_default` is false. This is the Lorrgs catalogue, not an assertion that every encounter-journal ability is included. Lorrgs' selected boss records have empty inline descriptions and delegate tooltips through Wowhead spell links. The `description` values are concise paraphrases of those game tooltips; each includes its own provenance.

Ritual of Awakening's tracked cast (1295124) has no descriptive tooltip. Its description uses the related same-named mechanic (1289683), explicitly identified in `description_source`; its tracked ID and Lorrgs icon are retained.

The API does not expose a difficulty filter for these spell records. Descriptions explain mechanics without claiming Mythic-specific numerical tuning. Lorrgs' configured timeline duration and cooldown values are retained only inside `lorrgs_metadata`; they should not be treated as independently verified spell timings. A configured cooldown of zero is not a real zero-second cooldown.

Source discovery: https://api2.lorrgs.io/api/seasons/current and https://api2.lorrgs.io/api/zones. Per-boss and per-specialization endpoints and original image URLs are preserved in the JSON. Retrieval: 2026-09-20T01:09:29.580105+00:00.
