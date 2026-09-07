# Family Steward: judge guide

Track: Everyday Agents, Agents for Humans 2026. This is a standalone new project,
not the previously submitted All Things Agentic project.

## Run without AWS

Use Python 3.12 and a fresh virtual environment at the repository root:

```sh
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
python -m pip install -e ".[dev,agent,agentcore]"
python -m pytest
python -m family_steward.web
```

Open http://127.0.0.1:4180. The local demo is free to run without cloud credentials.
It is not a simulated successful cloud call: without configured AWS access the
cloud review explicitly fails. The household workflow and approval simulation
remain functional offline. QMD is optional; see QMD_INTEGRATION.md for its separate
local setup. Missing QMD is reported honestly and does not break the dashboard.

1. Observe three prepared items and three owner decisions.
2. Inspect the source labels and remembered facts/preferences.
3. With QMD configured, search for the preferred time for routine updates.
4. Run the cloud review before approving a decision, if authorized AWS access is
   configured. This reviews the original packaged fictional snapshot, not live
   changes in the local browser.
5. Approve the school-form decision. The count changes from three to two and an
   outcome appears in memory. No actual form is signed or transmitted.
6. Restart the server to reset the in-memory demo. Refresh alone does not reset it.

## Optional hosted reviewer

The owner deployed AgentCore in us-east-1, with Nova Micro and a Strands read-only
review tool. See AGENTCORE_DEPLOYMENT_RECEIPT.md for the recorded deployment.
The browser never receives AWS credentials or invokes AWS directly.

The local server uses the existing `family-steward-deploy` profile, assuming
`FamilyStewardDeploymentRole`, and the environment variable
`FAMILY_STEWARD_RUNTIME_ARN`. It verifies the role, region, runtime name and account
before invocation. No default credential fallback. Configure this only for the
approved runtime; do not share owner credentials with judges.

Only `{"action":"review_fictional_household"}` is uploaded. No local memory,
query, approval or user-supplied text is uploaded. One attempt is allowed per
server process; successful repeat clicks return the cached result. Failures do
not silently retry. After a local approval, restart to review the original snapshot.

## Current limitations

- Synthetic household workflows, not integrations with real schools or banks.
- Local approval outcomes are in-process only, not durable across restarts.
- Hosted review uses a fixed fixture; it does not synchronize local approvals.
- QMD installation and models are optional, not bundled.
- There is no public unauthenticated paid endpoint.
- Before submission, arrange a judge-accessible cloud demonstration or recording;
  an IAM-protected endpoint alone is not anonymous judge access.

Do not submit until the public video and final testing-access instructions are complete.
