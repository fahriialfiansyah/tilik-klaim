"""Resolve what a reason points at, and compare the pairs it raises.

Two jobs, both in service of the case-detail screen's binding display rules
(`sprint/00-app-spec.md` § 4):

* **Every evidence reference must open.** So each reference a reason cites is resolved once,
  here, and shipped with the detail response. A reference that resolves to nothing is reported
  as `MISSING` rather than left out — an omitted reference renders as a shorter list, which is
  indistinguishable from a reason that simply cited less.
* **A comparison must compare.** The drawer for repeat-billing and cloned-documentation shows
  two candidates side by side with the fields that match and the fields that differ. Listing
  the reason's own component scores with the same value on both sides is not that.

Both jobs cross a privacy boundary, and the direction matters. A cloned-documentation pair
spans two participants by definition, so the peer side is reduced to fields that identify
nothing: kind, timing, length, digest. `docs/canonical/07_privacy_threat_model.md` names the
similarity highlight as the exposure route, so the reduction happens here rather than being
left to whichever screen renders it.
"""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from tilik_domain.canonical import CanonicalBundle, DocumentRef, ResourceRef, ResourceType
from tilik_domain.reasons import RiskMode

from app.dto.cases import (
    ComparisonCandidate,
    ComparisonField,
    SourceAvailability,
    SourceField,
    SourceResource,
)
from app.service.rules.registry import ReasonHit

TEMPLATE_CAVEAT = (
    "Dokumentasi berbasis templat menghasilkan kemiripan tinggi tanpa ada yang disalin. "
    "Baca ini sebelum mengambil keputusan."
)

IDENTIFYING_FIELDS: frozenset[str] = frozenset(
    {"participant_id", "text", "author_id", "performer_id", "location_id"}
)
"""Never shown for a resource belonging to another submission.

`text` and `participant_id` are the obvious ones. The other three are quieter: a practitioner
or location id is a small enough set that it re-identifies a visit at a single facility.
"""

TEXT_DIGEST_LENGTH = 12
"""Enough of a hash to compare two documents by eye, too little to attack."""


# --------------------------------------------------------------------------------------
# Source index
# --------------------------------------------------------------------------------------


def build_source_index(
    hits: tuple[ReasonHit, ...],
    bundle: CanonicalBundle | None,
    history: tuple[CanonicalBundle, ...] = (),
    peer_documents: tuple[DocumentRef, ...] = (),
    extra_refs: tuple[ResourceRef, ...] = (),
) -> tuple[SourceResource, ...]:
    """One entry per resource the screen can point at, in first-cited order.

    Order is stable rather than sorted so the index reads in the same sequence the reasons do;
    a reviewer following a reason's references down the list finds them where they were cited.

    `extra_refs` carries references the screen renders outside a reason — the episode timeline's
    resources, above all. Leaving them out was a live defect in waiting: the timeline draws an
    unresolvable reference as an integrity defect, so a procedure that is present and fine but
    simply not cited by any reason would have been flagged as a broken evidence trail.
    """
    own = bundle.resource_index() if bundle else {}
    related = _related_index(history, peer_documents)

    seen: set[tuple[str, str]] = set()
    sources: list[SourceResource] = []
    for ref in (*_referenced(hits), *extra_refs):
        key = (str(ref.resource_type), ref.resource_id)
        if key in seen:
            continue
        seen.add(key)
        sources.append(_resolve(ref, own, related))
    return tuple(sources)


def _referenced(hits: tuple[ReasonHit, ...]) -> tuple[ResourceRef, ...]:
    """Every reference a reason rests on, supporting and opposing alike.

    Counter-evidence references are included deliberately: the reference that argues *against*
    a signal is the one a reviewer most needs to be able to open.
    """
    refs: list[ResourceRef] = []
    for hit in hits:
        refs.extend(hit.evidence)
        refs.extend(ref for note in hit.counter_evidence for ref in note.refs)
    return tuple(refs)


