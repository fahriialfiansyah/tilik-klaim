"""The four baselines from `docs/canonical/06_evaluation_plan.md` § Baselines.

Every bundle is screened **once**, and all four baselines are derived from that one outcome.
Screening it four times would make the latency figures meaningless and would let the baselines
drift apart on details that have nothing to do with what distinguishes them.

| Baseline | Flags when | Ranks by | Mode |
|---|---|---|---|
| B0 random | its draw is in the top *n*, *n* being what B1 flagged | a seeded random draw | no |
| B1 rules only | any rule reason fired | the rules band | yes |
| B2 statistical only | similarity or anomaly clears its threshold | the higher of the two | no |
| Hybrid | the aggregated band is above no-observed-risk | band, then score within it | yes |

**B0 is matched to B1's workload on purpose.** A random baseline that flags everything would
have perfect recall and useless precision; one that flags nothing would have the reverse. Giving
it exactly as many flags as the rules baseline spends makes the comparison about *which* cases
each picks, which is the only question worth asking of a ranker.
"""
from __future__ import annotations

import hashlib
import time
from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum

from tilik_domain.canonical import CanonicalBundle, ResourceType
from tilik_domain.reasons import PriorityBand, ReasonCode, RiskMode
from tilik_model.dataset import ClaimContext
from tilik_model.ranking import Certainty, RankingModel, ReasonSummary, combine

from app.service.screening import Certainty as EngineCertainty
from app.service.screening import screen_bundle
from runner.metrics import Prediction

BAND_RANK: dict[PriorityBand, int] = {
    PriorityBand.NO_OBSERVED_RISK: 0,
    PriorityBand.NEEDS_CONTEXT: 1,
    PriorityBand.HIGH_PRIORITY_SIGNAL: 2,
    PriorityBand.DETERMINISTIC_CONFLICT: 3,
}

WITHIN_BAND_WEIGHT = 0.999
"""How much a continuous score may move a case *within* its band, never across one.

Strictly below 1.0 so a band boundary is never crossed by a tiebreak — the band is a claim the
system makes about a case, and a ranking that quietly reordered across it would contradict the
band shown on screen.
"""

MILLISECONDS = 1000.0


class BaselineId(StrEnum):
    """Named exactly as `app.dto.evaluations.BaselineMetrics.baseline` documents them."""

    B0_RANDOM = "B0_RANDOM"
    B1_RULES_ONLY = "B1_RULES_ONLY"
    B2_STATISTICAL_ONLY = "B2_STATISTICAL_ONLY"
    HYBRID = "HYBRID"


@dataclass(frozen=True)
class ScreeningOutcome:
    """One bundle, screened once. Everything the four baselines need, and nothing else."""

    bundle_id: str
    provider_id: str
    rules_band: PriorityBand
    hybrid_band: PriorityBand
    reason_modes: frozenset[RiskMode]
    reason_codes: frozenset[ReasonCode]
    certainty: Certainty
    similarity_score: float
    anomaly_score: float
    similarity_band: PriorityBand
    anomaly_band: PriorityBand
    evidence_refs_total: int
    evidence_refs_resolved: int
    billed_line_count: int
    unsupported_line_count: int
    latency_ms: float

    @property
    def flagged_by_rules(self) -> bool:
        return self.rules_band is not PriorityBand.NO_OBSERVED_RISK

    @property
    def flagged_by_statistics(self) -> bool:
        return (
            self.similarity_band is not PriorityBand.NO_OBSERVED_RISK
            or self.anomaly_band is not PriorityBand.NO_OBSERVED_RISK
        )

    @property
    def flagged_by_hybrid(self) -> bool:
        return self.hybrid_band is not PriorityBand.NO_OBSERVED_RISK


def screen_all(
    bundles: Sequence[CanonicalBundle],
    contexts: dict[str, ClaimContext],
    model: RankingModel,
) -> tuple[ScreeningOutcome, ...]:
    """Run the engine and the model once per bundle, timing the screening itself."""
    return tuple(_screen_one(bundle, contexts.get(bundle.bundle_id), model) for bundle in bundles)


