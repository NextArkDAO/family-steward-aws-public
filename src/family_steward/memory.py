"""Small append-only memory primitives for fictional household workflows."""

from __future__ import annotations

import json
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any


class MemoryKind(StrEnum):
    FACT = "fact"
    COMMITMENT = "commitment"
    PREFERENCE = "preference"
    DECISION = "decision"
    OUTCOME = "outcome"


@dataclass(frozen=True, slots=True)
class MemoryEvent:
    event_id: str
    kind: MemoryKind
    subject: str
    value: str
    recorded_at: datetime
    source: str
    requires_owner: bool = False
    expires_at: datetime | None = None
    supersedes: str | None = None

    def __post_init__(self) -> None:
        if self.recorded_at.tzinfo is None:
            raise ValueError("recorded_at must include a timezone")
        if self.expires_at is not None:
            if self.expires_at.tzinfo is None:
                raise ValueError("expires_at must include a timezone")
            if self.expires_at <= self.recorded_at:
                raise ValueError("expires_at must be later than recorded_at")

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["kind"] = self.kind.value
        payload["recorded_at"] = self.recorded_at.astimezone(UTC).isoformat()
        if self.expires_at is not None:
            payload["expires_at"] = self.expires_at.astimezone(UTC).isoformat()
        return payload

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> MemoryEvent:
        return cls(
            event_id=str(payload["event_id"]),
            kind=MemoryKind(payload["kind"]),
            subject=str(payload["subject"]),
            value=str(payload["value"]),
            recorded_at=datetime.fromisoformat(str(payload["recorded_at"])),
            source=str(payload["source"]),
            requires_owner=bool(payload.get("requires_owner", False)),
            expires_at=(
                datetime.fromisoformat(str(payload["expires_at"]))
                if payload.get("expires_at")
                else None
            ),
            supersedes=(str(payload["supersedes"]) if payload.get("supersedes") else None),
        )


class MicroMemory:
    """Append-only event collection with optional JSONL persistence."""

    def __init__(self, events: Iterable[MemoryEvent] = ()) -> None:
        self._events: list[MemoryEvent] = []
        self._ids: set[str] = set()
        for event in events:
            self.append(event)

    @property
    def events(self) -> tuple[MemoryEvent, ...]:
        return tuple(self._events)

    def append(self, event: MemoryEvent) -> None:
        if event.event_id in self._ids:
            raise ValueError(f"duplicate event_id: {event.event_id}")
        if event.supersedes is not None and event.supersedes not in self._ids:
            raise ValueError(f"unknown superseded event: {event.supersedes}")
        self._events.append(event)
        self._ids.add(event.event_id)

    def active(self, now: datetime) -> tuple[MemoryEvent, ...]:
        superseded = {event.supersedes for event in self._events if event.supersedes}
        return tuple(
            event
            for event in self._events
            if event.event_id not in superseded
            and (event.expires_at is None or event.expires_at > now)
        )

    def save_jsonl(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8", newline="\n") as handle:
            for event in self._events:
                handle.write(json.dumps(event.to_dict(), sort_keys=True) + "\n")

    @classmethod
    def load_jsonl(cls, path: Path) -> MicroMemory:
        events: list[MemoryEvent] = []
        with path.open(encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                if not line.strip():
                    continue
                try:
                    events.append(MemoryEvent.from_dict(json.loads(line)))
                except (KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
                    raise ValueError(f"invalid memory event on line {line_number}") from error
        return cls(events)
