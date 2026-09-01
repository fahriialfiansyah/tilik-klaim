"""One small corpus, written to disk and loaded back, shared by the whole test session.

The runner is only meaningful against artifacts that join, so the fixtures go through
`write_artifacts` and `load_build` exactly as a real run does rather than passing objects around
in memory. A run that works on in-memory objects and fails on the published files would be the
Sprint 01 defect a second time.
"""
from __future__ import annotations

import pytest
from tilik_data.pipeline import run as build_corpus
from tilik_data.pipeline import write_artifacts
from tilik_model.dataset import TRAIN, VALIDATION, load_build
from tilik_model.ranking import RankingModel

SEED = 20260902

CONFIG = {
    "seed": SEED,
    "corpus": {"claims": 260, "participants": 70, "providers": 6},
    "injections": {
        "per_mode": 10,
        "multi_label_ratio": 0.05,
        "difficulty_mix": {"obvious": 0.3, "moderate": 0.5, "subtle": 0.2},
    },
    "split": {"train": 0.6, "validation": 0.2, "test": 0.2, "provider_time_block_days": 30},
}


@pytest.fixture(scope="session")
def build_dir(tmp_path_factory):
    directory = tmp_path_factory.mktemp("build")
    write_artifacts(build_corpus(CONFIG), directory)
    return directory


@pytest.fixture(scope="session")
def artifacts(build_dir):
    return load_build(build_dir)


@pytest.fixture(scope="session")
def model(artifacts) -> RankingModel:
    return RankingModel.train(
        training_bundles=artifacts.partition(TRAIN),
        validation_bundles=artifacts.partition(VALIDATION),
        dataset_digest=artifacts.dataset_digest(),
    )
