"""The one call site: combine rule reasons with the two model scores, then apply the caps.

Everything this package does arrives here. Nothing outside `packages/model` may import any other
module in it, because Sprint 05's stated outcome includes **removing** this layer: if Sprint 06
measures no incremental precision@K or recall@K over rules-only, the revert is deleting one
import, not unpicking a model from four services.

The formula is fixed by `docs/canonical/05_model_card.md` § Risk aggregation and is not a design
decision made here:

    priority = max(deterministic_reason_priority, calibrated_similarity, calibrated_anomaly)

Three caps then apply, in this order, and the order matters:

1. **The similarity ceiling** is applied to the component, not to the aggregate, so no
   combination of inputs lets text similarity lift a case into a high band. Shared forms and
   templates produce very high similarity between notes nobody copied.
2. **The duplicate-fingerprint floor** raises an exact duplicate to high priority. It is a floor
   on the queue position and nothing else — the case is still reviewed by a person.
3. **The incomplete-bundle step-down comes last**, because it is the cap that protects against a
   false accusation and must be able to override the other two. It never lowers a case below
   *needs context*: a raised case stays visible, it simply stops being urgent, and the suggested
   next step becomes *request evidence*.

`apps/backend/app/service/screening.py` applies the same three caps to the rules-only band. The
two must agree wherever both run; Sprint 06 owns that comparison, when this layer is measured.
"""
from __future__ import annotations

from collections.abc import Sequence
from enum import StrEnum

from pydantic import BaseModel, ConfigDict
from tilik_domain.canonical import CanonicalBundle
from tilik_domain.reasons import DispositionAction, PriorityBand

from tilik_model.anomaly import PeerAnomaly
from tilik_model.calibration import CALIBRATION_PARTITION, BandCalibration
from tilik_model.dataset import ClaimContext, build_contexts
from tilik_model.features import FeatureExtractor, PeerProfile
from tilik_model.similarity import NoteSimilarity
from tilik_model.version import (
    ANOMALY_VERSION,
    CALIBRATION_VERSION,
    SIMILARITY_VERSION,
    ModelIdentity,
)

SIMILARITY_ONLY_CEILING = PriorityBand.NEEDS_CONTEXT
"""The highest band text similarity may contribute. Mirrors the rules layer's own ceiling."""

DUPLICATE_FINGERPRINT_FLOOR = PriorityBand.HIGH_PRIORITY_SIGNAL
"""An exact duplicate is high priority — and still reviewed by a person."""

RULESET_PRIORITY_VERSION = "0.1.0"
"""Version of the deterministic-priority mapping below, recorded with its component score."""

_BAND_RANK: dict[PriorityBand, int] = {
    PriorityBand.NO_OBSERVED_RISK: 0,
    PriorityBand.NEEDS_CONTEXT: 1,
    PriorityBand.HIGH_PRIORITY_SIGNAL: 2,
    PriorityBand.DETERMINISTIC_CONFLICT: 3,
}

_STEP_DOWN: dict[PriorityBand, PriorityBand] = {
    PriorityBand.DETERMINISTIC_CONFLICT: PriorityBand.HIGH_PRIORITY_SIGNAL,
    PriorityBand.HIGH_PRIORITY_SIGNAL: PriorityBand.NEEDS_CONTEXT,
    PriorityBand.NEEDS_CONTEXT: PriorityBand.NEEDS_CONTEXT,
    PriorityBand.NO_OBSERVED_RISK: PriorityBand.NO_OBSERVED_RISK,
}
"""One band lower, never below "needs context" — a raised case stays visible."""


class Certainty(StrEnum):
    """How much the record itself supports acting. Mirrors `screening.Certainty`."""

    FULL = "FULL"
    REDUCED_INCOMPLETE_BUNDLE = "REDUCED_INCOMPLETE_BUNDLE"


class Cap(StrEnum):
    """Which caps actually bit, recorded so a band can be explained rather than trusted."""

    SIMILARITY_ONLY_CEILING = "SIMILARITY_ONLY_CEILING"
    DUPLICATE_FINGERPRINT_FLOOR = "DUPLICATE_FINGERPRINT_FLOOR"
    INCOMPLETE_BUNDLE_STEP_DOWN = "INCOMPLETE_BUNDLE_STEP_DOWN"


