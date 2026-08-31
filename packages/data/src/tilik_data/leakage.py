"""Leakage probe: prove the corpus is not answerable from identifiers alone.

The probe trains a deliberately trivial classifier on features that carry **no clinical or
billing information whatsoever** — the bundle's own identifier and its position in the
serialisation order. If that succeeds, the corpus has a tell: injected records are distinguishable
by their names or their ordering, and every downstream metric is measuring bookkeeping.

**A high score here is an alarm, not a pass.** `docs/canonical/04_data_card.md` is explicit that
evaluation halts until it is explained. Reporting an impressive F1 from a leaking corpus would be
worse than reporting nothing, because it would be believed.
"""
from __future__ import annotations

from dataclasses import dataclass

from tilik_domain.canonical import CanonicalBundle

CHANCE_TOLERANCE = 0.10
"""How far above chance the probe may score before it counts as a leak.

Ten points is generous for a probe with no real signal available; anything beyond it means the
identifiers themselves are predictive.
"""


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


def strip_injector_traces(
    bundles: tuple[CanonicalBundle, ...], seed: int
) -> tuple[CanonicalBundle, ...]:
    """Remove what the injectors left behind: suffixed ids and injection-order grouping.

    Injected bundles arrive with ids like `BND-00042-R173`, which announces both that a record
    was injected and which injector did it. Regenerating identifiers and reordering the corpus
    removes the tell; the probe then confirms it is actually gone rather than assuming it.
    """
    import hashlib

    renamed = []
    for bundle in bundles:
        digest = hashlib.sha256(f"{seed}:{bundle.bundle_id}".encode()).hexdigest()[:12]
        renamed.append(bundle.model_copy(update={"bundle_id": f"BND-{digest}"}))

    # Order by the regenerated id, so serialisation order carries no injection information.
    return tuple(sorted(renamed, key=lambda bundle: bundle.bundle_id))
