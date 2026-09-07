# AgentCore Deployment Receipt

Status: deployed and live-verified on September 3, 2026 UTC.

## Outcome

Family Steward's bounded reviewer is running in Amazon Bedrock AgentCore in
`us-east-1`. The deployed runtime is `READY` and accepted one fictional-only
household review through its authenticated `DEFAULT` endpoint.

The Windows household controller, QMD index, approval simulation, and
append-only memory remain local. No real household data was uploaded or sent to
the runtime.

## Deployment

- Stack: `AgentCore-FamilySteward-default`
- Runtime: FamilySteward reviewer (deployment-specific identifier omitted)
- Runtime version: `1`
- Model: `amazon.nova-micro-v1:0`
- Region: `us-east-1`
- Runtime state: `READY`
- Idle timeout: 60 seconds
- Maximum session lifetime: 300 seconds
- Access: IAM-authenticated AgentCore endpoint; no public unauthenticated app
  endpoint was created

The normal CDK bootstrap path was not used. Deployment used the synthesized
direct CloudFormation template and one temporary private S3 staging object so
the proof did not require broad bootstrap infrastructure.

## Created Resources

CloudFormation reports exactly four resources, all `CREATE_COMPLETE`:

1. `AWS::BedrockAgentCore::Runtime`
2. `AWS::IAM::Role`
3. `AWS::IAM::Policy`
4. `AWS::CDK::Metadata`

AgentCore also created its normal service-managed `DEFAULT` runtime endpoint
and workload identity as lifecycle parts of the runtime. They are not separate
resources in the Family Steward CloudFormation stack. The account-level
service-linked role required by AgentCore Runtime Identity was created with
operator approval.

No database, scheduler, gateway, AgentCore Memory, Lambda function, API
Gateway, Cognito pool, payment resource, or public unauthenticated endpoint was
created.

## Permission Boundary

Deployment used the local `family-steward-deploy` profile, which assumes the
narrow `FamilyStewardDeploymentRole`. Permissions were added only as AWS
reported exact dependent operations during creation. Resource-scoped actions
target the named stack, runtime, runtime endpoint, execution-role prefix, and
default workload-identity directory. Creation actions that require `*` are
conditioned on the request tag `agentcore:project-name=FamilySteward`.

Invocation is limited to the named reviewer runtime and its `DEFAULT` endpoint.
The runtime execution role trusts only AgentCore and retains the generated
model, logging, tracing, and configuration permissions required by the official
construct.

## Live Proof

Invocation session:
`family-steward-fictional-review-20260903-003`

The request contained only:

```json
{"action":"review_fictional_household"}
```

AWS returned HTTP `200` with:

- status: `reviewed`
- model: `amazon.nova-micro-v1:0`
- region: `us-east-1`
- data boundary: `fictional_only`

The reviewer surfaced three owner decisions from the packaged fictional
fixture: final authorization for a school form, resolution of an appointment
and pickup conflict, and a renewal-plan choice. It did not claim that any action
occurred.

## Verification

- live runtime state: `READY`
- live authenticated invocation: passed
- fictional-data boundary: passed
- exact CloudFormation resource count: 4
- Python tests: 37 passed
- Ruff: passed for `src`, `tests`, and `tools`
- deployment response stored only in the local temporary directory

Pytest emitted a third-party Pydantic deprecation warning and could not write
its optional cache under the current restricted shell. Neither affected the 37
passing tests.

## Cost Controls

- Nova Micro is hard-pinned by application code.
- Only one named review action is accepted.
- Invalid or expanded payloads fail closed before model use.
- The runtime receives no persistent memory or database.
- Sessions idle out after 60 seconds and have a 300-second maximum lifetime.
- No scheduler invokes the runtime.
- No public anonymous traffic path exists.

## Staging Cleanup

The temporary private staging bucket is:
an account-specific staging bucket (identifier omitted from this public release).

After explicit operator approval, the sole staging object and the empty bucket
were deleted. A read-after-delete check returned `404 Not Found`. The canonical
package remains reproducible from the committed source and local packaging
tool.

Both temporary bucket and object statements were then removed from
`FamilyStewardDeploymentRole`. A policy inspection found zero remaining `s3:`
actions. The hosted runtime remained `READY` after cleanup.

## Rollback

To remove the hosted proof, delete the CloudFormation stack
`AgentCore-FamilySteward-default` in `us-east-1`. This removes the runtime and
its generated execution role and policy. The AgentCore service-linked role is
account-level and should be reviewed separately before deletion because other
future AgentCore runtimes may depend on it.

Deleting the stack does not affect the local Windows controller, QMD data,
fictional fixture, source code, or Git history.
