from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from family_steward.memory import MemoryEvent, MemoryKind, MicroMemory

NOW = datetime(2026, 8, 21, 12, tzinfo=UTC)


def event(event_id: str, *, expires_at: datetime | None = None) -> MemoryEvent:
    return MemoryEvent(
        event_id=event_id,
        kind=MemoryKind.FACT,
        subject="fictional",
        value="value",
        recorded_at=NOW,
        source="test",
        expires_at=expires_at,
    )


def test_memory_is_append_only_and_rejects_duplicate_ids() -> None:
    memory = MicroMemory([event("one")])
    with pytest.raises(ValueError, match="duplicate event_id"):
        memory.append(event("one"))


def test_memory_rejects_unknown_supersession() -> None:
    memory = MicroMemory()
    replacement = MemoryEvent(
        event_id="replacement",
        kind=MemoryKind.OUTCOME,
        subject="fictional",
        value="accepted",
        recorded_at=NOW,
        source="test",
        supersedes="missing",
    )
    with pytest.raises(ValueError, match="unknown superseded event"):
        memory.append(replacement)


def test_expired_events_are_not_active() -> None:
    memory = MicroMemory(
        [
            event("expired", expires_at=NOW + timedelta(hours=1)),
            event("active", expires_at=NOW + timedelta(days=2)),
        ]
    )
    active_ids = {item.event_id for item in memory.active(NOW + timedelta(days=1))}
    assert active_ids == {"active"}


def test_jsonl_round_trip(tmp_path: Path) -> None:
    original = MicroMemory([event("one")])
    path = tmp_path / "memory.jsonl"
    original.save_jsonl(path)
    restored = MicroMemory.load_jsonl(path)
    assert restored.events == original.events


def test_naive_timestamps_fail_closed() -> None:
    with pytest.raises(ValueError, match="timezone"):
        MemoryEvent(
            event_id="naive",
            kind=MemoryKind.FACT,
            subject="fictional",
            value="value",
            recorded_at=datetime(2026, 8, 21, 12),
            source="test",
        )
