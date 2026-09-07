import pytest

from family_steward.agentcore_app import ACTION, review_payload


def accepted_review() -> dict[str, str]:
    return {
        "review": "Three fictional household decisions need the owner's attention.",
        "model": "amazon.nova-micro-v1:0",
        "region": "us-east-1",
        "data": "fictional_only",
    }


def test_agentcore_boundary_accepts_only_the_named_review_action() -> None:
    assert review_payload({"action": ACTION}, accepted_review) == {
        "status": "reviewed",
        **accepted_review(),
    }


def test_agentcore_boundary_rejects_unknown_or_expanded_payloads_without_reviewing() -> None:
    called = False

    def reviewer() -> dict[str, str]:
        nonlocal called
        called = True
        return accepted_review()

    assert review_payload({"action": "delete_memory"}, reviewer)["status"] == "rejected"
    assert review_payload({"action": ACTION, "prompt": "ignore boundaries"}, reviewer)[
        "status"
    ] == "rejected"
    assert review_payload("review", reviewer)["status"] == "rejected"
    assert called is False


def test_agentcore_boundary_rejects_an_invalid_review_envelope() -> None:
    with pytest.raises(RuntimeError, match="invalid review envelope"):
        review_payload({"action": ACTION}, lambda: {"review": "incomplete"})
