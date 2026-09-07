"""Explicit, bounded client for the deployed fictional AgentCore reviewer."""

from __future__ import annotations

import json
import os
import re
from uuid import uuid4

MAX_RESPONSE_BYTES = 16_384


def review_hosted() -> dict[str, str]:
    import boto3
    from botocore.config import Config

    arn = os.environ.get("FAMILY_STEWARD_RUNTIME_ARN", "")
    if not re.fullmatch(
        r"arn:aws:bedrock-agentcore:us-east-1:\d{12}:runtime/"
        r"FamilySteward_FamilyStewardReviewer-[A-Za-z0-9]+", arn
    ):
        raise RuntimeError("Configure the approved Family Steward runtime ARN first")
    session = boto3.Session(profile_name="family-steward-deploy", region_name="us-east-1")
    identity = session.client("sts").get_caller_identity()
    if ":assumed-role/FamilyStewardDeploymentRole/" not in identity.get("Arn", ""):
        raise RuntimeError("The approved Family Steward role is required")
    if identity.get("Account") != arn.split(":")[4]:
        raise RuntimeError("Runtime account does not match the approved role")
    client = session.client(
        "bedrock-agentcore",
        config=Config(connect_timeout=10, read_timeout=90, retries={"total_max_attempts": 1}),
    )
    response = client.invoke_agent_runtime(
        agentRuntimeArn=arn,
        qualifier="DEFAULT",
        runtimeSessionId=f"family-steward-demo-{uuid4()}",
        contentType="application/json",
        accept="application/json",
        payload=json.dumps({"action": "review_fictional_household"}).encode(),
    )
    stream = response["response"]
    try:
        raw = stream.read(MAX_RESPONSE_BYTES + 1)
    finally:
        stream.close()
    if len(raw) > MAX_RESPONSE_BYTES or response.get("statusCode") != 200:
        raise RuntimeError("Hosted review failed its response boundary")
    result = json.loads(raw)
    expected = {"status", "review", "model", "region", "data"}
    if not isinstance(result, dict) or set(result) != expected:
        raise RuntimeError("Invalid hosted review envelope")
    if (result["status"], result["model"], result["region"], result["data"]) != (
        "reviewed", "amazon.nova-micro-v1:0", "us-east-1", "fictional_only"
    ) or not isinstance(result["review"], str) or not result["review"].strip():
        raise RuntimeError("Invalid hosted review provenance")
    return {key: result[key] for key in ("review", "model", "region", "data")}
