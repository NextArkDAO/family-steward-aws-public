from typing import Any

import pytest

from family_steward import cloud


class FakeSts:
    def __init__(self, arn: str) -> None:
        self.arn = arn

    def get_caller_identity(self) -> dict[str, str]:
        return {"Arn": self.arn}


class FakeSession:
    def __init__(self, arn: str) -> None:
        self.arn = arn

    def client(self, service: str) -> FakeSts:
        assert service == "sts"
        return FakeSts(self.arn)


def test_cloud_model_uses_only_accepted_profile_region_and_model(monkeypatch: Any) -> None:
    recorded: dict[str, Any] = {}
    session = FakeSession(
        "arn:aws:sts::000000000000:assumed-role/FamilyStewardBedrockDeveloper/test"
    )

    def fake_session(*, profile_name: str, region_name: str) -> FakeSession:
        recorded.update(profile=profile_name, region=region_name)
        return session

    def fake_model(**config: Any) -> dict[str, Any]:
        recorded.update(config)
        return config

    monkeypatch.setattr(cloud.boto3, "Session", fake_session)
    monkeypatch.setattr(cloud, "BedrockModel", fake_model)

    model = cloud.build_bedrock_model()

    assert recorded["profile"] == "family-steward"
    assert recorded["region"] == "us-east-1"
    assert model["model_id"] == "amazon.nova-micro-v1:0"
    assert model["max_tokens"] == 256


def test_cloud_model_rejects_root_identity(monkeypatch: Any) -> None:
    monkeypatch.setattr(
        cloud.boto3,
        "Session",
        lambda **_: FakeSession("arn:aws:iam::000000000000:root"),
    )

    with pytest.raises(RuntimeError, match="restricted AWS role"):
        cloud.build_bedrock_model()


def test_cloud_model_uses_runtime_role_without_a_workstation_profile(monkeypatch: Any) -> None:
    recorded: dict[str, Any] = {}
    session = FakeSession("runtime-role-does-not-require-sts-inspection")

    def fake_session(**config: str) -> FakeSession:
        recorded.update(config)
        return session

    def fake_model(**config: Any) -> dict[str, Any]:
        recorded.update(model=config)
        return config

    monkeypatch.setattr(cloud.boto3, "Session", fake_session)
    monkeypatch.setattr(cloud, "BedrockModel", fake_model)

    cloud.build_bedrock_model(runtime_role=True)

    assert recorded["region_name"] == "us-east-1"
    assert "profile_name" not in recorded
    assert recorded["model"]["model_id"] == "amazon.nova-micro-v1:0"
