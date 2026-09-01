"""The feature table: its declared schema, its imputation, and what it must never see.

Two of these are safety tests rather than correctness tests. `test_features_are_invariant_...`
is the leakage probe: it renames every identifier in a bundle and asserts the features do not
move, which is a stronger claim than "no injector field is copied into a column" — it proves no
feature can read *anything* from an identifier, including the ordinal and the injector suffix.
`test_no_feature_reads_a_demographic` holds the line the model card draws.
"""
from __future__ import annotations

import pytest
from tilik_data.leakage import reidentify
from tilik_domain.canonical import CanonicalBundle
from tilik_model.dataset import build_contexts
from tilik_model.features import (
    FEATURE_SCHEMA,
    FeatureExtractor,
    FeatureFamily,
    PeerProfile,
)

SEED = 20260902


@pytest.fixture(scope="module")
def extractor(bundles) -> FeatureExtractor:
    return FeatureExtractor(PeerProfile.fit(bundles))


def test_every_family_is_represented() -> None:
    """Six families are named in the model card; a missing one is a silent scope cut."""
    covered = {spec.family for spec in FEATURE_SCHEMA}
    assert covered == set(FeatureFamily)


def test_schema_names_are_unique_and_documented() -> None:
    names = [spec.name for spec in FEATURE_SCHEMA]
    assert len(names) == len(set(names))
    for spec in FEATURE_SCHEMA:
        assert spec.description.strip(), spec.name
        assert spec.imputation_note.strip(), spec.name


def test_row_conforms_to_the_declared_schema(extractor, bundles) -> None:
    """A feature table that does not match its schema cannot be read by anything downstream."""
    row = extractor.extract(bundles[0])
    assert len(row.values) == len(FEATURE_SCHEMA)
    assert row.names == tuple(spec.name for spec in FEATURE_SCHEMA)
    assert all(isinstance(value, float) for value in row.values)


def test_no_value_is_ever_nan_or_infinite(extractor, bundles) -> None:
    """A NaN reaching Isolation Forest is a crash or, worse, a silently dropped row."""
    import math

    for bundle in bundles[:60]:
        for name, value in zip(extractor.extract(bundle).names, extractor.extract(bundle).values):
            assert math.isfinite(value), f"{bundle.bundle_id}.{name} is {value}"


def test_an_imputed_feature_is_named_not_silently_zeroed(extractor, bundles) -> None:
    """"Missing" and "measured zero" are different facts and must not share a representation."""
    empty = bundles[0].model_copy(update={"documents": (), "procedures": (), "encounters": ()})
    row = extractor.extract(empty)
    assert row.imputed, "a bundle stripped of evidence imputed nothing, which cannot be right"
    for name in row.imputed:
        assert name in row.names


def test_features_are_invariant_to_renaming_every_identifier(bundles) -> None:
    """The leakage probe. No feature may read an identifier, so renaming must change nothing.

    `BND-00042-R173` announces which injector touched a record. A feature that read any part of
    an identifier — the suffix, the ordinal, even the length — would be learning the answer key.

    The rename is applied to the **whole corpus** and the peer profile is refitted on it, so
    every structural relation survives — the same participant is still the same participant, the
    same facility still the same facility — and only the strings differ. Renaming one bundle in
    isolation would merely make its facility unseen, which proves nothing.
    """
    renamed = tuple(_rename_everything(bundle, SEED) for bundle in bundles)
    original = FeatureExtractor(PeerProfile.fit(bundles))
    scrubbed = FeatureExtractor(PeerProfile.fit(renamed))

    contexts = build_contexts(bundles)
    renamed_contexts = build_contexts(renamed)

    for before, after in zip(bundles, renamed, strict=True):
        mine = contexts[before.bundle_id]
        theirs = renamed_contexts[after.bundle_id]
        expected = original.extract(before, mine.history, mine.peer_documents)
        actual = scrubbed.extract(after, theirs.history, theirs.peer_documents)
        assert actual.values == expected.values, (
            f"{before.bundle_id}: a feature moved when only identifiers changed"
        )
        assert actual.imputed == expected.imputed


def test_the_probe_would_catch_a_feature_that_read_an_identifier(bundles) -> None:
    """A probe that cannot fail proves nothing, so plant a leak and watch it move."""
    def reads_the_id(bundle) -> float:
        """The feature nobody may write: a number derived from an identifier's characters."""
        return float(sum(ord(character) for character in bundle.bundle_id))

    sample = bundles[:20]
    renamed = [_rename_everything(bundle, SEED) for bundle in sample]
    assert [b.bundle_id for b in renamed] != [b.bundle_id for b in sample], (
        "renaming did not change the ids, so the probe is inert"
    )
    assert [reads_the_id(b) for b in renamed] != [reads_the_id(b) for b in sample], (
        "a feature reading the identifier survived the rename, so the probe cannot detect one"
    )


def test_no_feature_reads_a_demographic() -> None:
    """The model card excludes protected characteristics; the four modes do not need them."""
    forbidden = ("age", "sex", "gender", "religion", "ethnic", "address", "region", "income")
    for spec in FEATURE_SCHEMA:
        haystack = f"{spec.name} {spec.description}".lower()
        for word in forbidden:
            assert word not in haystack, f"{spec.name} mentions {word!r}"


def test_peer_profile_handles_an_unseen_provider(extractor, bundles) -> None:
    """Cold start: a provider absent from the profile must impute, not divide by zero."""
    stranger = bundles[0].model_copy(
        update={"claim": bundles[0].claim.model_copy(update={"provider_id": "PRV-UNSEEN"})}
    )
    row = extractor.extract(stranger)
    peer_names = {spec.name for spec in FEATURE_SCHEMA if spec.family is FeatureFamily.PEER_CONTEXT}
    assert peer_names & set(row.imputed), "an unseen provider imputed no peer feature"


def test_a_bundle_with_no_lines_does_not_crash(extractor, bundles) -> None:
    """Degenerate input is data, not an exception."""
    row = extractor.extract(bundles[0].model_copy(update={"lines": ()}))
    assert len(row.values) == len(FEATURE_SCHEMA)


def _rename_everything(bundle: CanonicalBundle, seed: int) -> CanonicalBundle:
    """Rewrite every identifier-shaped string, preserving every relation between them."""
    renaming = {
        value: reidentify(value, seed)
        for value in _identifier_strings(bundle.model_dump())
    }
    return CanonicalBundle.model_validate(_substitute(bundle.model_dump(), renaming))


def _identifier_strings(node: object) -> set[str]:
    import re

    shape = re.compile(r"^[A-Z]{2,}-[A-Za-z0-9-]+$")
    if isinstance(node, dict):
        return set().union(*(_identifier_strings(v) for v in node.values())) if node else set()
    if isinstance(node, list | tuple):
        return set().union(*(_identifier_strings(v) for v in node)) if node else set()
    if isinstance(node, str) and shape.match(node):
        return {node}
    return set()


def _substitute(node: object, renaming: dict[str, str]) -> object:
    if isinstance(node, dict):
        return {key: _substitute(value, renaming) for key, value in node.items()}
    if isinstance(node, list | tuple):
        return [_substitute(item, renaming) for item in node]
    if isinstance(node, str):
        return renaming.get(node, node)
    return node
