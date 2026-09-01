"""Load a published corpus and hand each bundle the context a detector is allowed to see.

Two scoping rules are carried over from the rules layer, and getting them backwards would
change what the model measures:

* **History is per participant, per facility.** Repeat billing and unbundling are patterns in
  one person's care at one place, so history is that person's earlier claims there — and only
  the earlier ones, so a claim never sees its own future.
* **Cloning crosses participants.** A cloned note is a facility-level pattern, so peer documents
  are notes filed at the same facility for *other* participants. Notes cross that boundary;
  whole bundles never do.

The loader refuses artifacts that do not join. Until Sprint 05 the published corpus, split, and
labels shared no identifiers at all, and nothing noticed because nothing had tried to read them
together. A loader that accepts unjoinable inputs turns that into a silent wrong answer.
"""
from __future__ import annotations

import json
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path

from tilik_domain.canonical import CanonicalBundle, DocumentRef

TRAIN, VALIDATION, TEST = "train", "validation", "test"
PARTITIONS: tuple[str, ...] = (TRAIN, VALIDATION, TEST)


class ArtifactsDoNotJoin(RuntimeError):
    """The corpus, split, and labels do not share one identifier space."""


@dataclass(frozen=True)
class ClaimContext:
    """Everything one bundle's features may look at beyond the bundle itself."""

    history: tuple[CanonicalBundle, ...] = ()
    peer_documents: tuple[DocumentRef, ...] = ()


@dataclass(frozen=True)
class BuildArtifacts:
    """One generation run, loaded from disk and checked for internal consistency."""

    bundles: tuple[CanonicalBundle, ...]
    partitions: dict[str, frozenset[str]]
    excluded_demo: frozenset[str]
    labelled_bundle_ids: frozenset[str]
    manifest: dict

    def by_id(self) -> dict[str, CanonicalBundle]:
        return {bundle.bundle_id: bundle for bundle in self.bundles}

    def partition(self, name: str) -> tuple[CanonicalBundle, ...]:
        members = self.partitions[name]
        return tuple(bundle for bundle in self.bundles if bundle.bundle_id in members)

    def dataset_digest(self) -> str:
        return str(self.manifest.get("corpus_hash", "unset"))


def load_build(directory: Path) -> BuildArtifacts:
    """Read the four published files, then refuse them unless they share one id space."""
    corpus = json.loads((directory / "corpus.json").read_text(encoding="utf-8"))
    split = json.loads((directory / "split.json").read_text(encoding="utf-8"))
    labels = json.loads((directory / "labels.json").read_text(encoding="utf-8"))
    manifest = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))

    bundles = tuple(CanonicalBundle.model_validate(raw) for raw in corpus)
    artifacts = BuildArtifacts(
        bundles=bundles,
        partitions={name: frozenset(split[name]) for name in PARTITIONS},
        excluded_demo=frozenset(split.get("excluded_demo", ())),
        labelled_bundle_ids=frozenset(
            bundle_id for label in labels["labels"] for bundle_id in label["target_bundle_ids"]
        ),
        manifest=manifest,
    )
    assert_artifacts_join(artifacts)
    return artifacts


def assert_artifacts_join(artifacts: BuildArtifacts) -> None:
    """Raise unless the split and the labels both name records the corpus actually contains."""
    published = {bundle.bundle_id for bundle in artifacts.bundles}
    partitioned = frozenset().union(*artifacts.partitions.values())

    orphaned_split = partitioned - published
    if orphaned_split:
        raise ArtifactsDoNotJoin(
            f"{len(orphaned_split)} split ids are absent from the corpus, e.g. "
            f"{sorted(orphaned_split)[:3]}"
        )
    orphaned_labels = artifacts.labelled_bundle_ids - published
    if orphaned_labels:
        raise ArtifactsDoNotJoin(
            f"{len(orphaned_labels)} labelled ids are absent from the corpus, e.g. "
            f"{sorted(orphaned_labels)[:3]}"
        )
    unaccounted = published - partitioned - artifacts.excluded_demo
    if unaccounted:
        raise ArtifactsDoNotJoin(
            f"{len(unaccounted)} published bundles belong to no partition, e.g. "
            f"{sorted(unaccounted)[:3]}"
        )


def build_contexts(bundles: Sequence[CanonicalBundle]) -> dict[str, ClaimContext]:
    """History and peer notes for every bundle, scoped by the two rules in the module docstring."""
    by_participant_provider: dict[tuple[str, str], list[CanonicalBundle]] = {}
    documents_by_provider: dict[str, list[tuple[str, DocumentRef]]] = {}
    for bundle in bundles:
        claim = bundle.claim
        by_participant_provider.setdefault((claim.participant_id, claim.provider_id), []).append(
            bundle
        )
        for document in bundle.documents:
            documents_by_provider.setdefault(claim.provider_id, []).append(
                (claim.participant_id, document)
            )

    contexts: dict[str, ClaimContext] = {}
    for bundle in bundles:
        claim = bundle.claim
        siblings = by_participant_provider[(claim.participant_id, claim.provider_id)]
        contexts[bundle.bundle_id] = ClaimContext(
            history=tuple(
                other
                for other in siblings
                if other.bundle_id != bundle.bundle_id
                and other.claim.submitted_at <= claim.submitted_at
            ),
            peer_documents=tuple(
                document
                for participant_id, document in documents_by_provider.get(claim.provider_id, ())
                if participant_id != claim.participant_id
            ),
        )
    return contexts


def participants_of(bundles: Iterable[CanonicalBundle]) -> frozenset[str]:
    return frozenset(bundle.claim.participant_id for bundle in bundles)


def uncontaminated_training_bundles(
    artifacts: BuildArtifacts,
) -> tuple[tuple[CanonicalBundle, ...], tuple[str, ...]]:
    """Training rows, with every bundle whose participant also appears downstream removed.

    The published split groups by `(participant, facility, time block)`, so one participant can
    legitimately appear in two partitions — at a different facility, or a different month. That
    is fine for the corpus and is *not* fine for fitting: a model that has seen a participant's
    January claim has seen most of what makes their February claim predictable.

    Rather than re-cutting a split that was announced as frozen, the contamination is removed
    here, on the training side only, and the number of dropped rows is returned so it can be
    reported instead of disappearing.
    """
    downstream = participants_of(artifacts.partition(VALIDATION)) | participants_of(
        artifacts.partition(TEST)
    )
    training = artifacts.partition(TRAIN)
    kept = tuple(
        bundle for bundle in training if bundle.claim.participant_id not in downstream
    )
    dropped = tuple(
        bundle.bundle_id for bundle in training if bundle.claim.participant_id in downstream
    )
    return kept, dropped
