from pathlib import Path

from tools.prepare_agentcore_runtime import PACKAGE_FILES, prepare_runtime


def test_prepare_runtime_copies_only_allowlisted_source_and_fixture(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    package = root / "src" / "family_steward"
    fixture_dir = root / "fixtures"
    package.mkdir(parents=True)
    fixture_dir.mkdir()

    for name in PACKAGE_FILES:
        (package / name).write_text(f"# {name}\n", encoding="ascii")
    (package / "private.py").write_text("SECRET = True\n", encoding="ascii")
    (fixture_dir / "fictional_household.jsonl").write_text("{}\n", encoding="ascii")
    (root / ".env").write_text("TOKEN=private\n", encoding="ascii")

    destination = root / "infra" / ".agentcore-build" / "reviewer"
    copied = prepare_runtime(root, destination)

    relative_files = {
        path.relative_to(destination).as_posix()
        for path in destination.rglob("*")
        if path.is_file()
    }
    assert relative_files == {
        "pyproject.toml",
        "family_steward/fixtures/fictional_household.jsonl",
        *(f"family_steward/{name}" for name in PACKAGE_FILES),
    }
    assert len(copied) == len(PACKAGE_FILES) + 2
    assert not (destination / "family_steward" / "private.py").exists()
    assert not (destination / ".env").exists()


def test_prepare_runtime_replaces_stale_staging_content(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    package = root / "src" / "family_steward"
    fixture_dir = root / "fixtures"
    package.mkdir(parents=True)
    fixture_dir.mkdir()
    for name in PACKAGE_FILES:
        (package / name).write_text("# source\n", encoding="ascii")
    (fixture_dir / "fictional_household.jsonl").write_text("{}\n", encoding="ascii")

    destination = root / "build"
    destination.mkdir()
    (destination / "stale-secret.txt").write_text("remove me\n", encoding="ascii")

    prepare_runtime(root, destination)

    assert not (destination / "stale-secret.txt").exists()
