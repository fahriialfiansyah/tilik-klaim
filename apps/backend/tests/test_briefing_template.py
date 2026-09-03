"""The deterministic briefing — what ships when there is no LLM, which is the default."""
from __future__ import annotations

import pytest
from tilik_domain.versioning import EngineIdentity

from app.dto.cases import CaseDetailResponse
from app.service.briefing.template import template_briefing
from app.service.briefing.validation import FORBIDDEN_TERMS, validate_briefing
from tests.test_case_endpoints import ingest_and_screen

SCENARIOS = ("phantom", "repeat", "clone", "unbundled", "clean")


def _detail(api, scenario: str) -> CaseDetailResponse:
    screened = ingest_and_screen(api, scenario)
    return CaseDetailResponse.model_validate(api.get(f"/v1/cases/{screened['case_id']}").json())


@pytest.mark.parametrize("scenario", SCENARIOS)
def test_template_briefing_uses_no_forbidden_word(api, scenario: str) -> None:
    briefing = template_briefing(_detail(api, scenario), EngineIdentity())
    text = " ".join(
        [*(o.statement for o in briefing.observations),
         *(q.question + q.why_it_matters for q in briefing.open_questions),
         briefing.uncertainty_note]
    ).lower()
    for word in FORBIDDEN_TERMS:
        assert word not in text, f"{scenario}: template says {word!r}"


@pytest.mark.parametrize("scenario", SCENARIOS)
def test_every_template_observation_is_source_bound(api, scenario: str) -> None:
    briefing = template_briefing(_detail(api, scenario), EngineIdentity())
    for observation in briefing.observations:
        assert observation.source_refs, observation.statement
    assert briefing.uncertainty_note
    assert briefing.generated_by == "TEMPLATE"


@pytest.mark.parametrize("scenario", SCENARIOS)
def test_the_template_passes_its_own_validator(api, scenario: str) -> None:
    """The gate the LLM must pass is one the template passes trivially — or the gate is wrong."""
    detail = _detail(api, scenario)
    briefing = template_briefing(detail, EngineIdentity())
    verdict = validate_briefing(briefing, detail, supplied_text=detail.model_dump_json())
    assert verdict.accepted, verdict.reason


def test_a_quiet_case_says_nothing_was_observed_never_clean(api) -> None:
    briefing = template_briefing(_detail(api, "clean"), EngineIdentity())
    joined = " ".join(o.statement for o in briefing.observations).lower()
    assert "tidak ada risiko teramati" in joined or "tidak ada alasan" in joined
    assert "bersih" not in joined and "aman" not in joined


def test_template_needs_no_network(api, monkeypatch) -> None:
    import socket

    def explode(*args, **kwargs):
        raise AssertionError("the template reached for the network")

    monkeypatch.setattr(socket, "create_connection", explode)
    assert template_briefing(_detail(api, "phantom"), EngineIdentity()).observations
