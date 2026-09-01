"""One small, real corpus for the whole test session.

Built through `tilik_data.pipeline.run`, not from a checked-in fixture, so these tests exercise
the same scrub, split, and labels that ship — and so a change to the generator that would break
the model layer fails here rather than in Sprint 06.
"""
from __future__ import annotations

import pytest
from tilik_data.pipeline import run, write_artifacts

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
def build():
    """The published artifacts of one generation run, exactly as `write_artifacts` would."""
    return run(CONFIG)


@pytest.fixture(scope="session")
def bundles(build):
    return build.bundles


@pytest.fixture(scope="session")
def by_id(bundles):
    return {bundle.bundle_id: bundle for bundle in bundles}


@pytest.fixture(scope="session")
def build_dir(build, tmp_path_factory):
    """The run written to disk exactly as `packages/data` publishes it."""
    directory = tmp_path_factory.mktemp("build")
    write_artifacts(build, directory)
    return directory
