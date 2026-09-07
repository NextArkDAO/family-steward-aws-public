"""Bedrock AgentCore boundary for one bounded fictional household review."""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from bedrock_agentcore.runtime import BedrockAgentCoreApp

from family_steward.agent import build_agent, public_response_text
from family_steward.cloud import AWS_REGION, MODEL_ID, build_bedrock_model
from family_steward.memory import MicroMemory
from family_steward.steward import FamilySteward

ACTION = "review_fictional_household"
DEMO_NOW = datetime(2026, 8, 24, 12, tzinfo=UTC)
runtime = BedrockAgentCoreApp()


def review_payload(
    payload: object,
    reviewer: Callable[[], dict[str, str]],
) -> dict[str, str]:
    """Validate the runtime request before any model or household code runs."""
    if not isinstance(payload, dict) or set(payload) != {"action"}:
        return {"status": "rejected", "detail": "A bounded review action is required."}
    if payload["action"] != ACTION:
        return {"status": "rejected", "detail": "That action is not allowed."}

    result = reviewer()
    if set(result) != {"data", "model", "region", "review"}:
        raise RuntimeError("Aster returned an invalid review envelope")
    return {
        "status": "reviewed",
        "review": result["review"],
        "model": result["model"],
        "region": result["region"],
        "data": result["data"],
    }


def fixture_path() -> Path:
    """Find the packaged fixture first and the repository fixture during development."""
    packaged = Path(__file__).resolve().parent / "fixtures" / "fictional_household.jsonl"
    if packaged.is_file():
        return packaged
    return Path(__file__).resolve().parents[2] / "fixtures" / "fictional_household.jsonl"


def cloud_reviewer() -> dict[str, str]:
    """Run one explicit review with only the runtime role and fictional fixture."""
    steward = FamilySteward(MicroMemory.load_jsonl(fixture_path()))
    agent = build_agent(
        model=build_bedrock_model(runtime_role=True),
        steward=steward,
        now=DEMO_NOW,
    )
    response = agent(
        "Review the fictional household state once. Return only the owner decisions that "
        "require attention in one short plain-language paragraph. Do not use Markdown, "
        "internal IDs, subject keys, or bullets. Do not describe routine preparation or claim "
        "any action occurred."
    )
    return {
        "review": public_response_text(response),
        "model": MODEL_ID,
        "region": AWS_REGION,
        "data": "fictional_only",
    }


@runtime.entrypoint
def invoke(payload: dict[str, Any]) -> dict[str, str]:
    return review_payload(payload, cloud_reviewer)


def main() -> None:
    runtime.run()


if __name__ == "__main__":
    main()
