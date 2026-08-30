"""Validate a submitted bundle before anything else in the system sees it.

Validation runs as a staircase, and the order is deliberate. The cheap structural guards —
content type, size, nesting depth — run *before* the JSON is parsed, because the whole point of
a size limit is to refuse the work, not to do it and then complain. Only then does the payload
become a `CanonicalBundle`, and only then are references checked.

**The three-state result is the ethical core of this module.** `VALID_WITH_NOTES` is not a
softer `INVALID`; it is the answer for a bundle whose *shape* is sound but whose supporting
evidence is thin. An incomplete record and a billed-but-unevidenced service look identical
here, and collapsing them is precisely how this system would manufacture a false accusation.
The notes travel with the case and lower certainty downstream — they never raise a signal.

A submitted bundle is data. It is parsed, never executed, and nothing in it is ever treated as
an instruction — no eval, no dynamic import, no template rendering of its contents.
"""
from __future__ import annotations

import json
from typing import Any

from pydantic import BaseModel, ConfigDict, ValidationError
from tilik_domain.canonical import CanonicalBundle, ResourceType

from app.dto.bundles import ResourceCount, ValidationStatus
from app.errors import ErrorCode, ValidationIssue

MAX_ISSUES_REPORTED = 50
"""Enough to fix a bundle, few enough that the response stays readable."""

KNOWN_RESOURCE_KEYS: frozenset[str] = frozenset(
    {
        "bundle_id",
        "claim",
        "lines",
        "encounters",
        "conditions",
        "procedures",
        "medications",
        "diagnostics",
        "documents",
        "accounts",
        "charge_items",
        "invoices",
        "provenance",
    }
)
"""Top-level keys the canonical subset accepts. Anything else is named, not ignored."""


class ValidationOutcome(BaseModel):
    """What validation concluded, and everything the response needs to explain it."""

    model_config = ConfigDict(frozen=True, extra="forbid", arbitrary_types_allowed=True)

    status: ValidationStatus
    bundle: CanonicalBundle | None = None
    issues: tuple[ValidationIssue, ...] = ()
    completeness_notes: tuple[str, ...] = ()
    resource_counts: tuple[ResourceCount, ...] = ()

    @property
    def is_screenable(self) -> bool:
        """Invalid bundles cannot be screened; valid-with-notes deliberately can."""
        return self.status is not ValidationStatus.INVALID


class BundleRejected(Exception):
    """A bundle that cannot become a `CanonicalBundle` at all.

    Raised only for the pre-parse guards and hard parse failures. Anything the canonical model
    can represent comes back as a `ValidationOutcome` instead, so the operator sees a list of
    fixable issues rather than a single wall.
    """

    def __init__(self, code: ErrorCode, detail: str, issues: tuple[ValidationIssue, ...] = ()):
        super().__init__(detail)
        self.code = code
        self.detail = detail
        self.issues = issues


# --------------------------------------------------------------------------------------
# Stage 1 — structural guards, applied before the payload is parsed
# --------------------------------------------------------------------------------------


def guard_content_type(content_type: str | None) -> None:
    if content_type is None:
        raise BundleRejected(
            ErrorCode.BUNDLE_UNSUPPORTED_CONTENT_TYPE, "Content-Type header is required"
        )
    media_type = content_type.split(";", 1)[0].strip().lower()
    if media_type != "application/json":
        raise BundleRejected(
            ErrorCode.BUNDLE_UNSUPPORTED_CONTENT_TYPE,
            f"Expected application/json, received {media_type or 'nothing'}",
        )


def guard_size(raw: bytes, max_bytes: int) -> None:
    """Refuse an oversized payload without parsing it."""
    if len(raw) > max_bytes:
        raise BundleRejected(
            ErrorCode.BUNDLE_TOO_LARGE,
            f"Bundle is {len(raw)} bytes; the limit is {max_bytes}",
        )


def parse_json(raw: bytes, max_depth: int) -> dict[str, Any]:
    """Parse the payload, refusing anything nested deeply enough to be an attack.

    Depth is measured on the parsed structure rather than by counting brackets in the text,
    because the text form can be padded to disguise its shape.
    """
    try:
        payload = json.loads(raw)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise BundleRejected(
            ErrorCode.BUNDLE_MALFORMED_JSON, f"Payload is not valid JSON: {exc.__class__.__name__}"
        ) from exc

    if not isinstance(payload, dict):
        raise BundleRejected(
            ErrorCode.BUNDLE_SCHEMA_INVALID, "Top level of a bundle must be a JSON object"
        )

    depth = _measure_depth(payload, limit=max_depth)
    if depth > max_depth:
        raise BundleRejected(
            ErrorCode.BUNDLE_DEPTH_EXCEEDED,
            f"Bundle nests deeper than the {max_depth}-level limit",
        )
    return payload


