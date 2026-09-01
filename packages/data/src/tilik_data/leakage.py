"""Leakage probe, and the identifier scrub that has to pass it.

The probe trains a deliberately trivial classifier on features that carry **no clinical or
billing information whatsoever** — the bundle's own identifier and its position in the
serialisation order. If that succeeds, the corpus has a tell: injected records are distinguishable
by their names or their ordering, and every downstream metric is measuring bookkeeping.

**A high score here is an alarm, not a pass.** `docs/canonical/04_data_card.md` is explicit that
evaluation halts until it is explained. Reporting an impressive F1 from a leaking corpus would be
worse than reporting nothing, because it would be believed.

The scrub below is what the probe is checking. It rewrites **every** identifier the injectors
marked — not only the bundle's own, because the same suffix is stamped onto the claim, its lines,
and any new encounter. Renaming the bundle alone leaves `CLM-00008-U798` sitting inside it,
which is the identical tell one level down and is not visible to a probe that only reads
bundle ids.
"""
from __future__ import annotations

import hashlib
import re
from collections.abc import Iterator, Mapping
from dataclasses import dataclass

from tilik_domain.canonical import CanonicalBundle

from tilik_data.injectors.labels import LabelSet

CHANCE_TOLERANCE = 0.10
"""How far above chance the probe may score before it counts as a leak.

Ten points is generous for a probe with no real signal available; anything beyond it means the
identifiers themselves are predictive.
"""

ID_DIGEST_LENGTH = 12
"""Characters of SHA-256 kept in a regenerated identifier.

Long enough that a collision across a corpus of this scale is not a practical concern, and
`injector_free_ids` raises rather than silently merging two resources if one ever happens.
"""

INJECTOR_SUFFIX = re.compile(r"-[A-Z]\d{3}(?=-|$)")
"""What an injector appends: `BND-00042-R173`, `LN-00042-1-U798`, `CLM-00786-R266-U513`.

Clean identifiers only ever put digits after a hyphen, so a letter in that position is the
injector's signature and nothing else.
"""

IDENTIFIER = re.compile(r"^[A-Z]+(?:-[A-Za-z0-9]+)+$")
"""The shape of an identifier, so free text that happens to contain a code is left alone."""


@dataclass(frozen=True)
class LeakageReport:
    accuracy: float
    baseline: float
    """Accuracy from always predicting the majority class — the chance level to beat."""
    margin: float
    leaked: bool
    feature_names: tuple[str, ...]

    def summary(self) -> str:
        verdict = "LEAK — halt evaluation" if self.leaked else "no leak detected"
        return (
            f"probe accuracy {self.accuracy:.3f} vs baseline {self.baseline:.3f} "
            f"(margin {self.margin:+.3f}) → {verdict}"
        )


