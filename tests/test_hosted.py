import io
import json

import pytest

from family_steward.hosted import review_hosted

ARN = (
    "arn:aws:bedrock-agentcore:us-east-1:123456789012:runtime/"
    "FamilySteward_FamilyStewardReviewer-test"
)


def configure(monkeypatch, result=None, identity=None):
    calls = []
    monkeypatch.setenv("FAMILY_STEWARD_RUNTIME_ARN", ARN)

    class Session:
        def __init__(self, **kwargs):
            assert kwargs == {"profile_name": "family-steward-deploy", "region_name": "us-east-1"}

        def client(self, name, **kwargs):
            return self

        def get_caller_identity(self):
            return identity or {
                "Arn": "arn:aws:sts::123456789012:assumed-role/FamilyStewardDeploymentRole/test",
                "Account": "123456789012",
            }

        def invoke_agent_runtime(self, **kwargs):
            calls.append(kwargs)
            return {"statusCode": 200, "response": io.BytesIO(json.dumps(result or {
                "status": "reviewed", "review": "Three decisions need you.",
                "data": "fictional_only", "region": "us-east-1",
                "model": "amazon.nova-micro-v1:0",
            }).encode())}

    monkeypatch.setattr("boto3.Session", Session)
    return calls


def test_request_never_uploads_browser_or_memory_data(monkeypatch):
    calls = configure(monkeypatch)
    result = review_hosted()
    assert result["review"] == "Three decisions need you."
    assert json.loads(calls[0]["payload"]) == {"action": "review_fictional_household"}
    assert calls[0]["agentRuntimeArn"] == ARN
    assert calls[0]["qualifier"] == "DEFAULT"


def test_missing_runtime_fails_before_credentials(monkeypatch):
    monkeypatch.delenv("FAMILY_STEWARD_RUNTIME_ARN", raising=False)
    with pytest.raises(RuntimeError, match="Configure"):
        review_hosted()


def test_wrong_role_cannot_invoke(monkeypatch):
    calls = configure(monkeypatch, identity={"Arn": "wrong", "Account": "123456789012"})
    with pytest.raises(RuntimeError, match="role"):
        review_hosted()
    assert not calls


def test_unexpected_response_is_rejected(monkeypatch):
    configure(monkeypatch, result={"review": "Not a trusted envelope"})
    with pytest.raises(RuntimeError, match="envelope"):
        review_hosted()
