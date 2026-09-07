import json
import shutil
import subprocess
from datetime import UTC, datetime
from pathlib import Path

import pytest

from family_steward.memory import MemoryEvent, MemoryKind, MicroMemory
from family_steward.qmd import (
    QMD_COLLECTION,
    QMD_EXPECTED_VERSION,
    QMD_INDEX,
    QmdCandidate,
    QmdCandidateProvider,
    QmdMemoryRetriever,
    load_verified_manifest,
    qmd_status,
    render_event_markdown,
)

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "fixtures" / "fictional_household.jsonl"
CORPUS = ROOT / "fixtures" / "qmd-corpus"
MANIFEST = ROOT / "fixtures" / "qmd-authority-manifest.json"
NOW = datetime(2026, 8, 24, 12, tzinfo=UTC)


def completed(stdout: str) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(args=[], returncode=0, stdout=stdout, stderr="")


class StubProvider:
    def __init__(self, candidates: tuple[QmdCandidate, ...] = (), error: Exception | None = None):
        self.candidates = candidates
        self.error = error

    def discover(self, query: str) -> tuple[QmdCandidate, ...]:
        if self.error:
            raise self.error
        return self.candidates


def retriever(provider: StubProvider, corpus: Path = CORPUS) -> QmdMemoryRetriever:
    return QmdMemoryRetriever(provider, load_verified_manifest(MANIFEST, corpus))  # type: ignore[arg-type]


def test_qmd_status_is_honest_when_windows_canary_is_not_attached() -> None:
    status = qmd_status(None)
    assert status["state"] == "adapter_ready"
    assert status["available"] is False


def test_qmd_status_requires_all_three_local_paths(tmp_path: Path) -> None:
    binary = tmp_path / "qmd.cmd"
    binary.touch()
    assert qmd_status(str(binary))["available"] is False
    assert qmd_status(str(binary), str(tmp_path), str(tmp_path))["state"] == "connected"


