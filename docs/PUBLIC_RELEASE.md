# Public release boundary

This AWS-only release preserves the demonstrated application from source commit
5a97c63. It starts a new public history rather than publishing the private
working repository's history. No files from other NextArk products were added.

Excluded: private operational receipts and generated AgentCore deployment state.
The AWS target account is replaced with an all-zero configuration example;
account-specific staging and runtime identifiers are omitted from the receipt.
Names of required AWS roles and profiles remain documented for reproducibility.

The fixture is the fictional Carter household. Outcomes are session-only.
The public video demonstrates an authenticated AWS call; running the local
application does not grant access to the owner's AWS account. See JUDGE_GUIDE.md
for the no-credentials test build and optional cloud setup boundary.

Apache License 2.0 covers this repository's original source. Third-party
dependencies retain their own licenses. The video uses ElevenLabs narration.