class ReasonSummary(BaseModel):
    """What the rules layer observed, reduced to the facts the combiner needs.

    Deliberately not `ReasonHit`: `packages/model` does not import `apps/backend`, so the model
    cannot reach a reason's wording, its evidence, or anything else it has no business ranking on.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    has_any_reason: bool = False
    has_deterministic_reason: bool = False
    is_similarity_only: bool = False
    has_exact_duplicate_fingerprint: bool = False


class ComponentScore(BaseModel):
    """One input to the aggregate, kept with its version so the total can be re-derived."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str
    value: float
    band: PriorityBand
    version: str


class RankedPriority(BaseModel):
    """A proposed queue position, with every component that produced it."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    bundle_id: str
    band: PriorityBand

    deterministic_band: PriorityBand
    similarity_band: PriorityBand
    anomaly_band: PriorityBand

    components: tuple[ComponentScore, ...]
    caps_applied: tuple[Cap, ...]
    certainty: Certainty
    suggested_action: DispositionAction | None
    """A suggestion for a reviewer. Never a finding, never an action on the claim."""

    explained_by_reasons: bool
    """False when only a model score raised this case, so there is no reason to show a reviewer.

    Recorded rather than suppressed: the aggregation is specified as a plain maximum, and
    quietly refusing to raise unexplained cases would be a policy this layer is not entitled to
    invent. Sprint 06 decides what to do with them → model card § Limitations.
    """

    identity: ModelIdentity = ModelIdentity()


def deterministic_priority(reasons: ReasonSummary) -> PriorityBand:
    """The band the rule reasons imply on their own, before any cap."""
    if not reasons.has_any_reason:
        return PriorityBand.NO_OBSERVED_RISK
    if reasons.has_deterministic_reason:
        return PriorityBand.DETERMINISTIC_CONFLICT
    return PriorityBand.NEEDS_CONTEXT


def combine(
    *,
    bundle_id: str,
    reasons: ReasonSummary,
    similarity_score: float,
    anomaly_score: float,
    similarity_calibration: BandCalibration,
    anomaly_calibration: BandCalibration,
    certainty: Certainty,
    identity: ModelIdentity | None = None,
) -> RankedPriority:
    """Apply the formula, then the three caps. The only place a band is decided."""
    applied: list[Cap] = []

    rule_band = deterministic_priority(reasons)

    # Cap 1 — on the component, so nothing downstream can route around it.
    raw_similarity_band = similarity_calibration.band_for(similarity_score)
    similarity_band = _at_most(raw_similarity_band, SIMILARITY_ONLY_CEILING)
    if similarity_band is not raw_similarity_band or reasons.is_similarity_only:
        applied.append(Cap.SIMILARITY_ONLY_CEILING)

    anomaly_band = anomaly_calibration.band_for(anomaly_score)

    band = max((rule_band, similarity_band, anomaly_band), key=_BAND_RANK.__getitem__)

    # Cap 2 — a floor, not a verdict.
    if reasons.has_exact_duplicate_fingerprint:
        band = max((band, DUPLICATE_FINGERPRINT_FLOOR), key=_BAND_RANK.__getitem__)
        applied.append(Cap.DUPLICATE_FINGERPRINT_FLOOR)

    # Cap 3 — last, so it can override the other two.
    if certainty is Certainty.REDUCED_INCOMPLETE_BUNDLE:
        stepped = _STEP_DOWN[band]
        if stepped is not band:
            applied.append(Cap.INCOMPLETE_BUNDLE_STEP_DOWN)
        band = stepped

    return RankedPriority(
        bundle_id=bundle_id,
        band=band,
        deterministic_band=rule_band,
        similarity_band=similarity_band,
        anomaly_band=anomaly_band,
        components=(
            ComponentScore(
                name="deterministic_reason_priority",
                value=float(_rank(rule_band)),
                band=rule_band,
                version=RULESET_PRIORITY_VERSION,
            ),
            ComponentScore(
                name="text_similarity",
                value=similarity_score,
                band=similarity_band,
                version=SIMILARITY_VERSION,
            ),
            ComponentScore(
                name="peer_anomaly",
                value=anomaly_score,
                band=anomaly_band,
                version=ANOMALY_VERSION,
            ),
            ComponentScore(
                name="similarity_threshold",
                value=similarity_calibration.needs_context_at,
                band=SIMILARITY_ONLY_CEILING,
                version=CALIBRATION_VERSION,
            ),
            ComponentScore(
                name="anomaly_threshold",
                value=anomaly_calibration.high_priority_at,
                band=PriorityBand.HIGH_PRIORITY_SIGNAL,
                version=CALIBRATION_VERSION,
            ),
        ),
        caps_applied=tuple(applied),
        certainty=certainty,
        suggested_action=_suggest_action(reasons, certainty),
        explained_by_reasons=reasons.has_any_reason,
        identity=identity or ModelIdentity(),
    )


def _suggest_action(
    reasons: ReasonSummary, certainty: Certainty
) -> DispositionAction | None:
    """Mirrors `screening._suggest_action`. Only ever `None` or *request evidence*.

    Confirming, rejecting, and escalating are the reviewer's, and nothing statistical may point
    at them: a score is not an argument a person can weigh.
    """
    if certainty is Certainty.REDUCED_INCOMPLETE_BUNDLE:
        return DispositionAction.REQUEST_EVIDENCE
    if not reasons.has_any_reason:
        return None
    if reasons.has_deterministic_reason:
        return None  # a genuine conflict is the reviewer's call, unsuggested
    return DispositionAction.REQUEST_EVIDENCE


def _rank(band: PriorityBand) -> int:
    return _BAND_RANK[band]


def _at_most(band: PriorityBand, ceiling: PriorityBand) -> PriorityBand:
    return band if _rank(band) <= _rank(ceiling) else ceiling


class RankingModel:
    """A fitted extractor, similarity baseline, anomaly baseline, and two calibrations."""

    def __init__(
        self,
        *,
        extractor: FeatureExtractor,
        similarity: NoteSimilarity,
        anomaly: PeerAnomaly,
        similarity_calibration: BandCalibration,
        anomaly_calibration: BandCalibration,
        identity: ModelIdentity,
    ) -> None:
        self.extractor = extractor
        self.similarity = similarity
        self.anomaly = anomaly
        self.similarity_calibration = similarity_calibration
        self.anomaly_calibration = anomaly_calibration
        self.identity = identity

    @classmethod
    def train(
        cls,
        *,
        training_bundles: Sequence[CanonicalBundle],
        validation_bundles: Sequence[CanonicalBundle],
        dataset_digest: str = "unset",
    ) -> RankingModel:
        """Fit on training bundles, then calibrate the bands on validation bundles only.

        The two partitions are separate arguments rather than one corpus and a flag, so a caller
        cannot accidentally calibrate on the rows the model was fitted on.
        """
        peers = PeerProfile.fit(training_bundles)
        extractor = FeatureExtractor(peers)

        training_contexts = build_contexts(training_bundles)
        similarity = NoteSimilarity.fit(
            [
                document.text
                for bundle in training_bundles
                for document in bundle.documents
                if document.text
            ]
        )
        anomaly = PeerAnomaly.fit(
            [
                _row(extractor, bundle, training_contexts.get(bundle.bundle_id))
                for bundle in training_bundles
            ]
        )

        validation_contexts = build_contexts(validation_bundles)
        similarity_scores, anomaly_scores = [], []
        for bundle in validation_bundles:
            context = validation_contexts.get(bundle.bundle_id) or ClaimContext()
            similarity_scores.append(
                similarity.score(bundle.documents, context.peer_documents).value
            )
            anomaly_scores.append(anomaly.score(_row(extractor, bundle, context)).value)

        return cls(
            extractor=extractor,
            similarity=similarity,
            anomaly=anomaly,
            similarity_calibration=BandCalibration.fit(
                similarity_scores, partition=CALIBRATION_PARTITION
            ),
            anomaly_calibration=BandCalibration.fit(
                anomaly_scores, partition=CALIBRATION_PARTITION
            ),
            identity=ModelIdentity(dataset_digest=dataset_digest),
        )

    def rank(
        self,
        bundle: CanonicalBundle,
        *,
        reasons: ReasonSummary,
        certainty: Certainty,
        context: ClaimContext | None = None,
    ) -> RankedPriority:
        """Score one bundle and combine. The single entry point for the whole package."""
        context = context or ClaimContext()
        return combine(
            bundle_id=bundle.bundle_id,
            reasons=reasons,
            similarity_score=self.similarity.score(
                bundle.documents, context.peer_documents
            ).value,
            anomaly_score=self.anomaly.score(_row(self.extractor, bundle, context)).value,
            similarity_calibration=self.similarity_calibration,
            anomaly_calibration=self.anomaly_calibration,
            certainty=certainty,
            identity=self.identity,
        )


def _row(extractor: FeatureExtractor, bundle: CanonicalBundle, context: ClaimContext | None):
    context = context or ClaimContext()
    return extractor.extract(bundle, context.history, context.peer_documents)
