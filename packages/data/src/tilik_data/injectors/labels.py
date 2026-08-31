"""Injection ground-truth labels.

**These are injection ground-truth labels, never "fraud labels".** The naming discipline is not
cosmetic: a label here records *what this generator deliberately changed*, which is a fact about
our test design. It is not a finding about anyone's conduct, and it could not be — no person
exists behind these records. Calling the field `is_fraud` anywhere in code, docs, or the
proposal would smuggle in a claim the data cannot support.

Every label carries what an evaluation needs to be objective: which rule *should* fire, which
resources a correct explanation *should* point at, and how hard the case was meant to be. A
detector that fires for the wrong reason is not a success, and without expected evidence
references there would be no way to tell the difference.

`excluded_from_features` exists because these records are the most dangerous leak in the
project. Any of this reaching a feature table would let a model learn the answer key rather than
the pattern. → `docs/canonical/04_data_card.md` § Leakage controls.
"""
from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field
from tilik_domain.canonical import ResourceRef
from tilik_domain.reasons import ReasonCode, RiskMode

INJECTOR_VERSION = "0.1.0"
"""Bumped whenever an injector's behaviour changes, so old labels stay interpretable."""


class Difficulty(StrEnum):
    """How hard the injection was meant to be to spot.

    Reporting recall without this hides the shape of a detector's failures: catching every
    obvious case while missing every subtle one is a very different result from uniform
    performance, and only one of them is worth deploying.
    """

    OBVIOUS = "obvious"
    MODERATE = "moderate"
    SUBTLE = "subtle"


class InjectionLabel(BaseModel):
    """Ground truth for one injected pattern."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    injection_id: str
    mode: RiskMode
    difficulty: Difficulty

    source_bundle_id: str
    """The verified-clean bundle the injection was derived from."""
    target_bundle_ids: tuple[str, ...]
    """Every bundle the injection touched. More than one for repeat and unbundling."""

    expected_reason_codes: tuple[ReasonCode, ...]
    """What a correct detector should emit. Firing for another reason is not a hit."""
    expected_evidence_refs: tuple[ResourceRef, ...] = ()
    """What a correct explanation should point at."""
    violated_invariants: tuple[str, ...] = ()
    """Which documented normal pattern this injection breaks, in working language."""

    injector_version: str = INJECTOR_VERSION
    seed: int

    is_multi_label: bool = False
    """True when this bundle carries more than one injection."""

    excluded_from_features: bool = Field(
        default=True,
        description=(
            "Always true. Present as an explicit, checkable flag rather than a convention, "
            "so a leak is a failed assertion instead of an oversight."
        ),
    )


class LabelSet(BaseModel):
    """Every label from one generation run."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    labels: tuple[InjectionLabel, ...]
    seed: int
    injector_version: str = INJECTOR_VERSION

    def for_mode(self, mode: RiskMode) -> tuple[InjectionLabel, ...]:
        return tuple(label for label in self.labels if label.mode is mode)

    def bundle_ids(self) -> frozenset[str]:
        return frozenset(
            bundle_id for label in self.labels for bundle_id in label.target_bundle_ids
        )

    def multi_label_ratio(self) -> float:
        """Share of injections marked multi-label. Capped and reported, never left implicit."""
        if not self.labels:
            return 0.0
        return sum(1 for label in self.labels if label.is_multi_label) / len(self.labels)

    def counts_by_mode(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for label in self.labels:
            counts[str(label.mode)] = counts.get(str(label.mode), 0) + 1
        return counts