def probe(
    bundles: tuple[CanonicalBundle, ...],
    injected_ids: frozenset[str],
    *,
    tolerance: float = CHANCE_TOLERANCE,
) -> LeakageReport:
    """Try to predict "was this injected?" from identifiers and ordering alone.

    Uses a decision stump over id-derived numbers rather than a strong learner on purpose: the
    question is whether the answer is *trivially* recoverable, not whether some model somewhere
    could recover it.
    """
    if not bundles:
        return LeakageReport(0.0, 0.0, 0.0, False, ())

    rows = [
        (
            float(position),
            float(len(bundle.bundle_id)),
            float(sum(ord(character) for character in bundle.bundle_id) % 1000),
            bundle.bundle_id in injected_ids,
        )
        for position, bundle in enumerate(bundles)
    ]
    labels = [row[3] for row in rows]
    positives = sum(labels)
    baseline = max(positives, len(labels) - positives) / len(labels)

    best = baseline
    for feature_index in range(3):
        values = sorted({row[feature_index] for row in rows})
        # A handful of candidate thresholds is enough to reveal a trivially separable corpus.
        for threshold in values[:: max(1, len(values) // 32)]:
            for polarity in (True, False):
                correct = sum(
                    1
                    for row in rows
                    if ((row[feature_index] <= threshold) == polarity) == row[3]
                )
                best = max(best, correct / len(rows))

    margin = best - baseline
    return LeakageReport(
        accuracy=best,
        baseline=baseline,
        margin=margin,
        leaked=margin > tolerance,
        feature_names=("serialisation_position", "id_length", "id_character_sum"),
    )


def reidentify(original: str, seed: int) -> str:
    """Replace an identifier's body with an opaque, seed-derived digest, keeping its prefix.

    The prefix stays so a reader can still tell a claim from a line; everything that carried
    ordering or injector information does not.
    """
    prefix = original.split("-", 1)[0]
    digest = hashlib.sha256(f"{seed}:{original}".encode()).hexdigest()[:ID_DIGEST_LENGTH]
    return f"{prefix}-{digest}"


def carries_injector_suffix(value: str) -> bool:
    """True for an identifier an injector stamped, false for free text that merely looks close."""
    return bool(IDENTIFIER.match(value) and INJECTOR_SUFFIX.search(value))


def injector_free_ids(bundles: tuple[CanonicalBundle, ...], seed: int) -> dict[str, str]:
    """The full rename applied when traces are stripped: old identifier → published identifier.

    Two kinds of identifier are rewritten. Every `bundle_id`, so serialisation order and the
    original ordinal carry nothing. And every identifier anywhere inside a bundle that an
    injector marked — the claim, its lines, a new encounter — because those announce the answer
    just as loudly as the bundle id does.

    Returned as a map rather than applied in place so labels and any other artifact can be
    carried through the *same* rename instead of recomputing it and drifting.
    """
    renaming: dict[str, str] = {}
    for bundle in bundles:
        for original in (bundle.bundle_id, *_marked_identifiers(bundle.model_dump())):
            renaming.setdefault(original, reidentify(original, seed))

    _refuse_collisions(renaming)
    return renaming


def rename_labels(labels: LabelSet, renaming: Mapping[str, str]) -> LabelSet:
    """Carry a rename through the ground truth, so labels still join to the published corpus.

    Without this the labels name records that no longer exist under those names, and nothing
    downstream can score anything: the answer key would be written in a different alphabet from
    the exam.
    """

    def renamed(identifier: str) -> str:
        return renaming.get(identifier, identifier)

    return labels.model_copy(
        update={
            "labels": tuple(
                label.model_copy(
                    update={
                        "source_bundle_id": renamed(label.source_bundle_id),
                        "target_bundle_ids": tuple(
                            renamed(target) for target in label.target_bundle_ids
                        ),
                        "expected_evidence_refs": tuple(
                            ref.model_copy(update={"resource_id": renamed(ref.resource_id)})
                            for ref in label.expected_evidence_refs
                        ),
                    }
                )
                for label in labels.labels
            )
        }
    )


def strip_injector_traces(
    bundles: tuple[CanonicalBundle, ...], seed: int
) -> tuple[CanonicalBundle, ...]:
    """Remove what the injectors left behind: marked identifiers and injection-order grouping.

    Injected bundles arrive with ids like `BND-00042-R173`, which announces both that a record
    was injected and which injector did it — and the same suffix is stamped on the claim and its
    lines. Regenerating those identifiers and reordering the corpus removes the tell; the probe
    then confirms it is actually gone rather than assuming it.
    """
    renaming = injector_free_ids(bundles, seed)
    renamed = [
        CanonicalBundle.model_validate(_rewrite(bundle.model_dump(), renaming))
        for bundle in bundles
    ]

    # Order by the regenerated id, so serialisation order carries no injection information.
    return tuple(sorted(renamed, key=lambda bundle: bundle.bundle_id))


def _marked_identifiers(node: object) -> Iterator[str]:
    """Every injector-marked identifier anywhere in a dumped bundle."""
    if isinstance(node, dict):
        for value in node.values():
            yield from _marked_identifiers(value)
    elif isinstance(node, list | tuple):
        for item in node:
            yield from _marked_identifiers(item)
    elif isinstance(node, str) and carries_injector_suffix(node):
        yield node


def _rewrite(node: object, renaming: Mapping[str, str]) -> object:
    """Substitute whole identifiers throughout a dumped bundle, leaving everything else alone.

    Whole-string only. A partial replacement inside free text would edit a clinical note, and a
    note the generator wrote is content, not an identifier.
    """
    if isinstance(node, dict):
        return {key: _rewrite(value, renaming) for key, value in node.items()}
    if isinstance(node, list | tuple):
        return [_rewrite(item, renaming) for item in node]
    if isinstance(node, str):
        return renaming.get(node, node)
    return node


def _refuse_collisions(renaming: Mapping[str, str]) -> None:
    """Raise if two identifiers were about to become one.

    Silently merging two resources would corrupt the corpus in a way no later test could name,
    so the digest length is treated as a checked assumption rather than a safe one.
    """
    published: dict[str, str] = {}
    for original, replacement in renaming.items():
        clash = published.get(replacement)
        if clash is not None:
            raise RuntimeError(
                f"identifier collision: {original!r} and {clash!r} both map to {replacement!r}"
            )
        published[replacement] = original
