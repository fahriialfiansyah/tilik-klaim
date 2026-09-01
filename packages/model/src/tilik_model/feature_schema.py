"""The declared feature contract: what each column is, and what it means when it is missing.

The schema is data, not documentation. `model_card.py` renders it, the conformance test checks
the extractor against it, and the imputation value for every column is declared here rather than
chosen at the call site — because the failure this guards against is a missing measurement
arriving as a confident `0.0`. "No peer group to compare against" and "exactly average for its
peer group" are different facts, and a silent zero makes them identical.

Families are the six named in `docs/canonical/05_model_card.md` § Feature families. Demographics
and protected characteristics appear in none of them: the four risk modes do not need them, and
the model card excludes them until an authorised fairness analysis establishes a purpose.
"""
from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict

from tilik_model.version import FEATURE_VERSION

NO_RELATED_CLAIM_DAYS = 365.0
"""Stand-in gap when a claim has no related prior claim at all.

A year, not zero: zero would read as "another claim the same day", which is the strongest
repeat-billing signal there is. The sentinel has to sit at the *harmless* end of the range.
"""

MAXIMALLY_DIFFERENT = 1.0
"""Stand-in distance when there is nothing to compare a service sequence against."""

NO_DEVIATION = 0.0
"""Stand-in for a peer-context feature when the provider is unseen — the cold-start case.

Zero is correct *here* precisely because it is not a measurement: an unseen provider gives no
grounds to say a claim deviates, so the model must not act as if it had found one. The column is
listed in `FeatureRow.imputed` so the absence stays visible.
"""


class FeatureFamily(StrEnum):
    """The six families from the model card. Every column belongs to exactly one."""

    EVIDENCE_COMPLETENESS = "evidence_completeness"
    EPISODE_INTEGRITY = "episode_integrity"
    SIMILARITY = "similarity"
    PEER_CONTEXT = "peer_context"
    PROVENANCE = "provenance"
    AMOUNT_QUANTITY = "amount_quantity"


