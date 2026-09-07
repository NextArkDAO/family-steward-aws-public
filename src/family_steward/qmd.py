"""Bounded QMD discovery with Family Steward-owned memory authority."""

from __future__ import annotations

import hashlib
import json
import math
import os
import subprocess
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path, PurePosixPath
from types import MappingProxyType
from typing import Any

from family_steward.memory import MemoryEvent, MicroMemory

QMD_VERSION = "2.8.3"
QMD_BUILD = "facd35e"
QMD_EXPECTED_VERSION = f"qmd {QMD_VERSION} ({QMD_BUILD})"
QMD_COLLECTION = "family-steward-v0"
QMD_INDEX = "family-steward"
TRUSTED_MANIFEST_SHA256 = "4c8e0a92600b276f6977366c59abb20b9f83f0e84c17fb1ac35ff7a8366ff8a0"
MAX_QUERY_CHARS = 500
MAX_RESULTS = 8


@dataclass(frozen=True, slots=True)
class QmdCandidate:
    """Untrusted retrieval metadata that never crosses the browser boundary."""

    source_path: str
    score: float
    rank: int


@dataclass(frozen=True, slots=True)
class VerifiedMemoryHit:
    """Family Steward-owned memory selected from an untrusted candidate path."""

    event_id: str
    kind: str
    value: str
    source: str
    recorded_at: str

    def public_dict(self) -> dict[str, str]:
        return {
            "kind": self.kind,
            "value": self.value,
            "source": self.source,
            "recorded_at": self.recorded_at,
        }


@dataclass(frozen=True, slots=True)
class MemorySearchResult:
    state: str
    detail: str
    hits: tuple[VerifiedMemoryHit, ...]

    def public_dict(self) -> dict[str, Any]:
        return {
            "state": self.state,
            "detail": self.detail,
            "results": [hit.public_dict() for hit in self.hits],
        }


@dataclass(frozen=True, slots=True)
class _ManifestRecord:
    event_id: str
    source_path: str
    sha256: str


class _VerifiedManifest:
    __slots__ = ("_corpus_root", "_records")

    def __init__(self, corpus_root: Path, records: Mapping[str, _ManifestRecord]) -> None:
        self._corpus_root = corpus_root.resolve()
        self._records = MappingProxyType(dict(records))

    @property
    def corpus_root(self) -> Path:
        return self._corpus_root

    def record_for(self, source_path: str) -> _ManifestRecord | None:
        return self._records.get(source_path)


Runner = Callable[..., subprocess.CompletedProcess[str]]


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _parse_json_results(raw: str) -> list[dict[str, Any]]:
    positions = [0] if raw.startswith("[") else []
    positions.extend(index + 1 for index in range(len(raw)) if raw.startswith("\n[", index))
    for position in reversed(positions):
        try:
            payload = json.loads(raw[position:])
        except json.JSONDecodeError:
            continue
        if isinstance(payload, list) and all(isinstance(row, dict) for row in payload):
            return payload
    raise ValueError("QMD returned an invalid candidate packet")


def _safe_source_path(value: object) -> str:
    source = str(value or "")
    prefix = f"qmd://{QMD_COLLECTION}/"
    if not source.startswith(prefix):
        raise ValueError("QMD candidate escaped the Family Steward collection")
    relative = source[len(prefix) :]
    if "?" in relative:
        relative, query_string = relative.rsplit("?", maxsplit=1)
        if query_string != f"index={QMD_INDEX}":
            raise ValueError("QMD candidate named an unexpected index")
    path = PurePosixPath(relative)
    if path.is_absolute() or ".." in path.parts or not relative.endswith(".md"):
        raise ValueError("QMD candidate path is unsafe")
    return path.as_posix()