def _related_index(
    history: tuple[CanonicalBundle, ...], peer_documents: tuple[DocumentRef, ...]
) -> dict[tuple[str, str], object]:
    """Resources from other submissions the rules compared this one against."""
    index: dict[tuple[str, str], object] = {}
    for past in history:
        index.update(past.resource_index())
    for document in peer_documents:
        index[(str(ResourceType.DOCUMENT), document.document_id)] = document
    return index


def _resolve(
    ref: ResourceRef,
    own: dict[tuple[str, str], object],
    related: dict[tuple[str, str], object],
) -> SourceResource:
    key = (str(ref.resource_type), ref.resource_id)
    label = f"{ref.resource_type} {ref.resource_id}"

    resource = own.get(key)
    if resource is not None:
        return SourceResource(
            resource_type=ref.resource_type,
            resource_id=ref.resource_id,
            label=label,
            availability=SourceAvailability.PRESENT,
            fields=_fields(resource, redact=False),
        )

    resource = related.get(key)
    if resource is not None:
        return SourceResource(
            resource_type=ref.resource_type,
            resource_id=ref.resource_id,
            label=label,
            availability=SourceAvailability.RELATED_BUNDLE,
            fields=_fields(resource, redact=True),
        )

    # An episode or a practitioner is referenced by identity and never stored as a resource of
    # its own. Reporting that as MISSING would raise a false integrity defect on every bundle.
    availability = (
        SourceAvailability.MISSING
        if ref.resource_type.is_stored_resource
        else SourceAvailability.NOT_STORED
    )
    return SourceResource(
        resource_type=ref.resource_type,
        resource_id=ref.resource_id,
        label=label,
        availability=availability,
    )


def _fields(resource: object, *, redact: bool) -> tuple[SourceField, ...]:
    """Flatten one canonical resource for display, in declaration order.

    `redact` drops the identifying fields entirely rather than masking them. A masked field
    still tells a reader that the value exists and is worth asking about, which is the leak in
    slower motion.
    """
    dumped = getattr(resource, "model_dump", None)
    if dumped is None:
        return ()

    fields: list[SourceField] = []
    for name, value in dumped(mode="python").items():
        if redact and name in IDENTIFYING_FIELDS:
            continue
        if name == "text" and isinstance(value, str):
            fields.append(SourceField(name="text", value=value))
            continue
        rendered = _render(value)
        if rendered is not None:
            fields.append(SourceField(name=name, value=rendered))

    if redact and isinstance(resource, DocumentRef):
        fields = [*fields, *_document_shape(resource)]
    return tuple(fields)


def _document_shape(document: DocumentRef) -> tuple[SourceField, ...]:
    """What can be said about someone else's note without quoting it."""
    length = len(document.text) if document.text else 0
    return (
        SourceField(name="text_length", value=str(length)),
        SourceField(name="text_digest", value=document.text_hash[:TEXT_DIGEST_LENGTH]),
    )


def _render(value: object) -> str | None:
    """Scalar rendering. Nested structures are left out rather than dumped as Python repr."""
    if value is None:
        return "—"
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, Decimal | int | float | bool | str):
        return str(value)
    return None


# --------------------------------------------------------------------------------------
# Comparisons
# --------------------------------------------------------------------------------------


def build_comparisons(
    hits: tuple[ReasonHit, ...],
    bundle: CanonicalBundle | None,
    history: tuple[CanonicalBundle, ...] = (),
    peer_documents: tuple[DocumentRef, ...] = (),
) -> tuple[ComparisonCandidate, ...]:
    """Side-by-side pairs for the two comparison-shaped modes."""
    if bundle is None:
        return ()

    by_claim = {past.claim.claim_id: past for past in history}
    documents = {document.document_id: document for document in peer_documents}
    own_documents = {document.document_id: document for document in bundle.documents}

    candidates: list[ComparisonCandidate] = []
    for hit in hits:
        if hit.mode is RiskMode.REPEAT_BILLING:
            candidate = _claim_comparison(hit, bundle, by_claim)
        elif hit.mode is RiskMode.CLONED_DOCUMENTATION:
            candidate = _document_comparison(hit, own_documents, documents)
        else:
            continue
        if candidate is not None:
            candidates.append(candidate)
    return tuple(candidates)


