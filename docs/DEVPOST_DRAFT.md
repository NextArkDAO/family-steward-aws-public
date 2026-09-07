# Devpost draft - not submitted

## Project name
Family Steward

## Tagline
Less household administration. Only the decisions that need you.

## Inspiration
Families repeatedly juggle school forms, appointment conflicts and renewals.
Another inbox is not relief. We wanted an agent that prepares the routine work
and knows when to stop and ask a person.

## What it does
Family Steward demonstrates three fictional household workflows. Its local
controller distinguishes safe preparation from owner-only decisions, preserves
the source event when an approval is recorded, and offers verified local memory
recall. Aster, the Strands reviewer hosted on Amazon Bedrock AgentCore, uses Nova
Micro to explain the original fictional decision packet. It cannot pay, sign,
send, or resolve a household decision on its own.

## How we built it
Python implements the deterministic authority gate and append-only micro-memory.
A small local web interface shows preparation, decisions and source-linked memory.
QMD provides optional local candidate retrieval; application validation checks the
candidate against the accepted projection and current event before display.
AgentCore hosts one bounded Strands action with IAM authentication. The explicit
browser review travels through the local server to that runtime. It sends only a
fixed action identifier, never browser content or real household information.

## Challenges
The challenge was keeping the agent useful without making it authoritative.
Another was demonstrating real AWS execution without creating an unnecessary
public paid endpoint. We also separated the cloud's fixed fictional snapshot
from mutable local approvals so an outdated review cannot masquerade as current.

## Accomplishments
Three recurring storylines; a clear approval boundary; verified local retrieval;
an authenticated AgentCore deployment; and a bounded cloud-review connection.
The local experience is usable even without cloud credentials. This prototype
demonstrates the workflow, not measured household time savings or production readiness.

## What we learned
Preparation and execution are different promises. A useful household agent must
explain which work was actually done, what remains pending, and who has authority.

## Next
Evaluate with consenting households before adding real integrations. Durable
storage, access controls, and real-world effects require separate design and approval.

## Built with
Python, Strands Agents SDK, Amazon Bedrock AgentCore, Amazon Nova Micro, QMD,
HTML, CSS, JavaScript.

## Required attachments still to verify
- Public repository: https://github.com/NextArkDAO/family-steward (visibility gate pending).
- Architecture: docs/ARCHITECTURE.md.
- Public video: pending recording and approval; maximum five minutes.
- AWS Builder ID: operator must verify the correct account identifier in Devpost.
- Testing access: docs/JUDGE_GUIDE.md; finalize access before submission.

## Disclosure
New project built during the hackathon period using public frameworks and AI coding
assistance. QMD and the AWS/Strands libraries are pre-existing third-party tools,
not claimed as original work. No code or private data from another NextArk product
is included. Review the dependency licenses before public release.
