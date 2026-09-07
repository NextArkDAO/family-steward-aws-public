from datetime import UTC, datetime

from family_steward.memory import MemoryEvent, MemoryKind, MicroMemory
from family_steward.steward import FamilySteward

NOW = datetime(2026, 8, 21, 12, tzinfo=UTC)


def commitment(event_id: str, value: str, *, requires_owner: bool) -> MemoryEvent:
    return MemoryEvent(
        event_id=event_id,
        kind=MemoryKind.COMMITMENT,
        subject="school_form",
        value=value,
        recorded_at=NOW,
        source="fictional_school_portal",
        requires_owner=requires_owner,
    )


def test_safe_preparation_remains_quiet() -> None:
    steward = FamilySteward(
        MicroMemory([commitment("prepare", "Prepare known fields.", requires_owner=False)])
    )
    result = steward.scan(NOW)
    assert len(result.prepared) == 1
    assert result.prepared[0].detail == "Prepare known fields."
    assert result.prepared[0].source == "fictional_school_portal"
    assert result.decisions == ()
    assert result.should_interrupt is False


def test_owner_authority_creates_one_bounded_decision() -> None:
    steward = FamilySteward(
        MicroMemory([commitment("authorize", "Approve final authorization?", requires_owner=True)])
    )
    result = steward.scan(NOW)
    assert result.should_interrupt is True
    assert len(result.decisions) == 1
    assert result.decisions[0].source_event_id == "authorize"
    assert result.decisions[0].source == "fictional_school_portal"


def test_outcome_preserves_original_event() -> None:
    memory = MicroMemory(
        [commitment("authorize", "Approve final authorization?", requires_owner=True)]
    )
    steward = FamilySteward(memory)
    decision = steward.scan(NOW).decisions[0]
    outcome = steward.record_outcome(
        decision=decision,
        outcome_event_id="outcome-authorize",
        outcome="approved",
        recorded_at=NOW,
    )
    assert len(memory.events) == 2
    assert memory.events[0].event_id == "authorize"
    assert outcome.supersedes == "authorize"
    assert {item.event_id for item in memory.active(NOW)} == {"outcome-authorize"}