def _claim_comparison(
    hit: ReasonHit, bundle: CanonicalBundle, by_claim: dict[str, CanonicalBundle]
) -> ComparisonCandidate | None:
    """This claim against the prior one the rule matched it to.

    Both belong to the same participant at the same provider — `history_for` scopes it that
    way — so nothing here crosses a person's boundary.
    """
    past = next(
        (
            by_claim[ref.resource_id]
            for ref in hit.evidence
            if ref.resource_type is ResourceType.CLAIM and ref.resource_id in by_claim
        ),
        None,
    )
    if past is None:
        return None

    left, right = bundle.claim, past.claim
    fields = (
        _field("Kunjungan", left.encounter_id, right.encounter_id),
        _field("Jenis perawatan", str(left.care_type), str(right.care_type)),
        _field("Total tagihan", f"{left.total_amount}", f"{right.total_amount}"),
        _field("Jumlah baris", str(len(bundle.lines)), str(len(past.lines))),
        _field("Waktu kirim", left.submitted_at.isoformat(), right.submitted_at.isoformat()),
        _field("Episode", left.episode_id or "—", right.episode_id or "—"),
    )
    start, end = _overlap(bundle, past)
    return ComparisonCandidate(
        candidate_claim_id=right.claim_id,
        fields=fields,
        overlap_start=start,
        overlap_end=end,
        similarity_components=dict(hit.component_scores),
    )


def _document_comparison(
    hit: ReasonHit,
    own_documents: dict[str, DocumentRef],
    peer_documents: dict[str, DocumentRef],
) -> ComparisonCandidate | None:
    """This note against the peer note it resembles, without quoting either side.

    The compared pair belongs to two different participants, so the fields are the note's
    *shape* — kind, timing, length, digest — never its content. A reviewer confirming a genuine
    copy opens the source panel for their own bundle's document; the other side stays closed,
    and the template caveat says why high similarity is not by itself an answer.
    """
    mine = next(
        (
            own_documents[ref.resource_id]
            for ref in hit.evidence
            if ref.resource_type is ResourceType.DOCUMENT and ref.resource_id in own_documents
        ),
        None,
    )
    theirs = next(
        (
            peer_documents[ref.resource_id]
            for ref in hit.evidence
            if ref.resource_type is ResourceType.DOCUMENT and ref.resource_id in peer_documents
        ),
        None,
    )
    if mine is None or theirs is None:
        return None

    fields = (
        _field("Jenis dokumen", mine.kind, theirs.kind),
        _field("Waktu penulisan", mine.authored_at.isoformat(), theirs.authored_at.isoformat()),
        _field("Panjang teks", str(len(mine.text or "")), str(len(theirs.text or ""))),
        _field(
            "Sidik teks",
            mine.text_hash[:TEXT_DIGEST_LENGTH],
            theirs.text_hash[:TEXT_DIGEST_LENGTH],
        ),
    )
    return ComparisonCandidate(
        candidate_claim_id=theirs.document_id,
        fields=fields,
        similarity_components=dict(hit.component_scores),
        template_caveat=TEMPLATE_CAVEAT,
    )


def _field(name: str, left: str, right: str) -> ComparisonField:
    return ComparisonField(
        field_name=name, left_value=left, right_value=right, matches=left == right
    )


def _overlap(
    bundle: CanonicalBundle, past: CanonicalBundle
) -> tuple[datetime | None, datetime | None]:
    """The part of the two episodes that actually coincides, if any.

    An overlap is what makes a repeat worth a second look; its absence is what argues the two
    were separate visits. Returning `None` for a non-overlapping pair says the second thing.
    """
    left = _window(bundle)
    right = _window(past)
    if left is None or right is None:
        return None, None

    start = max(left[0], right[0])
    end = min(left[1], right[1])
    return (start, end) if start <= end else (None, None)


def _window(bundle: CanonicalBundle) -> tuple[datetime, datetime] | None:
    if not bundle.encounters:
        return None
    starts = [encounter.start_at for encounter in bundle.encounters]
    ends = [encounter.end_at or encounter.start_at for encounter in bundle.encounters]
    return min(starts), max(ends)
