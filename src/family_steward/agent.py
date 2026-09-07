"""Bounded Strands adapter for the Family Steward reasoning layer."""

from __future__ import annotations

import json
import re
from datetime import datetime
from typing import TYPE_CHECKING, Any

from strands import Agent, tool
from strands.models import Model

from family_steward.steward import FamilySteward, ScanResult

if TYPE_CHECKING:
    from strands.tools.decorator import DecoratedFunctionTool


SYSTEM_PROMPT = """You are the Family Steward for a fictional household demonstration.
Explain only the bounded packet returned by the household review tool. Routine preparation
should remain quiet. Surface a decision only when the packet says owner authority is required.
Never claim that you changed memory, approved a decision, sent a message, or completed a
real-world action. Do not request secrets or infer missing household facts.
"""

_THINKING_BLOCK = re.compile(r"<thinking>.*?</thinking>", re.DOTALL | re.IGNORECASE)


def public_response_text(response: object) -> str:
    """Remove provider-internal reasoning before returning a household-facing answer."""
    text = _THINKING_BLOCK.sub("", str(response)).strip()
    public_lines = []
    for line in text.splitlines():
        normalized = line.strip()
        lowered = normalized.lower()
        if "decision id" in lowered or lowered.startswith(("- **subject", "subject:")):
            continue
        normalized = normalized.removeprefix("- ").replace("**", "").strip()
        if normalized:
            public_lines.append(normalized)
    text = " ".join(public_lines)
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        raise RuntimeError("Aster returned no household-facing review")
    if len(text) > 800 or any(marker in text for marker in ("<", ">", "```")):
        raise RuntimeError("Aster returned an invalid household-facing review")
    return text


def scan_packet(result: ScanResult) -> dict[str, Any]:
    """Project deterministic results into the only packet the model may inspect."""
    return {
        "prepared": [item.detail for item in result.prepared],
        "decisions": [
            {
                "decision_id": decision.decision_id,
                "subject": decision.subject,
                "question": decision.question,
                "reason": decision.reason,
            }
            for decision in result.decisions
        ],
        "should_interrupt": result.should_interrupt,
    }


def build_review_tool(steward: FamilySteward, now: datetime) -> DecoratedFunctionTool:
    """Create a read-only tool bound to one deterministic review instant."""

    @tool(
        name="review_household_state",
        description="Read one bounded fictional household review packet without changing it.",
    )
    def review_household_state() -> str:
        return json.dumps(scan_packet(steward.scan(now)), sort_keys=True)

    return review_household_state


def build_agent(*, model: Model, steward: FamilySteward, now: datetime) -> Agent:
    """Construct an agent only when the caller explicitly supplies a model."""
    return Agent(
        model=model,
        name="Aster",
        description="A quiet fictional family memory steward.",
        system_prompt=SYSTEM_PROMPT,
        tools=[build_review_tool(steward, now)],
        callback_handler=None,
        load_tools_from_directory=False,
    )
