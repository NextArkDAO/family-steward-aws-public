"""Rebuild the fictional QMD projection and print its trusted manifest digest."""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

from family_steward.memory import MicroMemory
from family_steward.qmd import QMD_COLLECTION, render_event_markdown


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    fixture = root / "fixtures" / "fictional_household.jsonl"
    corpus = root / "fixtures" / "qmd-corpus" / "memory"
    manifest_path = root / "fixtures" / "qmd-authority-manifest.json"
    if corpus.parent.exists():
        shutil.rmtree(corpus.parent)
    corpus.mkdir(parents=True)

    records = []
    for event in sorted(MicroMemory.load_jsonl(fixture).events, key=lambda item: item.event_id):
        content = render_event_markdown(event)
        relative = f"memory/{event.event_id}.md"
        (corpus.parent / relative).write_bytes(content)
        records.append(
            {
                "event_id": event.event_id,
                "path": relative,
                "sha256": hashlib.sha256(content).hexdigest(),
            }
        )

    payload = {
        "collection": QMD_COLLECTION,
        "records": records,
        "schema_version": "family-steward-qmd-authority-v0",
    }
    raw = (json.dumps(payload, indent=2) + "\n").encode()
    manifest_path.write_bytes(raw)
    print(hashlib.sha256(raw).hexdigest())


if __name__ == "__main__":
    main()
