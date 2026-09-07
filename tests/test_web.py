from datetime import UTC, datetime
from pathlib import Path

import pytest

from family_steward.memory import MicroMemory
from family_steward.qmd import MemorySearchResult, VerifiedMemoryHit
from family_steward.web import FamilyStewardApplication, build_dashboard

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "fictional_household.jsonl"
NOW = datetime(2026, 8, 24, 12, tzinfo=UTC)


def test_dashboard_projects_three_bounded_household_storylines() -> None:
    dashboard = build_dashboard(MicroMemory.load_jsonl(FIXTURE), NOW)
    assert dashboard["summary"] == {"decisions": 3, "prepared": 3, "remembered": 3}
    assert dashboard["decisions"][0]["source_event_id"] == "evt-school-form-sign"
    assert {item["source"] for item in dashboard["decisions"]} == {
        "School Portal",
        "Family Calendar",
        "Household Account",
    }
    assert {item["subject"] for item in dashboard["prepared"]} == {
        "School Form",
        "Appointment Coordination",
        "Household Renewal",
    }
    assert "fictional" in dashboard["mode"].lower()


def test_approval_updates_only_the_in_memory_demonstration() -> None:
    application = FamilyStewardApplication(FIXTURE)
    before = FIXTURE.read_bytes()
    dashboard = application.approve("decision:evt-school-form-sign")
    assert dashboard["summary"]["decisions"] == 2
    assert dashboard["summary"]["remembered"] == 4
    assert FIXTURE.read_bytes() == before


def test_unknown_decision_fails_closed() -> None:
    application = FamilyStewardApplication(FIXTURE)
    with pytest.raises(ValueError, match="no longer active"):
        application.approve("decision:missing")


def test_cloud_review_projects_only_public_bounded_result(monkeypatch: pytest.MonkeyPatch) -> None:
    application = FamilyStewardApplication(FIXTURE)

    calls = []

    def fake_review():
        calls.append(1)
        return {"review": "One decision needs you.", "data": "fictional_only"}

    monkeypatch.setattr("family_steward.hosted.review_hosted", fake_review)

    result = application.cloud_review()
    assert result["review"] == "One decision needs you."
    assert result["data"] == "fictional_only"
    assert application.cloud_review() == result
    assert calls == [1]


def test_cloud_review_refuses_stale_fixture_after_approval(monkeypatch):
    application = FamilyStewardApplication(FIXTURE)
    application.approve("decision:evt-school-form-sign")
    monkeypatch.setattr("family_steward.hosted.review_hosted", lambda: pytest.fail("Paid call"))
    with pytest.raises(ValueError, match="Restart"):
        application.cloud_review()


def test_cloud_failure_is_not_automatically_retried(monkeypatch):
    application = FamilyStewardApplication(FIXTURE)

    def fail():
        raise RuntimeError("Cloud unavailable")

    monkeypatch.setattr("family_steward.hosted.review_hosted", fail)
    with pytest.raises(RuntimeError):
        application.cloud_review()
    with pytest.raises(ValueError, match="already attempted"):
        application.cloud_review()


def test_detached_memory_search_fails_safe_without_guessing() -> None:
    application = FamilyStewardApplication(FIXTURE)
    result = application.search_memory("When should routine updates begin?")
    assert result["state"] == "unavailable"
    assert result["results"] == []


def test_memory_search_projects_only_verified_public_fields() -> None:
    application = FamilyStewardApplication(FIXTURE)

    class FakeRetriever:
        def search(self, query: str, memory: MicroMemory, now: datetime) -> MemorySearchResult:
            assert query == "When should routine updates begin?"
            return MemorySearchResult(
                "found",
                "Verified.",
                (
                    VerifiedMemoryHit(
                        "evt-morning-preference",
                        "preference",
                        "Do not send routine household updates before 8:00 AM.",
                        "fictional_owner",
                        "2026-08-21T12:02:00+00:00",
                    ),
                ),
            )

    application.retriever = FakeRetriever()  # type: ignore[assignment]
    result = application.search_memory("When should routine updates begin?")
    serialized = str(result)
    assert result["state"] == "found"
    assert result["results"][0]["value"].startswith("Do not send")
    assert "evt-morning" not in serialized
    assert "score" not in serialized
    assert "qmd://" not in serialized
