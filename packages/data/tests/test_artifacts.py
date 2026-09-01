"""What actually reaches disk.

`write_artifacts` is the only place the corpus becomes something another package can read, and
until these tests existed it was the only step in the pipeline with no test at all. That gap was
not theoretical: it published the corpus **before** `strip_injector_traces` ran, so the files
disagreed with each other and with the manifest, while the leakage probe reported a pass on a
corpus that never reached disk.

So these tests assert on the **files**, never on the in-memory result. A control that holds in
memory and fails on disk is not a control — it is a comment.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pytest
from tilik_domain.canonical import CanonicalBundle

from tilik_data.generator import corpus_hash
from tilik_data.pipeline import run, write_artifacts
from tilik_data.split import freeze_digest

SEED = 20260902

CONFIG = {
    "seed": SEED,
    "corpus": {"claims": 200, "participants": 60, "providers": 5},
    "injections": {
        "per_mode": 8,
        "multi_label_ratio": 0.05,
        "difficulty_mix": {"obvious": 0.3, "moderate": 0.5, "subtle": 0.2},
    },
    "split": {
        "train": 0.6,
        "validation": 0.2,
        "test": 0.2,
        "provider_time_block_days": 30,
    },
}

INJECTOR_TELL = re.compile(r"-[A-Z]\d{3}(?=-|$)")
"""The shape the injectors append: `BND-00042-R173`, `LN-00042-1-U798`.

It announces both that a record was injected and which injector did it — the most damaging
thing that could reach a feature table, because a model would learn the answer key instead of
the pattern.
"""


@pytest.fixture(scope="module")
def artifacts(tmp_path_factory) -> dict:
    """Run the pipeline end to end and read back exactly what a consumer would read."""
    out = tmp_path_factory.mktemp("build")
    write_artifacts(run(CONFIG), out)
    return {
        "corpus": json.loads((out / "corpus.json").read_text(encoding="utf-8")),
        "labels": json.loads((out / "labels.json").read_text(encoding="utf-8")),
        "split": json.loads((out / "split.json").read_text(encoding="utf-8")),
        "manifest": json.loads((out / "manifest.json").read_text(encoding="utf-8")),
    }


def _every_string(node: object, path: str = "") -> list[tuple[str, str]]:
    """Every string in a decoded JSON document, with the path that reached it."""
    if isinstance(node, dict):
        return [
            pair for key, value in node.items() for pair in _every_string(value, f"{path}.{key}")
        ]
    if isinstance(node, list):
        return [pair for item in node for pair in _every_string(item, path)]
    if isinstance(node, str):
        return [(path, node)]
    return []


def test_the_three_files_share_one_id_space(artifacts) -> None:
    """The defect this module exists for: the split could not be joined to the corpus at all."""
    corpus_ids = {bundle["bundle_id"] for bundle in artifacts["corpus"]}
    split = artifacts["split"]
    partitioned = set(split["train"]) | set(split["validation"]) | set(split["test"])

    assert partitioned, "the split published no ids"
    assert partitioned <= corpus_ids, (
        f"{len(partitioned - corpus_ids)} split ids are absent from the published corpus"
    )
    assert corpus_ids == partitioned | set(split["excluded_demo"]), (
        "every published bundle must be accounted for by the split"
    )


def test_labels_join_to_the_published_corpus(artifacts) -> None:
    """A label whose target does not exist cannot be scored, only guessed at."""
    corpus_ids = {bundle["bundle_id"] for bundle in artifacts["corpus"]}
    labels = artifacts["labels"]["labels"]
    assert labels, "the run published no labels"

    for label in labels:
        assert label["source_bundle_id"] in corpus_ids, label["injection_id"]
        for target in label["target_bundle_ids"]:
            assert target in corpus_ids, f"{label['injection_id']} targets missing {target}"


def test_label_evidence_points_at_resources_that_exist(artifacts) -> None:
    """The expected refs are what makes "fired for the right reason" checkable."""
    published: set[str] = set()
    for bundle in artifacts["corpus"]:
        published.add(bundle["claim"]["claim_id"])
        published.update(line["line_id"] for line in bundle["lines"])
        published.update(encounter["encounter_id"] for encounter in bundle["encounters"])
        published.update(procedure["procedure_id"] for procedure in bundle["procedures"])
        published.update(document["document_id"] for document in bundle["documents"])

    for label in artifacts["labels"]["labels"]:
        for ref in label["expected_evidence_refs"]:
            assert ref["resource_id"] in published, (
                f"{label['injection_id']} expects evidence {ref['resource_id']}, "
                "which no published bundle contains"
            )


def test_no_published_identifier_announces_an_injector(artifacts) -> None:
    """`BND-00008-U798` tells a reader the answer. It must not survive to disk — anywhere."""
    for name in ("corpus", "labels", "split"):
        offenders = [
            (path, value)
            for path, value in _every_string(artifacts[name])
            if INJECTOR_TELL.search(value)
        ]
        assert not offenders, (
            f"{name}.json publishes {len(offenders)} injector-marked identifier(s); "
            f"first few: {offenders[:5]}"
        )


def test_manifest_describes_the_corpus_that_was_written(artifacts) -> None:
    """A digest over a corpus nobody published is provenance for the wrong artifact."""
    rebuilt = tuple(CanonicalBundle.model_validate(raw) for raw in artifacts["corpus"])
    assert corpus_hash(rebuilt) == artifacts["manifest"]["corpus_hash"]
    assert artifacts["manifest"]["bundles"] == len(artifacts["corpus"])


def test_manifest_test_digest_matches_the_published_split(artifacts) -> None:
    """Freezing the test set means nothing if the digest describes a different set of ids."""
    digest = freeze_digest(frozenset(artifacts["split"]["test"]))
    assert digest == artifacts["split"]["test_set_digest"]
    assert digest == artifacts["manifest"]["test_set_digest"]


def test_published_corpus_reloads_as_canonical_bundles(artifacts) -> None:
    """The corpus is only usable downstream if it parses back into the domain type."""
    reloaded = [CanonicalBundle.model_validate(raw) for raw in artifacts["corpus"]]
    assert len(reloaded) == len(artifacts["corpus"])


def test_writing_twice_produces_identical_files(tmp_path: Path) -> None:
    """Reproducibility is the whole claim; two runs of one seed must agree byte for byte."""
    first, second = tmp_path / "a", tmp_path / "b"
    write_artifacts(run(CONFIG), first)
    write_artifacts(run(CONFIG), second)
    for name in ("corpus.json", "labels.json", "split.json", "DATA_CARD.md"):
        assert (first / name).read_bytes() == (second / name).read_bytes(), name
