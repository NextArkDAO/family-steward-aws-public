"""Explicit least-privilege Bedrock connection for Family Steward."""

from __future__ import annotations

import boto3
from strands.models import BedrockModel

AWS_PROFILE = "family-steward"
AWS_REGION = "us-east-1"
MODEL_ID = "amazon.nova-micro-v1:0"
REQUIRED_ROLE = ":assumed-role/FamilyStewardBedrockDeveloper/"


def build_bedrock_model(*, runtime_role: bool = False) -> BedrockModel:
    """Build the accepted model using either local or runtime-scoped credentials."""
    if runtime_role:
        # AgentCore supplies temporary credentials for its execution role. It must not
        # inherit a workstation profile name or depend on workstation configuration.
        session = boto3.Session(region_name=AWS_REGION)
    else:
        session = boto3.Session(profile_name=AWS_PROFILE, region_name=AWS_REGION)
        identity = session.client("sts").get_caller_identity()
        arn = str(identity.get("Arn", ""))
        if REQUIRED_ROLE not in arn:
            raise RuntimeError("Family Steward requires its restricted AWS role")

    return BedrockModel(
        boto_session=session,
        model_id=MODEL_ID,
        max_tokens=256,
        temperature=0.0,
        streaming=True,
    )
