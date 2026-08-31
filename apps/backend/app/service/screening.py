"""Screen one bundle: derive the graph, run the rules, assign a band.

The banding is the most safety-critical code in the service, because the band is what orders a
reviewer's day. `docs/canonical/05_model_card.md` gives the combiner and three caps, and each
cap exists to stop a specific harm:

* **Text similarity alone never reaches the top band.** Shared templates are ordinary practice.
* **Missing evidence plus an incomplete bundle lowers certainty** and routes to *request
  evidence*, never toward *confirm anomaly* — an incomplete record is not evidence a service
  was not delivered.
* **An exact duplicate fingerprint is high priority but still human-reviewed.** Nothing here
  decides anything; screening produces a queue position and an argued case, and a person acts.

There is no hardcoded "this score means fraud" threshold anywhere. Bands come from which
reasons fired and how certain they are, and every component score is kept alongside the
aggregate so the basis can be shown.
"""
from __future__ import annotations

import hashlib
import json
from enum import StrEnum
from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict
from tilik_domain.canonical import CanonicalBundle, DocumentRef
from tilik_domain.reasons import DispositionAction, PriorityBand, ReasonCode
from tilik_domain.versioning import EngineIdentity

from app.service.evidence_graph import EvidenceGap, GapReason, build_evidence_graph
from app.service.rules.clone_baseline import CloneBaselineRule
from app.service.rules.phantom import PhantomRule
from app.service.rules.registry import ReasonHit, RuleContext, RuleRegistry
from app.service.rules.repeat import RepeatBillingRule
from app.service.rules.unbundling import UnbundlingRule

if TYPE_CHECKING:
    from collections.abc import Iterable

    from app.service.evidence_graph import EvidenceGraph

DEFAULT_REGISTRY = RuleRegistry(
    (PhantomRule(), RepeatBillingRule(), UnbundlingRule(), CloneBaselineRule())
)
"""Fixed rule order, so two screenings of one bundle list reasons in the same sequence."""

SIMILARITY_ONLY_CEILING = PriorityBand.NEEDS_CONTEXT
"""The highest band a case may reach when text similarity is its only evidence."""


class Certainty(StrEnum):
    """How much the record itself supports acting on the reasons.

    This is about the *completeness of the evidence*, not the strength of suspicion. A reduced
    certainty is the system saying "ask for more", never "we are less sure they did it".
    """

    FULL = "FULL"
    REDUCED_INCOMPLETE_BUNDLE = "REDUCED_INCOMPLETE_BUNDLE"


class ScreeningResult(BaseModel):
    """Everything one screening run produced, with its version identity attached."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    bundle_id: str
    input_hash: str
    """Digest of the screened content. Same hash and same version means same result."""
    band: PriorityBand
    certainty: Certainty
    reasons: tuple[ReasonHit, ...]
    gaps: tuple[EvidenceGap, ...]
    suggested_action: DispositionAction | None
    """A suggestion for the reviewer, never an applied decision."""
    identity: EngineIdentity
    rule_ids: tuple[str, ...]

    @property
    def has_observed_risk(self) -> bool:
        """`False` means no detector fired. It does not mean the claim is clean or safe."""
        return bool(self.reasons)


def screen_bundle(
    bundle: CanonicalBundle,
    history: Iterable[CanonicalBundle] = (),
    peer_documents: Iterable[DocumentRef] = (),
    *,
    registry: RuleRegistry = DEFAULT_REGISTRY,
    identity: EngineIdentity | None = None,
) -> ScreeningResult:
    """Screen `bundle` and return its reasons, band, and the basis for both.

    `peer_documents` are notes from other participants at the same provider. Clone detection
    needs them; without them that mode is inert.
    """
    prior = tuple(history)
    graph = build_evidence_graph(bundle, history=prior, peer_documents=peer_documents)
    context = RuleContext(bundle=bundle, history=prior, graph=graph)
    reasons = registry.evaluate(context)

    certainty = _assess_certainty(graph)
    band = _assign_band(reasons, certainty)

    return ScreeningResult(
        bundle_id=bundle.bundle_id,
        input_hash=input_hash(bundle, prior),
        band=band,
        certainty=certainty,
        reasons=reasons,
        gaps=graph.gaps,
        suggested_action=_suggest_action(reasons, certainty),
        identity=identity or EngineIdentity(),
        rule_ids=registry.rule_ids(),
    )


def input_hash(bundle: CanonicalBundle, history: tuple[CanonicalBundle, ...] = ()) -> str:
    """Content digest over the screened input.

    Screening the same hash at the same engine version must produce the same result, so this
    is what a determinism check compares — not object identity or ordering.
    """
    payload = [bundle.model_dump(mode="json")]
    payload.extend(past.model_dump(mode="json") for past in history)
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


# --------------------------------------------------------------------------------------
# Banding and the caps
# --------------------------------------------------------------------------------------


def _assess_certainty(graph: EvidenceGraph) -> Certainty:
    """An unresolvable reference means the bundle is incomplete, not that evidence is absent."""
    incomplete = any(
        gap.reason is GapReason.DANGLING_REFERENCE for gap in graph.gaps
    )
    return Certainty.REDUCED_INCOMPLETE_BUNDLE if incomplete else Certainty.FULL


def _assign_band(reasons: tuple[ReasonHit, ...], certainty: Certainty) -> PriorityBand:
    if not reasons:
        return PriorityBand.NO_OBSERVED_RISK

    band = (
        PriorityBand.DETERMINISTIC_CONFLICT
        if any(reason.deterministic for reason in reasons)
        else PriorityBand.NEEDS_CONTEXT
    )

    # Cap: similarity on its own argues for a look, never for the top of the queue.
    if _is_similarity_only(reasons):
        band = SIMILARITY_ONLY_CEILING

    # Cap: an incomplete bundle lowers certainty rather than raising a signal.
    if certainty is Certainty.REDUCED_INCOMPLETE_BUNDLE:
        band = _step_down(band)

    return band


def _is_similarity_only(reasons: tuple[ReasonHit, ...]) -> bool:
    return all(
        reason.code is ReasonCode.NEAR_DUPLICATE_DOCUMENTATION for reason in reasons
    )


_STEP_DOWN: dict[PriorityBand, PriorityBand] = {
    PriorityBand.DETERMINISTIC_CONFLICT: PriorityBand.HIGH_PRIORITY_SIGNAL,
    PriorityBand.HIGH_PRIORITY_SIGNAL: PriorityBand.NEEDS_CONTEXT,
    PriorityBand.NEEDS_CONTEXT: PriorityBand.NEEDS_CONTEXT,
    PriorityBand.NO_OBSERVED_RISK: PriorityBand.NO_OBSERVED_RISK,
}
"""One band lower, never below "needs context" — a raised case stays visible."""


def _step_down(band: PriorityBand) -> PriorityBand:
    return _STEP_DOWN[band]


def _suggest_action(
    reasons: tuple[ReasonHit, ...], certainty: Certainty
) -> DispositionAction | None:
    """Suggest the reviewer's next step. The reviewer is free to ignore it.

    The one rule that is not a suggestion but a safety property: when the bundle is incomplete,
    the route is *request evidence*. Offering "confirm anomaly" on a record known to be missing
    pieces invites a finding the evidence cannot support.
    """
    if not reasons:
        return None
    if certainty is Certainty.REDUCED_INCOMPLETE_BUNDLE:
        return DispositionAction.REQUEST_EVIDENCE
    if any(reason.deterministic for reason in reasons):
        return None  # a genuine conflict is the reviewer's call, unsuggested
    return DispositionAction.REQUEST_EVIDENCE
