"""Structural measurements over one bundle — the arithmetic behind the feature families.

Separated from `features.py` so the feature declarations stay readable beside the schema they
implement. **None of these reads an identifier as a value.** Identifiers appear only in equality
tests — does this reference resolve, is this the same code — which survive a re-identification
of the whole corpus unchanged. `tests/test_features.py` proves that property holds.
"""
from __future__ import annotations

import difflib
from collections.abc import Iterable, Sequence
from datetime import datetime

from tilik_domain.canonical import CanonicalBundle, EncounterStatus, EventStatus

MINIMUM_ROBUST_SCALE = 1.0
"""Floor for a peer scale, so a facility whose claims are all identical cannot divide by zero."""

SECONDS_PER_DAY = 86_400.0


def clinical_event_statuses(bundle: CanonicalBundle) -> tuple[EventStatus, ...]:
    return (
        *(procedure.status for procedure in bundle.procedures),
        *(medication.status for medication in bundle.medications),
        *(diagnostic.status for diagnostic in bundle.diagnostics),
        *(
            EventStatus.ENTERED_IN_ERROR
            if encounter.status is EncounterStatus.ENTERED_IN_ERROR
            else EventStatus.COMPLETED
            for encounter in bundle.encounters
        ),
    )


def visit_window(bundle: CanonicalBundle) -> tuple[datetime, datetime]:
    starts = [encounter.start_at for encounter in bundle.encounters]
    ends = [encounter.end_at or encounter.start_at for encounter in bundle.encounters]
    if not starts:
        moment = bundle.claim.submitted_at
        return (moment, moment)
    return (min(starts), max(ends))


def windows_overlap(
    left: tuple[datetime, datetime], right: tuple[datetime, datetime]
) -> bool:
    return left[0] <= right[1] and right[0] <= left[1]


def line_fingerprints(bundle: CanonicalBundle) -> list[tuple[str, str, str, str]]:
    """A line's billing identity: what was billed, how much, at what price."""
    return [
        (line.code_system, line.code, str(line.quantity), str(line.line_amount))
        for line in bundle.lines
    ]


def service_sequence(bundle: CanonicalBundle) -> tuple[str, ...]:
    return tuple(line.code for line in sorted(bundle.lines, key=lambda line: line.service_at))


def nearest_sequence_distance(
    sequence: tuple[str, ...], candidates: Sequence[tuple[str, ...]]
) -> float | None:
    """Distance from a service sequence to the closest non-empty candidate, 0 (same) to 1.

    `difflib` rather than a hand-rolled edit distance: it is deterministic, in the standard
    library, and one fewer piece of arithmetic to get subtly wrong.
    """
    usable = [candidate for candidate in candidates if candidate]
    if not sequence or not usable:
        return None
    return min(
        1.0 - difflib.SequenceMatcher(None, sequence, candidate).ratio()
        for candidate in usable
    )


def max_jaccard(mine: set[str], others: Iterable[set[str]]) -> float | None:
    if not mine:
        return None
    scores = [
        len(mine & other) / len(mine | other) for other in others if other
    ]
    return max(scores) if scores else None


def median(values: Sequence[float]) -> float:
    ordered = sorted(values)
    if not ordered:
        return 0.0
    middle = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[middle]
    return (ordered[middle - 1] + ordered[middle]) / 2.0


def robust_scale(values: Sequence[float]) -> float:
    """Median absolute deviation, floored so an identical peer group cannot divide by zero."""
    if not values:
        return MINIMUM_ROBUST_SCALE
    centre = median(values)
    return max(median([abs(value - centre) for value in values]), MINIMUM_ROBUST_SCALE)