def render_event_markdown(event: MemoryEvent) -> bytes:
    expires = event.expires_at.isoformat() if event.expires_at else "none"
    supersedes = event.supersedes or "none"
    requires_owner = str(event.requires_owner).lower()
    text = (
        "# Fictional family memory\n\n"
        f"- Event: `{event.event_id}`\n"
        f"- Kind: `{event.kind.value}`\n"
        f"- Subject: `{event.subject}`\n"
        f"- Memory: {event.value}\n"
        f"- Source: `{event.source}`\n"
        f"- Recorded: `{event.recorded_at.isoformat()}`\n"
        f"- Expires: `{expires}`\n"
        f"- Requires owner: `{requires_owner}`\n"
        f"- Supersedes: `{supersedes}`\n"
    )
    return text.encode("utf-8")


def load_verified_manifest(manifest_path: Path, corpus_root: Path) -> _VerifiedManifest:
    raw = manifest_path.read_bytes()
    if _sha256(raw) != TRUSTED_MANIFEST_SHA256:
        raise ValueError("QMD authority manifest does not match the trusted release")
    payload = json.loads(raw)
    if set(payload) != {"collection", "records", "schema_version"}:
        raise ValueError("QMD authority manifest shape is invalid")
    if payload["collection"] != QMD_COLLECTION:
        raise ValueError("QMD authority manifest names the wrong collection")
    if payload["schema_version"] != "family-steward-qmd-authority-v0":
        raise ValueError("QMD authority manifest version is unsupported")
    if not isinstance(payload["records"], list) or not payload["records"]:
        raise ValueError("QMD authority manifest has no records")

    root = corpus_root.resolve()
    records: dict[str, _ManifestRecord] = {}
    event_ids: set[str] = set()
    for row in payload["records"]:
        if not isinstance(row, dict) or set(row) != {"event_id", "path", "sha256"}:
            raise ValueError("QMD authority record shape is invalid")
        source_path = PurePosixPath(str(row["path"]))
        if source_path.is_absolute() or ".." in source_path.parts:
            raise ValueError("QMD authority record path is unsafe")
        normalized = source_path.as_posix()
        event_id = str(row["event_id"])
        if normalized in records or event_id in event_ids:
            raise ValueError("QMD authority manifest contains a duplicate binding")
        source_file = (root / Path(*source_path.parts)).resolve()
        if root not in source_file.parents or not source_file.is_file():
            raise ValueError("QMD authority source is unavailable")
        digest = str(row["sha256"])
        if len(digest) != 64 or _sha256(source_file.read_bytes()) != digest:
            raise ValueError("QMD authority source digest does not match")
        records[normalized] = _ManifestRecord(event_id, normalized, digest)
        event_ids.add(event_id)
    return _VerifiedManifest(root, records)


def qmd_status(
    binary: str | None,
    config_dir: str | None = None,
    cache_dir: str | None = None,
) -> dict[str, str | bool]:
    if not binary:
        return {
            "name": "QMD local semantic memory",
            "state": "adapter_ready",
            "available": False,
            "detail": "The safe local memory connector is ready but detached.",
        }
    available = Path(binary).is_file() and bool(config_dir) and bool(cache_dir)
    return {
        "name": "QMD local semantic memory",
        "state": "connected" if available else "unavailable",
        "available": available,
        "detail": (
            "Aster can search the fictional family memory locally."
            if available
            else "The local memory connector is unavailable; Aster will continue safely."
        ),
    }


