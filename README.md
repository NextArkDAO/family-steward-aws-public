# Family Steward

Public source release for the AWS Agents for Humans Hackathon.

[Demo video](https://www.youtube.com/watch?v=7Fb_2CFAKSc) |
[Architecture](docs/ARCHITECTURE.md) |
[Judge setup](docs/JUDGE_GUIDE.md)

This repository starts with a sanitized source snapshot. Private operational
history and deployment state are not included. The runnable application,
fictional fixtures, tests and infrastructure source are included. No other
NextArk submission is modified by this release.

Before deploying in your own AWS account, replace the deliberately invalid
`000000000000` example in `infra/FamilySteward/agentcore/aws-targets.json`.
Deployment can incur charges. No owner credentials or runtime access are bundled.

Family Steward is a quiet household companion that handles recurring family
administration and only interrupts when a real human decision is required.

It is a new, public-safe project for the 2026 Agents for Humans Hackathon. It
uses fictional data and does not contain code or private material from any
other NextArk product.

## Product promise

Family Steward helps a household stay ahead of school forms, appointments,
renewals, schedules, and recurring commitments without becoming another inbox
that someone has to manage.

The first proof follows three recurring household storylines:

- school permission and schedule coordination;
- appointment preparation with a family calendar conflict;
- a household renewal with an owner-only choice.

Across each storyline, Family Steward can:

1. Observe a bounded set of household events.
2. Preserve a tiny append-only memory of facts, commitments, preferences, and
   prior decisions.
3. Complete safe preparation work silently.
4. Surface one concise decision only when owner authority is required.
5. Record the outcome without deleting the original evidence.

## Safety boundary

- Fictional demonstration data only.
- No autonomous payments, purchases, signatures, or form submission.
- No health, financial, school, or identity records from real people.
- No silent rewriting of household facts or preferences.
- No cloud deployment until the local product and cost gates pass.

## Local setup

Python 3.10 or newer is required. Python 3.12 is the accepted development
runtime for this repository.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev,agent,agentcore]"
python -m pytest
python -m family_steward.web
```

The household experience opens at `http://127.0.0.1:4180`. It uses only the
fictional fixture and records demonstration decisions in memory for the life
of that local server. It never changes the fixture on disk. The cloud review
is an explicit user action; loading or refreshing the page never invokes a
model or spends credits.

The Strands agent layer is optional during deterministic core testing. AWS
credentials are not required for the test suite or local demo. The adapter
requires an explicitly supplied model and cannot create one implicitly.

The web cloud review uses the `family-steward-deploy` profile and
`FamilyStewardDeploymentRole` to invoke the existing AgentCore reviewer in
`us-east-1`. Set `FAMILY_STEWARD_RUNTIME_ARN` to the approved runtime. The
earlier direct Bedrock CLI demo retains its separate restricted profile.
The web button does not silently fall back to direct Bedrock.

The judgeable AWS path adds the optional `agentcore` dependency and exposes
exactly one AgentCore action, `review_fictional_household`. Unknown actions and
expanded payloads are rejected before a model call. Deployment remains manual
and operator-approved; installing the dependency does not create AWS resources.

QMD `2.8.3` is the accepted optional local semantic-retrieval layer. Run
`.\scripts\setup-qmd.ps1` once to create the dedicated fictional Carter index,
then use `.\scripts\run-local.ps1` to attach it on demand. QMD discovers only
candidate paths. Family Steward verifies the pinned projection and active
micro-memory before one result may reach the browser. Raw QMD snippets, scores,
paths, and internal IDs are never returned to the browser or Nova.

## Status

The three-storyline product is operational. AgentCore was deployed and
live-verified September 3. On September 5 the web review button successfully
invoked that runtime. Temporary staging storage was removed; the runtime remains.
QMD is an optional on-demand local index, not an always-on service.

The cloud reviews its original packaged fixture, not local approval changes.
Only one attempt is allowed per server process, with successful results cached.
After local approval, restart the demo before a fresh cloud review.

Start with [Judge guide](docs/JUDGE_GUIDE.md),
[architecture](docs/ARCHITECTURE.md),
[privacy](docs/PRIVACY_AND_RESPONSIBLE_AI.md), and
[submission checklist](docs/SUBMISSION_CHECKLIST.md).
This is not yet a submitted entry. The public video and final judge-access
arrangement still require completion and operator review.

## License

Apache License 2.0.
