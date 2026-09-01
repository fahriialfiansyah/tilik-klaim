"""One command that produces the whole corpus and its artifacts.

Order matters and is enforced: generate → verify clean → inject → strip injector traces →
split → probe for leakage → write the data card. The probe runs **after** the traces are
stripped and **before** anything is reported, because a leaking corpus must halt the run rather
than produce numbers someone might believe.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import yaml
from tilik_domain.canonical import CanonicalBundle

from tilik_data.amounts import ROUNDING_TOLERANCE
from tilik_data.corpus import InjectionPlan, build_corpus
from tilik_data.data_card import CorpusStats, missing_elements, render
from tilik_data.generator import corpus_hash
from tilik_data.injectors.labels import LabelSet
from tilik_data.leakage import (
    LeakageReport,
    injector_free_ids,
    probe,
    rename_labels,
    strip_injector_traces,
)
from tilik_data.manifest import GENERATOR_VERSION, Manifest
from tilik_data.split import Split, SplitRatios, make_split


class LeakageDetected(RuntimeError):
    """The probe fired. No metric may be reported until this is explained."""


@dataclass(frozen=True)
class BuildResult:
    """What a run publishes — and only that.

    There is deliberately no pre-strip corpus on this type. `write_artifacts` used to reach past
    the scrub and write the corpus as the injectors left it, which published the tell and left
    the split unjoinable; holding only the scrubbed corpus and the labels renamed to match makes
    that mistake unrepresentable rather than merely fixed.
    """

    bundles: tuple[CanonicalBundle, ...]
    labels: LabelSet
    split: Split
    manifest: Manifest
    leakage: LeakageReport
    data_card: str


def load_config(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def run(config: dict, *, halt_on_leak: bool = True) -> BuildResult:
    """Build everything. Raises `LeakageDetected` if the corpus is answerable from ids alone."""
    seed = int(config["seed"])
    corpus_config = config["corpus"]
    injection_config = config["injections"]
    split_config = config["split"]

    plan = InjectionPlan(
        per_mode=int(injection_config["per_mode"]),
        multi_label_ratio=float(injection_config["multi_label_ratio"]),
        difficulty_mix=dict(injection_config["difficulty_mix"]),
    )
    corpus = build_corpus(
        seed,
        claims=int(corpus_config["claims"]),
        participants=int(corpus_config["participants"]),
        providers=int(corpus_config["providers"]),
        plan=plan,
    )

    # Strip what the injectors left behind before anything measures the corpus. The labels go
    # through the *same* rename, so ground truth still names records that exist.
    renaming = injector_free_ids(corpus.bundles, seed)
    cleaned = strip_injector_traces(corpus.bundles, seed)
    labels = rename_labels(corpus.labels, renaming)
    renamed_injected = labels.bundle_ids()

    split = make_split(
        cleaned,
        ratios=SplitRatios(
            train=float(split_config["train"]),
            validation=float(split_config["validation"]),
            test=float(split_config["test"]),
        ),
        block_days=int(split_config["provider_time_block_days"]),
        seed=seed,
    )

    report = probe(cleaned, renamed_injected)
    if report.leaked and halt_on_leak:
        raise LeakageDetected(
            f"{report.summary()} — evaluation halts. Report no metric until this is explained."
        )

    stats = CorpusStats(
        bundles=len(cleaned),
        participants=int(corpus_config["participants"]),
        providers=int(corpus_config["providers"]),
        injections=len(labels.labels),
        injections_by_mode=labels.counts_by_mode(),
        multi_label_ratio=labels.multi_label_ratio(),
        train=len(split.train),
        validation=len(split.validation),
        test=len(split.test),
        excluded_demo=len(split.excluded_demo),
        corpus_hash=corpus_hash(cleaned),
        seed=seed,
        leakage_summary=report.summary(),
    )
    card = render(
        stats,
        generator_version=GENERATOR_VERSION,
        rounding_tolerance=str(ROUNDING_TOLERANCE),
    )
    absent = missing_elements(card)
    if absent:
        raise RuntimeError(f"data card is missing required elements: {absent}")

    manifest = Manifest.stamped(
        seed=seed,
        corpus_hash=stats.corpus_hash,
        bundles=stats.bundles,
        participants=stats.participants,
        providers=stats.providers,
        injections=stats.injections,
        injections_by_mode=stats.injections_by_mode,
        multi_label_ratio=stats.multi_label_ratio,
        train=stats.train,
        validation=stats.validation,
        test=stats.test,
        excluded_demo=stats.excluded_demo,
        test_set_digest=split.frozen_at,
        leakage_margin=report.margin,
        leakage_passed=not report.leaked,
    )
    return BuildResult(cleaned, labels, split, manifest, report, card)


def write_artifacts(result: BuildResult, out_dir: Path) -> None:
    """Persist the corpus, labels, split, manifest, and data card.

    Everything written here comes from the same scrubbed, renamed run, so the four files join on
    one id space. `tests/test_artifacts.py` asserts that on the files themselves rather than on
    the in-memory result — the distinction is exactly what went wrong before.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "manifest.json").write_text(
        result.manifest.model_dump_json(indent=2), encoding="utf-8"
    )
    (out_dir / "DATA_CARD.md").write_text(result.data_card, encoding="utf-8")
    (out_dir / "labels.json").write_text(
        result.labels.model_dump_json(indent=2), encoding="utf-8"
    )
    (out_dir / "split.json").write_text(
        json.dumps(
            {
                "train": sorted(result.split.train),
                "validation": sorted(result.split.validation),
                "test": sorted(result.split.test),
                "excluded_demo": sorted(result.split.excluded_demo),
                "test_set_digest": result.split.frozen_at,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    (out_dir / "corpus.json").write_text(
        json.dumps(
            [bundle.model_dump(mode="json") for bundle in result.bundles],
            separators=(",", ":"),
            default=str,
        ),
        encoding="utf-8",
    )


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Generate the TilikKlaim synthetic corpus.")
    parser.add_argument("--config", default="config/generator.yaml", type=Path)
    parser.add_argument("--out", default="build", type=Path)
    args = parser.parse_args()

    result = run(load_config(args.config))
    write_artifacts(result, args.out)

    manifest = result.manifest
    print(f"corpus     {manifest.bundles} bundles, hash {manifest.corpus_hash[:16]}")
    print(f"injections {manifest.injections}  {manifest.injections_by_mode}")
    print(f"multi-label {manifest.multi_label_ratio:.3f}")
    print(f"split      train {manifest.train} / val {manifest.validation} / test {manifest.test}")
    print(f"leakage    {result.leakage.summary()}")
    print(f"artifacts  {args.out.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
