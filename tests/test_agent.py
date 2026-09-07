from datetime import UTC, datetime

from family_steward.agent import SYSTEM_PROMPT, build_review_tool, public_response_text, scan_packet
from family_steward.memory import MemoryEvent, MemoryKind, MicroMemory
from family_steward.steward import FamilySteward

NOW = datetime(2026, 8, 21, 12, tzinfo=UTC)


def steward() -> FamilySteward:
    return FamilySteward(
        MicroMemory(
            [
                MemoryEvent(
                    event_id="prepare",
                    kind=MemoryKind.COMMITMENT,
                    subject="school_form",
                    value="Prepare known fields.",
                    recorded_at=NOW,
                    source="fictional_fixture",
                ),
                MemoryEvent(
                    event_id="authorize",
                    kind=MemoryKind.COMMITMENT,
                    subject="school_form",
                    value="Approve final authorization?",
                    recorded_at=NOW,
                    source="fictional_fixture",
                    requires_owner=True,
                ),
            ]
        )
    )


def test_scan_packet_omits_internal_source_identifiers() -> None:
    packet = scan_packet(steward().scan(NOW))

    assert packet["should_interrupt"] is True
    assert packet["prepared"] == ["Prepare known fields."]
    assert "source_event_id" not in packet["decisions"][0]


def test_strands_tool_is_read_only_and_explicitly_named() -> None:
    review_tool = build_review_tool(steward(), NOW)

    assert review_tool.tool_name == "review_household_state"
    assert review_tool.tool_spec["inputSchema"]["json"]["properties"] == {}
    assert "without changing" in review_tool.tool_spec["description"]


def test_system_prompt_denies_silent_authority() -> None:
    prompt = SYSTEM_PROMPT.lower()

    assert "never claim that you changed memory" in prompt
    assert "do not request secrets" in prompt


def test_public_response_removes_internal_reasoning() -> None:
    response = public_response_text(
        "<thinking>private chain</thinking>\n"
        "**Decision requiring owner authority:**\n"
        "- **Decision ID:** decision:private\n"
        "- **Question:** One decision needs you.\n"
        "- **Subject:** private_key"
    )
    assert response == "Decision requiring owner authority: Question: One decision needs you."