def _screen_one(
    bundle: CanonicalBundle, context: ClaimContext | None, model: RankingModel
) -> ScreeningOutcome:
    context = context or ClaimContext()

    started = time.perf_counter()
    result = screen_bundle(bundle, context.history, context.peer_documents)
    elapsed_ms = (time.perf_counter() - started) * MILLISECONDS

    reasons = ReasonSummary(
        has_any_reason=bool(result.reasons),
        has_deterministic_reason=any(reason.deterministic for reason in result.reasons),
        is_similarity_only=bool(result.reasons)
        and all(
            reason.code is ReasonCode.NEAR_DUPLICATE_DOCUMENTATION for reason in result.reasons
        ),
        has_exact_duplicate_fingerprint=any(
            reason.code is ReasonCode.DUPLICATE_CLAIM_FINGERPRINT for reason in result.reasons
        ),
    )
    certainty = (
        Certainty.REDUCED_INCOMPLETE_BUNDLE
        if result.certainty is EngineCertainty.REDUCED_INCOMPLETE_BUNDLE
        else Certainty.FULL
    )

    similarity = model.similarity.score(bundle.documents, context.peer_documents).value
    anomaly = model.anomaly.score(
        model.extractor.extract(bundle, context.history, context.peer_documents)
    ).value
    ranked = combine(
        bundle_id=bundle.bundle_id,
        reasons=reasons,
        similarity_score=similarity,
        anomaly_score=anomaly,
        similarity_calibration=model.similarity_calibration,
        anomaly_calibration=model.anomaly_calibration,
        certainty=certainty,
        identity=model.identity,
    )

    total, resolved = _evidence_validity(bundle, context, result.reasons)
    index = bundle.resource_index()
    return ScreeningOutcome(
        bundle_id=bundle.bundle_id,
        provider_id=bundle.claim.provider_id,
        rules_band=result.band,
        hybrid_band=ranked.band,
        reason_modes=frozenset(reason.mode for reason in result.reasons),
        reason_codes=frozenset(reason.code for reason in result.reasons),
        certainty=certainty,
        similarity_score=similarity,
        anomaly_score=anomaly,
        similarity_band=ranked.similarity_band,
        anomaly_band=ranked.anomaly_band,
        evidence_refs_total=total,
        evidence_refs_resolved=resolved,
        billed_line_count=len(bundle.lines),
        unsupported_line_count=sum(
            1
            for line in bundle.lines
            if not any(ref.key() in index for ref in line.supporting_refs)
        ),
        latency_ms=elapsed_ms,
    )


def _evidence_validity(
    bundle: CanonicalBundle, context: ClaimContext, reasons
) -> tuple[int, int]:
    """How many displayed evidence references resolve to a resource that actually exists.

    The search covers everything the reviewer can actually open, which is wider than the bundle:

    * **history**, because a repeat-billing reason points at the earlier claim;
    * **peer documents**, because cloning is a facility-level pattern across *different*
      participants, so the matched note is by definition in someone else's bundle.

    Leaving peer documents out reports a working clone detector as producing broken references —
    on this corpus, 39 of 140 — and the obvious response to that number would be to "fix" a
    detector that was right.
    """
    index = dict(bundle.resource_index())
    for past in context.history:
        index.update(past.resource_index())
    for document in context.peer_documents:
        index[(ResourceType.DOCUMENT, document.document_id)] = document

    total = resolved = 0
    for reason in reasons:
        for ref in reason.evidence:
            total += 1
            resolved += int(ref.key() in index)
    return total, resolved


def predictions_for(
    baseline: BaselineId, outcomes: Sequence[ScreeningOutcome], *, seed: int
) -> tuple[Prediction, ...]:
    """Turn one screening pass into the predictions of one baseline."""
    if baseline is BaselineId.B0_RANDOM:
        return _random_predictions(outcomes, seed=seed)
    if baseline is BaselineId.B1_RULES_ONLY:
        return tuple(
            Prediction(
                bundle_id=outcome.bundle_id,
                flagged=outcome.flagged_by_rules,
                modes=outcome.reason_modes,
                score=float(BAND_RANK[outcome.rules_band]),
                attributes_modes=True,
            )
            for outcome in outcomes
        )
    if baseline is BaselineId.B2_STATISTICAL_ONLY:
        return tuple(
            Prediction(
                bundle_id=outcome.bundle_id,
                flagged=outcome.flagged_by_statistics,
                modes=frozenset(),
                score=max(outcome.similarity_score, outcome.anomaly_score),
                attributes_modes=False,
            )
            for outcome in outcomes
        )
    return tuple(
        Prediction(
            bundle_id=outcome.bundle_id,
            flagged=outcome.flagged_by_hybrid,
            modes=outcome.reason_modes,
            score=BAND_RANK[outcome.hybrid_band]
            + WITHIN_BAND_WEIGHT
            * max(outcome.similarity_score, outcome.anomaly_score),
            attributes_modes=True,
        )
        for outcome in outcomes
    )


def _random_predictions(
    outcomes: Sequence[ScreeningOutcome], *, seed: int
) -> tuple[Prediction, ...]:
    """A seeded random ordering, flagging as many cases as the rules baseline flagged.

    Seeded from the bundle identifier rather than drawn from a stream, so the draw does not
    depend on iteration order and a re-run reproduces it exactly.
    """
    scored = sorted(
        ((_uniform(seed, outcome.bundle_id), outcome) for outcome in outcomes),
        key=lambda pair: (-pair[0], pair[1].bundle_id),
    )
    budget = sum(1 for outcome in outcomes if outcome.flagged_by_rules)
    flagged = {outcome.bundle_id for _, outcome in scored[:budget]}
    return tuple(
        Prediction(
            bundle_id=outcome.bundle_id,
            flagged=outcome.bundle_id in flagged,
            modes=frozenset(),
            score=score,
            attributes_modes=False,
        )
        for score, outcome in scored
    )


def _uniform(seed: int, bundle_id: str) -> float:
    """A deterministic draw in [0, 1) from a seed and an identifier."""
    digest = hashlib.sha256(f"{seed}:{bundle_id}".encode()).digest()
    return int.from_bytes(digest[:8], "big") / float(1 << 64)
