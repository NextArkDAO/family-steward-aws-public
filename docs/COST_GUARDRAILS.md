# Cost Guardrails

## Account posture

- AWS account plan: Free Plan
- Initial build target was local only; the bounded reviewer is now hosted.
- Expected cloud demonstration cost: below USD 5
- Review threshold: USD 5
- Hard stop threshold: USD 10

These are operator review thresholds, not an AWS-enforced spending cap. A
current billing total has not been verified in this receipt. Do not report the
expected cost as actual spend or claim a budget alarm exists without evidence.

The web client permits one cloud attempt per process, no automatic retries,
and cached successful responses. Loading the page does not spend. AgentCore
sessions idle out after 60 seconds, with a 300-second maximum lifetime. There
is no public anonymous paid endpoint or scheduled invocation.

Immediate local stop: stop the demo server or unset FAMILY_STEWARD_RUNTIME_ARN.
Full cloud stop: with operator approval delete the named CloudFormation stack
described in AGENTCORE_DEPLOYMENT_RECEIPT.md. Do not delete the reviewer before
the judging-access plan has been fulfilled. Staging S3 storage is already gone.

## Rules

1. Do not upgrade the AWS account without Dwayne's separate approval.
2. Do not create persistent compute before local tests pass.
3. Use synthetic data only.
4. Use Nova Micro by default and cap model calls during development.
5. Prefer scale-to-zero and pay-per-request services.
6. Delete disposable demonstration resources after proof is captured.
7. Record every cloud resource, region, cost control, and cleanup command.