def _measure_depth(value: Any, *, limit: int, level: int = 1) -> int:
    """Depth of the nesting, giving up as soon as the limit is beaten.

    Iterative rather than recursive: a deeply nested payload is exactly the input that would
    blow the interpreter stack, and crashing on hostile input is not a rejection.
    """
    deepest = level
    stack: list[tuple[Any, int]] = [(value, level)]
    while stack:
        current, depth = stack.pop()
        deepest = max(deepest, depth)
        if depth > limit:
            return depth
        if isinstance(current, dict):
            stack.extend((item, depth + 1) for item in current.values())
        elif isinstance(current, list):
            stack.extend((item, depth + 1) for item in current)
    return deepest


# --------------------------------------------------------------------------------------
# Stage 2 — schema, then references
# --------------------------------------------------------------------------------------


def validate_bundle(payload: dict[str, Any]) -> ValidationOutcome:
    """Turn a parsed payload into a validated bundle, or into a list of fixable issues."""
    unknown = sorted(set(payload) - KNOWN_RESOURCE_KEYS)
    if unknown:
        raise BundleRejected(
            ErrorCode.BUNDLE_UNKNOWN_RESOURCE_TYPE,
            f"Unsupported top-level keys: {', '.join(unknown)}",
            tuple(
                ValidationIssue(
                    code=ErrorCode.BUNDLE_UNKNOWN_RESOURCE_TYPE,
                    resource_type=key,
                    detail=f"{key!r} is not part of the documented bundle subset",
                )
                for key in unknown[:MAX_ISSUES_REPORTED]
            ),
        )

    try:
        bundle = CanonicalBundle.model_validate(payload)
    except ValidationError as exc:
        return ValidationOutcome(
            status=ValidationStatus.INVALID, issues=_schema_issues(exc)
        )

    issues = (*_duplicate_id_issues(bundle), *_dangling_reference_issues(bundle))
    issues += _circular_reference_issues(bundle)

    if issues:
        return ValidationOutcome(
            status=ValidationStatus.INVALID,
            issues=issues[:MAX_ISSUES_REPORTED],
            resource_counts=count_resources(bundle),
        )

    notes = completeness_notes(bundle)
    return ValidationOutcome(
        status=ValidationStatus.VALID_WITH_NOTES if notes else ValidationStatus.VALID,
        bundle=bundle,
        completeness_notes=notes,
        resource_counts=count_resources(bundle),
    )


def _schema_issues(error: ValidationError) -> tuple[ValidationIssue, ...]:
    """Turn pydantic's report into per-resource issues an operator can act on.

    Only the field location and the failure type are carried across. Pydantic echoes offending
    input values, and in this domain those values can be clinical text.
    """
    issues: list[ValidationIssue] = []
    for detail in error.errors()[:MAX_ISSUES_REPORTED]:
        location = ".".join(str(part) for part in detail["loc"])
        issues.append(
            ValidationIssue(
                code=ErrorCode.BUNDLE_SCHEMA_INVALID,
                resource_type=str(detail["loc"][0]) if detail["loc"] else None,
                detail=f"{location}: {detail['type']}",
            )
        )
    return tuple(issues)


def _duplicate_id_issues(bundle: CanonicalBundle) -> tuple[ValidationIssue, ...]:
    """Two resources sharing an id make every reference to that id ambiguous."""
    seen: dict[tuple[str, str], int] = {}
    for resource_type, items, id_field in _resource_groups(bundle):
        for item in items:
            key = (str(resource_type), getattr(item, id_field))
            seen[key] = seen.get(key, 0) + 1
    return tuple(
        ValidationIssue(
            code=ErrorCode.BUNDLE_DUPLICATE_RESOURCE_ID,
            resource_type=resource_type,
            resource_id=resource_id,
            detail=f"{resource_type}/{resource_id} appears {count} times",
        )
        for (resource_type, resource_id), count in sorted(seen.items())
        if count > 1
    )


def _dangling_reference_issues(bundle: CanonicalBundle) -> tuple[ValidationIssue, ...]:
    """Name the missing resource. "Invalid bundle" is not something an operator can fix."""
    return tuple(
        ValidationIssue(
            code=ErrorCode.BUNDLE_DANGLING_REFERENCE,
            resource_type=str(ref.resource_type),
            resource_id=ref.resource_id,
            detail=f"{ref.resource_type}/{ref.resource_id} is referenced but not present",
        )
        for ref in bundle.unresolved_refs()
    )