class QmdCandidateProvider:
    """Run one on-demand semantic query in a dedicated QMD state boundary."""

    def __init__(
        self,
        binary: Path,
        *,
        config_dir: Path | None = None,
        cache_dir: Path | None = None,
        runner: Runner = subprocess.run,
    ) -> None:
        if not binary.is_file():
            raise ValueError("QMD binary does not exist")
        if (config_dir is None) != (cache_dir is None):
            raise ValueError("QMD config and cache paths must be provided together")
        self.binary = binary.resolve()
        self.runner = runner
        self.environment = None
        if config_dir is not None and cache_dir is not None:
            if not config_dir.is_dir() or not cache_dir.is_dir():
                raise ValueError("QMD state paths do not exist")
            self.environment = dict(
                os.environ,
                QMD_CONFIG_DIR=str(config_dir.resolve()),
                XDG_CACHE_HOME=str(cache_dir.resolve()),
                QMD_EMBED_PARALLELISM="1",
            )

    def verify_version(self) -> None:
        completed = self.runner(
            [str(self.binary), "--version"],
            check=True,
            capture_output=True,
            text=True,
            timeout=10,
            env=self.environment,
        )
        if completed.stdout.strip() != QMD_EXPECTED_VERSION:
            raise RuntimeError("QMD version does not match the accepted build")

    def discover(self, query: str, *, limit: int = 5) -> tuple[QmdCandidate, ...]:
        normalized = query.strip()
        if not normalized or len(normalized) > MAX_QUERY_CHARS:
            raise ValueError("query must contain between 1 and 500 characters")
        if limit < 1 or limit > MAX_RESULTS:
            raise ValueError("limit must be between 1 and 8")
        self.verify_version()
        completed = self.runner(
            [
                str(self.binary),
                "--index",
                QMD_INDEX,
                "vsearch",
                normalized,
                "-c",
                QMD_COLLECTION,
                "-n",
                str(limit),
                "--format",
                "json",
            ],
            check=True,
            capture_output=True,
            text=True,
            timeout=45,
            env=self.environment,
        )
        rows = _parse_json_results(completed.stdout)
        if len(rows) > limit:
            raise ValueError("QMD returned too many candidates")
        candidates: list[QmdCandidate] = []
        seen: set[str] = set()
        for rank, row in enumerate(rows, start=1):
            source_path = _safe_source_path(row.get("file") or row.get("uri"))
            score = float(row.get("score", 0.0))
            if source_path in seen or not math.isfinite(score):
                raise ValueError("QMD returned invalid candidate metadata")
            seen.add(source_path)
            candidates.append(QmdCandidate(source_path, score, rank))
        return tuple(candidates)


class QmdMemoryRetriever:
    """Resolve QMD paths back to current Family Steward memory without reading snippets."""

    def __init__(self, provider: QmdCandidateProvider, manifest: _VerifiedManifest) -> None:
        if type(manifest) is not _VerifiedManifest:
            raise TypeError("QMD authority manifest must come from the trusted loader")
        self.provider = provider
        self.manifest = manifest

    def search(self, query: str, memory: MicroMemory, now: datetime) -> MemorySearchResult:
        try:
            candidates = self.provider.discover(query)
            active = {event.event_id: event for event in memory.active(now)}
            hits: list[VerifiedMemoryHit] = []
            for candidate in candidates:
                record = self.manifest.record_for(candidate.source_path)
                if record is None:
                    continue
                event = active.get(record.event_id)
                if event is None:
                    continue
                relative_parts = PurePosixPath(record.source_path).parts
                source_file = self.manifest.corpus_root / Path(*relative_parts)
                if source_file.read_bytes() != render_event_markdown(event):
                    raise ValueError("QMD projection no longer matches active memory")
                hits.append(
                    VerifiedMemoryHit(
                        event_id=event.event_id,
                        kind=event.kind.value,
                        value=event.value,
                        source=event.source,
                        recorded_at=event.recorded_at.isoformat(),
                    )
                )
                break
        except (OSError, ValueError, RuntimeError, subprocess.SubprocessError):
            return MemorySearchResult(
                "unavailable",
                "Local memory search is unavailable. Aster did not guess or expose raw results.",
                (),
            )
        if not hits:
            return MemorySearchResult(
                "no_match",
                "No current fictional family memory matched that question.",
                (),
            )
        return MemorySearchResult(
            "found",
            "Aster found current fictional family memory with its source preserved.",
            tuple(hits),
        )
