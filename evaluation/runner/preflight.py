"""Gates that run **before** any metric is computed.

`docs/canonical/06_evaluation_plan.md` § Experimental protocol puts schema and leakage tests
before the evaluation, and the order is the point: a metric computed on a leaking or
unjoinable corpus is a number someone might believe. Producing it and checking afterwards
means the number exists, and a number that exists gets quoted.

Every failure here halts the run. None of them is a warning.
"""
from __future__ import annotations

from dataclasses import dataclass

from tilik_data.leakage import carries_injector_suffix, probe
from tilik_data.split import GOLD_BUNDLE_IDS
from tilik_model.dataset import TEST, TRAIN, VALIDATION, BuildArtifacts, participants_of


class PreflightFailed(RuntimeError):
    """A gate failed. No metric may be computed until it is explained."""


@dataclass(frozen=True)
class PreflightReport:
    """What the gates checked and what they found, recorded beside the metrics."""

    bundles: int
    leakage_summary: str
    demo_fixtures_excluded: int
    train_participants_shared_with_test: int

    def summary(self) -> str:
        return (
            f"{self.bundles} bundles · {self.leakage_summary} · "
            f"{self.demo_fixtures_excluded} demo fixtures excluded"
        )


def run_preflight(artifacts: BuildArtifacts) -> PreflightReport:
    """Check the corpus before measuring anything against it."""
    published = {bundle.bundle_id for bundle in artifacts.bundles}

    _refuse_injector_traces(artifacts)
    _refuse_demo_fixtures(artifacts, published)
    report = probe(artifacts.bundles, frozenset(artifacts.labelled_bundle_ids))
    if report.leaked:
        raise PreflightFailed(
            f"leakage probe fired: {report.summary()}. Evaluation halts; report no metric "
            "until this is explained."
        )

    shared = participants_of(artifacts.partition(TRAIN)) & participants_of(
        artifacts.partition(TEST)
    )
    return PreflightReport(
        bundles=len(artifacts.bundles),
        leakage_summary=report.summary(),
        demo_fixtures_excluded=len(artifacts.excluded_demo),
        train_participants_shared_with_test=len(shared),
    )


def _refuse_injector_traces(artifacts: BuildArtifacts) -> None:
    """No published identifier may announce which injector touched a record."""
    marked = [
        bundle.bundle_id
        for bundle in artifacts.bundles
        for value in _identifier_strings(bundle.model_dump())
        if carries_injector_suffix(value)
    ]
    if marked:
        raise PreflightFailed(
            f"{len(marked)} published identifier(s) still carry an injector suffix, e.g. "
            f"{sorted(set(marked))[:3]}. Regenerate the corpus before evaluating."
        )


def _refuse_demo_fixtures(artifacts: BuildArtifacts, published: set[str]) -> None:
    """The five curated fixtures are the records most likely to have been looked at while tuning."""
    for partition in (TRAIN, VALIDATION, TEST):
        intruders = artifacts.partitions[partition] & GOLD_BUNDLE_IDS
        if intruders:
            raise PreflightFailed(
                f"demo fixture(s) {sorted(intruders)} reached the {partition} partition; "
                "they must never enter a metric."
            )
    stowaways = published & GOLD_BUNDLE_IDS
    if stowaways:
        raise PreflightFailed(f"demo fixture(s) {sorted(stowaways)} are in the corpus itself")


def _identifier_strings(node: object) -> list[str]:
    if isinstance(node, dict):
        return [value for item in node.values() for value in _identifier_strings(item)]
    if isinstance(node, list | tuple):
        return [value for item in node for value in _identifier_strings(item)]
    return [node] if isinstance(node, str) else []
