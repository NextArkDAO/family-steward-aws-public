"""Build the minimal, fictional-only AgentCore reviewer source tree."""

from __future__ import annotations

import shutil
from pathlib import Path

PACKAGE_FILES = (
    "__init__.py",
    "agent.py",
    "agentcore_app.py",
    "cloud.py",
    "memory.py",
    "steward.py",
)
PYPROJECT = """[build-system]
requires = ["setuptools>=75", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "family-steward-agentcore-runtime"
version = "0.1.0"
requires-python = ">=3.12,<3.13"
dependencies = [
  "bedrock-agentcore==1.22.0",
  "boto3==1.43.78",
  "botocore[crt]==1.43.78",
  "strands-agents==1.53.0",
]

[tool.setuptools.packages.find]
where = ["."]
include = ["family_steward*"]
"""


def prepare_runtime(root: Path, destination: Path) -> tuple[Path, ...]:
    """Rebuild a deployment tree from an explicit allowlist of canonical files."""
    source_package = root / "src" / "family_steward"
    fixture = root / "fixtures" / "fictional_household.jsonl"

    if destination.exists():
        shutil.rmtree(destination)
    package = destination / "family_steward"
    fixtures = package / "fixtures"
    fixtures.mkdir(parents=True)

    copied: list[Path] = []
    for name in PACKAGE_FILES:
        source = source_package / name
        target = package / name
        shutil.copy2(source, target)
        copied.append(target)

    target_fixture = fixtures / fixture.name
    shutil.copy2(fixture, target_fixture)
    copied.append(target_fixture)

    pyproject = destination / "pyproject.toml"
    pyproject.write_text(PYPROJECT, encoding="ascii", newline="\n")
    copied.append(pyproject)
    return tuple(copied)


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    destination = (
        root
        / "infra"
        / "FamilySteward"
        / ".agentcore-build"
        / "FamilyStewardReviewer"
    )
    files = prepare_runtime(root, destination)
    print(f"Prepared {len(files)} allowlisted files at {destination}")


if __name__ == "__main__":
    main()
