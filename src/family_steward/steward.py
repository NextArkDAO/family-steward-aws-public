"""Deterministic interruption gate for Family Steward."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from family_steward.memory import MemoryEvent, MemoryKind, MicroMemory


@dataclass(frozen=True, slots=True)
class DecisionPacket:
    decision_id: str
    subject: str
    question: str
    reason: str
    source_event_id: str
    source: str


@dataclass(frozen=True, slots=True)
class PreparedTask:
    subject: str
    detail: str
    source: str


@dataclass(frozen=True, slots=True)
class ScanResult:
    prepared: tuple[PreparedTask, ...]
    decisions: tuple[DecisionPacket, ...]

    @property
    def should_interrupt(self) -> bool:
        return bool(self.decisions)


class FamilySteward:
    def __init__(self, memory: MicroMemory) -> None:
        self.memory = memory

    def scan(self, now: datetime) -> ScanResult:
        prepared: list[PreparedTask] = []
        decisions: list[DecisionPacket] = []

        for event in self.memory.active(now):
            if event.kind is not MemoryKind.COMMITMENT:
                continue
            if event.requires_owner:
                decisions.append(
                    DecisionPacket(
                        decision_id=f"decision:{event.event_id}",
                        subject=event.subject,
                        question=event.value,
                        reason="The remaining step requires household-owner authority.",
                        source_event_id=event.event_id,
                        source=event.source,
                    )
                )
            else:
                prepared.append(
                    PreparedTask(
                        subject=event.subject,
                        detail=event.value,
                        source=event.source,
                    )
                )

        return ScanResult(prepared=tuple(prepared), decisions=tuple(decisions))

    def record_outcome(
        self,
        *,
        decision: DecisionPacket,
        outcome_event_id: str,
        outcome: str,
        recorded_at: datetime,
    ) -> MemoryEvent:
        event = MemoryEvent(
            event_id=outcome_event_id,
            kind=MemoryKind.OUTCOME,
            subject=decision.subject,
            value=outcome,
            recorded_at=recorded_at,
            source="owner_decision",
            supersedes=decision.source_event_id,
        )
        self.memory.append(event)
        return event
