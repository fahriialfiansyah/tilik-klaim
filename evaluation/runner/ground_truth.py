"""Read the injection ground truth, with the breakdown dimensions the evaluation plan requires.

**These are injection ground-truth labels, never fraud labels.** A label records what the
generator deliberately changed — a fact about our test design, not a finding about conduct.

`tilik_model.dataset.load_build` keeps only which bundles are labelled, because that is all a
model may see. Evaluation needs more: difficulty and multi-label status are required breakdowns
in `docs/canonical/06_evaluation_plan.md` § Experimental protocol, and reporting recall without
difficulty hides the shape of a detector's failures — catching every obvious case while missing
every subtle one is a very different result from uniform performance.
"""
from __future__ import annotations

import json
from pathlib import Path

from tilik_domain.canonical import CanonicalBundle
from tilik_domain.reasons import RiskMode

from runner.metrics import GroundTruth

MIXED_DIFFICULTY = "mixed"
"""A bundle carrying injections at two difficulties is reported as mixed, never as either one."""

CLEAN = "clean"


def load_ground_truth(
    directory: Path, bundles: tuple[CanonicalBundle, ...]
) -> tuple[GroundTruth, ...]:
    """One record per bundle, clean ones included — they are the false-positive denominator."""
    labels = json.loads((directory / "labels.json").read_text(encoding="utf-8"))["labels"]

    modes: dict[str, set[RiskMode]] = {}
    difficulties: dict[str, set[str]] = {}
    multi: dict[str, bool] = {}
    for label in labels:
        for bundle_id in label["target_bundle_ids"]:
            modes.setdefault(bundle_id, set()).add(RiskMode(label["mode"]))
            difficulties.setdefault(bundle_id, set()).add(str(label["difficulty"]))
            multi[bundle_id] = multi.get(bundle_id, False) or bool(label["is_multi_label"])

    return tuple(
        GroundTruth(
            bundle_id=bundle.bundle_id,
            modes=frozenset(modes.get(bundle.bundle_id, ())),
            difficulty=_difficulty_of(difficulties.get(bundle.bundle_id, set())),
            is_multi_label=multi.get(bundle.bundle_id, False),
        )
        for bundle in bundles
    )


def _difficulty_of(levels: set[str]) -> str:
    if not levels:
        return CLEAN
    return levels.pop() if len(levels) == 1 else MIXED_DIFFICULTY