def test_qmd_provider_verifies_build_and_uses_dedicated_state(tmp_path: Path) -> None:
    binary = tmp_path / "qmd.cmd"
    binary.touch()
    config = tmp_path / "config"
    cache = tmp_path / "cache"
    config.mkdir()
    cache.mkdir()
    calls: list[tuple[list[str], dict[str, object]]] = []

    def runner(args: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        calls.append((args, kwargs))
        if args[-1] == "--version":
            return completed(QMD_EXPECTED_VERSION)
        return completed(
            "notice\n"
            + json.dumps(
                [
                    {
                        "file": (
                            f"qmd://{QMD_COLLECTION}/memory/evt-morning-preference.md"
                            f"?index={QMD_INDEX}"
                        ),
                        "score": 0.91,
                    }
                ]
            )
        )

    candidates = QmdCandidateProvider(
        binary, config_dir=config, cache_dir=cache, runner=runner
    ).discover("How do mornings work?")
    assert candidates[0].source_path == "memory/evt-morning-preference.md"
    assert calls[1][0][1:] == [
        "--index",
        QMD_INDEX,
        "vsearch",
        "How do mornings work?",
        "-c",
        QMD_COLLECTION,
        "-n",
        "5",
        "--format",
        "json",
    ]
    assert calls[1][1]["env"]["QMD_CONFIG_DIR"] == str(config.resolve())  # type: ignore[index]


def test_qmd_provider_rejects_foreign_collection_candidates(tmp_path: Path) -> None:
    binary = tmp_path / "qmd.cmd"
    binary.touch()

    def runner(args: list[str], **_: object) -> subprocess.CompletedProcess[str]:
        if args[-1] == "--version":
            return completed(QMD_EXPECTED_VERSION)
        return completed('[{"file":"qmd://private-memory/secret.md","score":1}]')

    provider = QmdCandidateProvider(binary, runner=runner)
    with pytest.raises(ValueError, match="escaped"):
        provider.discover("Find a family preference")


def test_qmd_provider_rejects_an_unexpected_named_index(tmp_path: Path) -> None:
    binary = tmp_path / "qmd.cmd"
    binary.touch()

    def runner(args: list[str], **_: object) -> subprocess.CompletedProcess[str]:
        if args[-1] == "--version":
            return completed(QMD_EXPECTED_VERSION)
        return completed(
            f'['
            f'{{"file":"qmd://{QMD_COLLECTION}/memory/evt-morning-preference.md'
            f'?index=private","score":1}}'
            f']'
        )

    provider = QmdCandidateProvider(binary, runner=runner)
    with pytest.raises(ValueError, match="unexpected index"):
        provider.discover("Find a family preference")


def test_qmd_provider_rejects_unbounded_queries(tmp_path: Path) -> None:
    binary = tmp_path / "qmd.cmd"
    binary.touch()
    provider = QmdCandidateProvider(binary)
    with pytest.raises(ValueError, match="between 1 and 500"):
        provider.discover("x" * 501)


def test_manifest_and_projection_bind_every_fictional_event() -> None:
    manifest = load_verified_manifest(MANIFEST, CORPUS)
    memory = MicroMemory.load_jsonl(FIXTURE)
    for event in memory.events:
        record = manifest.record_for(f"memory/{event.event_id}.md")
        assert record is not None
        assert (CORPUS / record.source_path).read_bytes() == render_event_markdown(event)


def test_retriever_returns_only_current_authoritative_memory() -> None:
    provider = StubProvider(
        (
            QmdCandidate("memory/evt-morning-preference.md", 0.91, 1),
            QmdCandidate("memory/evt-school-form-prepare.md", 0.41, 2),
        )
    )
    result = retriever(provider).search(
        "When should routine updates begin?", MicroMemory.load_jsonl(FIXTURE), NOW
    )
    public = result.public_dict()
    assert result.state == "found"
    assert public["results"] == [
        {
            "kind": "preference",
            "value": "Do not send routine household updates before 8:00 AM.",
            "source": "fictional_owner",
            "recorded_at": "2026-08-21T12:02:00+00:00",
        }
    ]
    assert "score" not in json.dumps(public)
    assert "qmd://" not in json.dumps(public)
    assert "event_id" not in json.dumps(public)


def test_retriever_rejects_a_superseded_candidate() -> None:
    memory = MicroMemory.load_jsonl(FIXTURE)
    memory.append(
        MemoryEvent(
            event_id="outcome:evt-school-form-sign",
            kind=MemoryKind.OUTCOME,
            subject="school_form",
            value="Approved by the fictional household owner.",
            recorded_at=NOW,
            source="owner_decision",
            supersedes="evt-school-form-sign",
        )
    )
    provider = StubProvider((QmdCandidate("memory/evt-school-form-sign.md", 1.0, 1),))
    result = retriever(provider).search("What needs approval?", memory, NOW)
    assert result.state == "no_match"
    assert result.hits == ()


def test_retriever_fails_safe_when_projection_changes(tmp_path: Path) -> None:
    copied = tmp_path / "corpus"
    shutil.copytree(CORPUS, copied)
    manifest = load_verified_manifest(MANIFEST, copied)
    (copied / "memory" / "evt-morning-preference.md").write_text("changed")
    provider = StubProvider(
        (QmdCandidate("memory/evt-morning-preference.md", 0.91, 1),)
    )
    result = QmdMemoryRetriever(provider, manifest).search(  # type: ignore[arg-type]
        "When do updates start?", MicroMemory.load_jsonl(FIXTURE), NOW
    )
    assert result.state == "unavailable"
    assert result.hits == ()


def test_retriever_fails_safe_when_qmd_is_absent() -> None:
    result = retriever(StubProvider(error=OSError("offline"))).search(
        "When do updates start?", MicroMemory.load_jsonl(FIXTURE), NOW
    )
    assert result.state == "unavailable"
    assert result.hits == ()
