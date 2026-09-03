"""Build the case detail from the stores — one place, used by the router and the briefing.

The briefing (ADR-0005) reads *exactly* the object `GET /v1/cases/{id}` returns; building it
here rather than inside the router is what makes that a fact instead of a convention.
"""
from __future__ import annotations

from app.dto.cases import CaseDetailResponse
from app.service.case_query import to_detail
from app.store.bundles import BundleStore
from app.store.cases import CaseStore


def load_case_detail(
    case_id: str, cases: CaseStore, bundles: BundleStore
) -> CaseDetailResponse | None:
    """`None` when there is no such case. Otherwise the detail, with its comparison history."""
    case = cases.get(case_id)
    if case is None:
        return None

    ingestion = bundles.get(case.ingestion_id)
    if ingestion is None or ingestion.bundle is None:
        return to_detail(case, ingestion)

    # The other submissions the rules compared this one against. Without them a reference to a
    # prior claim or a peer note resolves to nothing, and the screen would report a genuine
    # comparison as an evidence-integrity defect.
    claim = ingestion.bundle.claim
    history = bundles.history_for(
        claim.participant_id, claim.provider_id, exclude_bundle_id=ingestion.bundle.bundle_id
    )
    peer_documents = bundles.peer_documents_for(
        claim.provider_id, exclude_bundle_id=ingestion.bundle.bundle_id
    )
    return to_detail(case, ingestion, history, peer_documents, bundles.case_id_for_bundle)
