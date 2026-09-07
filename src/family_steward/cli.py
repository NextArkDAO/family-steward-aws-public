"""Local fictional demonstration entry point."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from family_steward.memory import MicroMemory
from family_steward.steward import FamilySteward


def main() -> None:
    fixture = Path(__file__).resolve().parents[2] / "fixtures" / "fictional_household.jsonl"
    memory = MicroMemory.load_jsonl(fixture)
    result = FamilySteward(memory).scan(datetime(2026, 8, 24, 12, tzinfo=UTC))
    print(
        json.dumps(
            {
                "prepared": result.prepared,
                "decisions": [
                    {
                        "decision_id": item.decision_id,
                        "subject": item.subject,
                        "question": item.question,
                        "reason": item.reason,
                    }
                    for item in result.decisions
                ],
                "should_interrupt": result.should_interrupt,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
