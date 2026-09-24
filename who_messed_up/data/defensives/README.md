# Midnight 12.1 major raid defensives

Research date: 2026-09-23. Version: 1.0.0. Raid PvE only.

Open **report.html** for the searchable human-readable report. Keep the icons directory beside it. The report works offline; source links require internet access.

Contents: 40 specializations, 69 defensive entries (including replacement variants), 3 supporting reset/recovery abilities, 191 talent modifiers, and 70 unique icons.

- report.html / report.md — research report
- defensives.json — machine-readable catalogue
- defensives.schema.json — JSON structure schema
- integration-guide.md — audit logic, event requirements and limitations
- icon-manifest.json / icons — 71 ability mappings to 69 verified image files
- source-receipts.json — research snapshot hashes
- validation.json — package integrity results

64 unique icons came from Lorrgs. Six matching assets were unavailable there and use explicitly labeled Wowhead CDN fallbacks: Lay on Hands, Holy Bulwark, Impending Victory, Black Ox Brew, Cold Snap and Mortal Coil. The manifest maps all 72 entries to 69 files and includes URLs, dimensions and SHA-256 hashes. An icon grouping is not proof that two spell IDs are interchangeable in combat logs.

Base cooldowns include inherent specialization adjustments and exclude optional talents. Modifier rules identify ranks, hero trees and choice nodes. Single-talent examples are not fully stacked builds. Passive talents are metadata; they are not independent defensives to score.

This is research metadata, not a tested Warcraft Logs parser or complete cooldown simulation engine. Validate event IDs, automatic casts and uncertain stacking rules against representative logs before reporting definitive missed uses. Missing build or event data should yield unknown, not a penalty.

The artwork is game imagery delivered by the cited providers; downloading it does not grant a new redistribution license.
