"""Grouped train/validation/test split.

**Never a random row split.** Claims for one participant, and claims at one provider inside one
time block, are related: an evaluation that put a participant's January claim in train and their
February claim in test would be scoring a model that has already seen the answer in a
near-identical record. The reported number would be real arithmetic on a meaningless comparison.

So the split is by *group*, and the group key is `(participant, provider-time-block)`. Groups are
assigned whole. A group never straddles a boundary, and `test_split.py` asserts it.

The five gold demo fixtures are excluded from every partition. They exist to be shown to judges,
which means they are the records most likely to have been looked at while tuning — precisely the
records that must not contribute to a metric.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime

from tilik_domain.canonical import CanonicalBundle

GOLD_BUNDLE_IDS: frozenset[str] = frozenset(
    {"BND-CLEAN", "BND-PHANTOM", "BND-REPEAT", "BND-CLONE", "BND-UNBUNDLED"}
)
"""The demo fixtures. Kept out of every metric set — see the module docstring."""

TRAIN, VALIDATION, TEST = "train", "validation", "test"


@dataclass(frozen=True)
class SplitRatios:
    train: float = 0.6
    validation: float = 0.2
    test: float = 0.2

    def __post_init__(self) -> None:
        total = self.train + self.validation + self.test
        if abs(total - 1.0) > 1e-9:
            raise ValueError(f"split ratios must sum to 1.0, got {total}")


@dataclass(frozen=True)
class Split:
    """Which bundle ids belong to each partition, plus the excluded demo fixtures."""

    train: frozenset[str]
    validation: frozenset[str]
    test: frozenset[str]
    excluded_demo: frozenset[str]
    frozen_at: str
    """A digest of the test partition, so a later change to it is detectable rather than silent."""

    def partition_of(self, bundle_id: str) -> str | None:
        for name, members in (
            (TRAIN, self.train), (VALIDATION, self.validation), (TEST, self.test)
        ):
            if bundle_id in members:
                return name
        return None

    def all_partitioned(self) -> frozenset[str]:
        return self.train | self.validation | self.test


def provider_time_block(submitted_at: datetime, block_days: int) -> int:
    """Which time block a claim falls in, counted from the epoch in whole blocks."""
    return int(submitted_at.timestamp() // (block_days * 86_400))


def group_key(bundle: CanonicalBundle, block_days: int) -> str:
    """The unit that moves between partitions as a whole."""
    block = provider_time_block(bundle.claim.submitted_at, block_days)
    return f"{bundle.claim.participant_id}|{bundle.claim.provider_id}|{block}"


def make_split(
    bundles: tuple[CanonicalBundle, ...],
    *,
    ratios: SplitRatios | None = None,
    block_days: int = 30,
    seed: int = 0,
) -> Split:
    """Assign whole groups to partitions, deterministically.

    Assignment hashes the group key with the seed rather than shuffling, so a group lands in the
    same partition regardless of corpus size or ordering. Adding records cannot silently move an
    existing group across a boundary and invalidate an earlier measurement.
    """
    ratios = ratios or SplitRatios()

    groups: dict[str, list[str]] = {}
    excluded: set[str] = set()
    for bundle in bundles:
        if bundle.bundle_id in GOLD_BUNDLE_IDS:
            excluded.add(bundle.bundle_id)
            continue
        groups.setdefault(group_key(bundle, block_days), []).append(bundle.bundle_id)

    partitions: dict[str, set[str]] = {TRAIN: set(), VALIDATION: set(), TEST: set()}
    for key, members in groups.items():
        digest = hashlib.sha256(f"{seed}:{key}".encode()).digest()
        position = int.from_bytes(digest[:8], "big") / float(1 << 64)
        if position < ratios.train:
            bucket = TRAIN
        elif position < ratios.train + ratios.validation:
            bucket = VALIDATION
        else:
            bucket = TEST
        partitions[bucket].update(members)

    test_members = frozenset(partitions[TEST])
    return Split(
        train=frozenset(partitions[TRAIN]),
        validation=frozenset(partitions[VALIDATION]),
        test=test_members,
        excluded_demo=frozenset(excluded),
        frozen_at=freeze_digest(test_members),
    )


def freeze_digest(bundle_ids: frozenset[str]) -> str:
    """A digest of the test partition.

    Recorded when the split is made and re-checkable afterwards. Freezing the test set is only
    meaningful if a violation is *detectable*; a promise not to touch it is not a control.
    """
    joined = "\n".join(sorted(bundle_ids))
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()


def assert_test_set_unchanged(split: Split) -> None:
    """Raise if the test partition no longer matches the digest taken when it was frozen."""
    current = freeze_digest(split.test)
    if current != split.frozen_at:
        raise RuntimeError(
            "The frozen test set has changed since the split was made. Any metric computed "
            "against it is invalid until this is explained."
        )
