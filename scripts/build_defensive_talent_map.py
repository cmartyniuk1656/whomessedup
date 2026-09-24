"""Extract defensive talent entry IDs from a pinned SimulationCraft trait export.

The research's entry_id values identify trait definitions in this snapshot; WCL
records trait node entry IDs. Keep both identities and require matching node/spell.
Run with --source pointing to trait_data.inc from SOURCE_URL below.
"""
import argparse
import hashlib
import json
import re
from pathlib import Path

SOURCE_URL = "https://github.com/simulationcraft/simc/blob/849a7bef306cc46d137106e372b95fdb0fdeb061/engine/dbc/generated/trait_data.inc"
DATA = Path(__file__).resolve().parents[1] / "who_messed_up/data/defensives"


def build(source):
    raw = source.read_bytes()
    text = raw.decode("utf-8")
    research = json.loads((DATA / "defensives.json").read_text(encoding="utf-8"))
    talents = [c["talent"] for a in research["abilities"] for p in a["specialization_profiles"]
               for c in p["access"]["all_of"] if c["kind"] == "selected_talent"]
    talents += [p["talent"] for m in research["talent_modifiers"] for p in m["applicability"]]
    expected = {(t["entry_id"], t["node_id"], t["spell_id"]) for t in talents}
    entries = {}
    for line in text.splitlines():
        match = re.match(r"\s*\{\s*(\d+),\s*(\d+),\s*(\d+),\s*(\d+),\s*(\d+),\s*(\d+),\s*(\d+),\s*(\d+),", line)
        if not match:
            continue
        _, _, entry, node, _, _, definition, spell = map(int, match.groups())
        if (definition, node, spell) in expected or (entry, node, spell) in expected:
            entries[str(entry)] = dict(nodeId=node, spellId=spell, definitionId=definition)
    if not entries:
        raise ValueError("No matching talent entries in source")
    output = dict(build=text.splitlines()[0].split("wow build ")[-1], source=SOURCE_URL,
                  sourceSha256=hashlib.sha256(raw).hexdigest(),
                  description="Verified node-entry to research trait-definition mapping; node and spell must also match.",
                  entries=entries)
    (DATA / "talent-entry-map.json").write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(f"Mapped {len(entries)} defensive talent entries")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    build(parser.parse_args().source)
