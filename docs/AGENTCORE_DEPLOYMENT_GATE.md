# AgentCore Deployment Gate

Status: ready for deployment approval; no AWS resources created.

## Accepted deployment

Family Steward deploys one disposable, private reviewer for the hackathon proof:

- Amazon Bedrock AgentCore Runtime;
- Python 3.12 CodeZip;
- AWS IAM authorization;
- Amazon Nova Micro;
- 60-second idle timeout and 300-second maximum lifetime;
- one exact action: `review_fictional_household`.

The local household controller, QMD index, approval simulation, and append-only
memory remain on Windows. The runtime receives no real household data and has no
database, scheduler, gateway, public unauthenticated endpoint, or persistent
memory resource.

## Package receipt

The runtime staging tree is rebuilt from an explicit allowlist by
`tools/prepare_agentcore_runtime.py`. It contains seven Family Steward source
files, one fictional JSONL fixture, and a deployment `pyproject.toml`.

Local package result:

- artifact: `FamilyStewardReviewer.zip`;
- compressed size: 31.52 MB;
- entries: 4,124, including pinned third-party dependencies;
- unsafe named entries: none;
- repository, virtual environment, credentials, `.env` files, QMD state,
  browser data, and unrelated workstation files: excluded.

Generated package and staging output are ignored by Git.

## Synthesized resources

The local CloudFormation template contains four resources:

1. one `AWS::BedrockAgentCore::Runtime`;
2. one runtime execution `AWS::IAM::Role`;
3. one runtime execution `AWS::IAM::Policy`;
4. one `AWS::CDK::Metadata` resource.

There is no DynamoDB table, Lambda function, EventBridge schedule, API Gateway,
Cognito pool, AgentCore Memory, AgentCore Gateway, or payment resource.

The generated runtime role trusts only `bedrock-agentcore.amazonaws.com`. Its
data-plane permissions are limited to Bedrock model invocation, AgentCore
runtime logging and tracing, and the configuration-bundle operations emitted by
the official AgentCore CDK construct. Application code hard-pins Nova Micro and
rejects any payload other than the exact accepted action before model use.

## Verification

- Python tests: 37 passed;
- Ruff: passed for `src`, `tests`, and `tools`;
- AgentCore schema validation: passed;
- CodeZip packaging: passed;
- staged fail-closed smoke test: passed;
- CDK TypeScript build: passed;
- local CloudFormation synthesis: passed;
- npm production dependency audit: zero known vulnerabilities;
- `git diff --check`: passed.

## Current blocker

The existing `family-steward` and `family-steward-login` identities correctly
lack CloudFormation deployment authority. The first AWS deployment requires an
operator-approved infrastructure identity or a narrowly scoped deployment role.
Do not add CloudFormation or IAM permissions to the runtime role.

## Deployment gate

Before deployment, Dwayne must explicitly approve creation of the four
synthesized resources and the expected low-volume AgentCore and Nova Micro
usage. After deployment, invoke the fictional review once, capture logs and the
response, record cost controls and deletion instructions, then remove the stack
after judging evidence is secured unless continued hosting is approved.