class FeatureSpec(BaseModel):
    """One column of the feature table."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str
    family: FeatureFamily
    description: str
    imputation: float
    imputation_note: str
    """Why that value, in working language. Rendered into the model card verbatim."""

    feature_version: str = FEATURE_VERSION


def _spec(
    name: str,
    family: FeatureFamily,
    description: str,
    imputation: float,
    imputation_note: str,
) -> FeatureSpec:
    return FeatureSpec(
        name=name,
        family=family,
        description=description,
        imputation=imputation,
        imputation_note=imputation_note,
    )


_COMPLETENESS = FeatureFamily.EVIDENCE_COMPLETENESS
_EPISODE = FeatureFamily.EPISODE_INTEGRITY
_SIMILARITY = FeatureFamily.SIMILARITY
_PEER = FeatureFamily.PEER_CONTEXT
_PROVENANCE = FeatureFamily.PROVENANCE
_AMOUNT = FeatureFamily.AMOUNT_QUANTITY

FEATURE_SCHEMA: tuple[FeatureSpec, ...] = (
    _spec(
        "unsupported_line_ratio",
        _COMPLETENESS,
        "Share of billed lines with no supporting clinical record that resolves.",
        0.0,
        "A claim with no billed lines has no unsupported line to count.",
    ),
    _spec(
        "dangling_reference_count",
        _COMPLETENESS,
        "References that point at a record the bundle does not contain.",
        0.0,
        "Counted directly; a bundle with no references has none dangling.",
    ),
    _spec(
        "retracted_evidence_count",
        _COMPLETENESS,
        "Supporting records marked entered-in-error — evidence withdrawn, not never recorded.",
        0.0,
        "Counted directly.",
    ),
    _spec(
        "noncompleted_evidence_ratio",
        _COMPLETENESS,
        "Share of clinical records whose status is anything other than completed.",
        0.0,
        "A bundle carrying no clinical record has no status to be uncertain about.",
    ),
    _spec(
        "overlapping_history_claim_count",
        _EPISODE,
        "Earlier claims at the same facility whose visit window overlaps this one.",
        0.0,
        "No prior claim was supplied, so no overlap is observable.",
    ),
    _spec(
        "days_to_nearest_related_claim",
        _EPISODE,
        "Days to the closest related claim by submission time.",
        NO_RELATED_CLAIM_DAYS,
        "A year stands in for no related claim; zero would read as a same-day repeat.",
    ),
    _spec(
        "repeated_line_fingerprint_ratio",
        _EPISODE,
        "Share of billed lines whose code, quantity, and amount also appear on a prior claim.",
        0.0,
        "Nothing to repeat when no prior claim was supplied.",
    ),
    _spec(
        "exact_claim_fingerprint_match",
        _EPISODE,
        "One when the full set of billed lines is identical to a prior claim, zero otherwise.",
        0.0,
        "Nothing to match when no prior claim was supplied.",
    ),
    _spec(
        "max_history_procedure_jaccard",
        _SIMILARITY,
        "Highest overlap between this visit's procedure codes and a prior visit's.",
        0.0,
        "No procedure record or no prior claim leaves nothing to overlap.",
    ),
    _spec(
        "max_history_condition_jaccard",
        _SIMILARITY,
        "Highest overlap between this visit's recorded condition codes and a prior visit's.",
        0.0,
        "No condition record or no prior claim leaves nothing to overlap.",
    ),
    _spec(
        "service_sequence_distance",
        _SIMILARITY,
        "Edit distance between this claim's ordered service codes and the closest prior claim's.",
        MAXIMALLY_DIFFERENT,
        "With nothing to compare against, the sequence is treated as maximally different.",
    ),
    _spec(
        "duplicate_note_digest_count",
        _SIMILARITY,
        "Notes whose content digest is identical to a note filed elsewhere at this facility.",
        0.0,
        "No note, or no facility notes to compare against, means nothing to duplicate.",
    ),
    _spec(
        "line_count_peer_deviation",
        _PEER,
        "How far this claim's billed-line count sits from the facility's usual, robustly scaled.",
        NO_DEVIATION,
        "An unseen facility gives no grounds to call a claim unusual.",
    ),
    _spec(
        "total_amount_peer_deviation",
        _PEER,
        "How far this claim's total sits from the facility's usual, robustly scaled.",
        NO_DEVIATION,
        "An unseen facility gives no grounds to call a claim unusual.",
    ),
    _spec(
        "unseen_service_code_ratio",
        _PEER,
        "Share of billed codes this facility has not billed before.",
        NO_DEVIATION,
        "An unseen facility has no established code vocabulary to be outside of.",
    ),
    _spec(
        "missing_provenance_ratio",
        _PROVENANCE,
        "Share of records in the bundle carrying no provenance entry.",
        0.0,
        "An empty bundle has no record whose provenance could be missing.",
    ),
    _spec(
        "missing_authorship_ratio",
        _PROVENANCE,
        "Share of notes filed with no recorded author.",
        0.0,
        "A bundle with no note has no missing author.",
    ),
    _spec(
        "provenance_version_mismatch_count",
        _PROVENANCE,
        "Provenance entries recorded under a different schema version than the bundle.",
        0.0,
        "Counted directly.",
    ),
    _spec(
        "reconciliation_delta_ratio",
        _AMOUNT,
        "Gap between the claim total and the sum of its lines, as a share of the total.",
        0.0,
        "A claim with no total and no lines reconciles trivially.",
    ),
    _spec(
        "line_arithmetic_error_count",
        _AMOUNT,
        "Lines where quantity times unit price does not reach the billed line amount.",
        0.0,
        "Counted directly.",
    ),
    _spec(
        "max_line_amount_share",
        _AMOUNT,
        "The largest single line's share of the claim total.",
        0.0,
        "No line, or a zero total, leaves no share to compute.",
    ),
)

FEATURE_NAMES: tuple[str, ...] = tuple(spec.name for spec in FEATURE_SCHEMA)

_BY_NAME: dict[str, FeatureSpec] = {spec.name: spec for spec in FEATURE_SCHEMA}


def spec_for(name: str) -> FeatureSpec:
    """Look up one column. Raises when a name is not in the schema."""
    try:
        return _BY_NAME[name]
    except KeyError as exc:
        raise KeyError(f"{name!r} is not a declared feature") from exc


def specs_for_family(family: FeatureFamily) -> tuple[FeatureSpec, ...]:
    return tuple(spec for spec in FEATURE_SCHEMA if spec.family is family)


class FeatureRow(BaseModel):
    """One bundle's features, in schema order, with every imputed column named."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    bundle_id: str
    values: tuple[float, ...]
    imputed: tuple[str, ...] = ()
    """Columns that carry a declared stand-in rather than a measurement."""

    feature_version: str = FEATURE_VERSION

    @property
    def names(self) -> tuple[str, ...]:
        return FEATURE_NAMES

    def as_mapping(self) -> dict[str, float]:
        return dict(zip(FEATURE_NAMES, self.values, strict=True))

    def value_of(self, name: str) -> float:
        return self.as_mapping()[spec_for(name).name]