def _circular_reference_issues(bundle: CanonicalBundle) -> tuple[ValidationIssue, ...]:
    """Detect a claim line that supports itself, directly or through a chain.

    Walked iteratively with a visited set, so a cycle is reported rather than recursed into.
    """
    adjacency: dict[str, set[str]] = {}
    for line in bundle.lines:
        node = f"{ResourceType.CLAIM_LINE}/{line.line_id}"
        targets = {f"{ref.resource_type}/{ref.resource_id}" for ref in line.supporting_refs}
        if line.charge_item_ref is not None:
            targets.add(
                f"{line.charge_item_ref.resource_type}/{line.charge_item_ref.resource_id}"
            )
        adjacency.setdefault(node, set()).update(targets)

    issues: list[ValidationIssue] = []
    for start in sorted(adjacency):
        if _reaches_itself(start, adjacency):
            resource_type, _, resource_id = start.partition("/")
            issues.append(
                ValidationIssue(
                    code=ErrorCode.BUNDLE_CIRCULAR_REFERENCE,
                    resource_type=resource_type,
                    resource_id=resource_id,
                    detail=f"{start} takes part in a reference cycle",
                )
            )
    return tuple(issues)


def _reaches_itself(start: str, adjacency: dict[str, set[str]]) -> bool:
    seen: set[str] = set()
    stack = list(adjacency.get(start, ()))
    while stack:
        node = stack.pop()
        if node == start:
            return True
        if node in seen:
            continue
        seen.add(node)
        stack.extend(adjacency.get(node, ()))
    return False


# --------------------------------------------------------------------------------------
# Completeness — the notes that make VALID_WITH_NOTES mean something
# --------------------------------------------------------------------------------------


def completeness_notes(bundle: CanonicalBundle) -> tuple[str, ...]:
    """Record what the submission does not contain, in working language.

    **A note is about a whole missing category, never about one unevidenced line.** That
    boundary is the most consequential decision in this module. A billed line with no
    supporting reference is the phantom-billing *signal* — it is what the system exists to
    surface. If it were also recorded here it would lower certainty downstream and defuse the
    very detector it should be feeding. So it is not a note; it is a finding, and the rule
    engine owns it.

    What is left are the categories whose total absence makes tracing impossible for the whole
    bundle. Those genuinely reduce what can be concluded from anything in it.

    Every note describes the *submission*, never the care. "No encounter data was included" is
    a fact about a file; "no care was given" would be a claim this system is not entitled to
    make. Clinical documents are deliberately not on this list — most claims carry none, and
    treating that as incompleteness would mark almost every bundle as thin.
    """
    notes: list[str] = []
    if not bundle.encounters:
        notes.append("Bundel tidak memuat data kunjungan.")
    if not bundle.procedures and not bundle.medications:
        notes.append("Bundel tidak memuat catatan tindakan maupun pemberian obat.")
    if not bundle.charge_items:
        notes.append("Bundel tidak memuat rincian tagihan.")
    if not bundle.provenance:
        notes.append("Bundel tidak memuat data asal-usul (provenance).")
    return tuple(notes)


def count_resources(bundle: CanonicalBundle) -> tuple[ResourceCount, ...]:
    counts = [
        ResourceCount(resource_type=str(resource_type), count=len(items))
        for resource_type, items, _ in _resource_groups(bundle)
    ]
    counts.append(ResourceCount(resource_type=str(ResourceType.CLAIM), count=1))
    return tuple(sorted(counts, key=lambda entry: entry.resource_type))


def _resource_groups(bundle: CanonicalBundle) -> tuple[tuple[ResourceType, tuple, str], ...]:
    return (
        (ResourceType.CLAIM_LINE, bundle.lines, "line_id"),
        (ResourceType.ENCOUNTER, bundle.encounters, "encounter_id"),
        (ResourceType.CONDITION, bundle.conditions, "condition_id"),
        (ResourceType.PROCEDURE, bundle.procedures, "procedure_id"),
        (ResourceType.MEDICATION, bundle.medications, "medication_id"),
        (ResourceType.DIAGNOSTIC, bundle.diagnostics, "diagnostic_id"),
        (ResourceType.DOCUMENT, bundle.documents, "document_id"),
        (ResourceType.ACCOUNT, bundle.accounts, "account_id"),
        (ResourceType.CHARGE_ITEM, bundle.charge_items, "charge_item_id"),
        (ResourceType.INVOICE, bundle.invoices, "invoice_id"),
    )
