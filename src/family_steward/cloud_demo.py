"""One-call fictional Bedrock acceptance demonstration."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from family_steward.agent import build_agent, public_response_text
from family_steward.cloud import build_bedrock_model
from family_steward.memory import MicroMemory
from family_steward.steward import FamilySteward


def main() -> None:
    fixture = Path(__file__).resolve().parents[2] / "fixtures" / "fictional_household.jsonl"
    steward = FamilySteward(MicroMemory.load_jsonl(fixture))
    agent = build_agent(
        model=build_bedrock_model(),
        steward=steward,
        now=datetime(2026, 8, 24, 12, tzinfo=UTC),
    )
    response = agent(
        "Review the fictional household state once. Stay quiet about prepared routine work and "
        "return only the owner decision that truly requires attention."
    )
    print(public_response_text(response))


if __name__ == "__main__":
    main()
