"""The five gates. Any failure rejects the whole briefing; nothing is trimmed."""
from __future__ import annotations

import pytest
from tilik_domain.versioning import EngineIdentity

from app.dto.briefing import BriefingObservation, BriefingQuestion
from app.dto.cases import CaseDetailResponse
from app.dto.common import EvidenceRefDto
from app.service.briefing.template import template_briefing
from app.service.briefing.validation import FORBIDDEN_TERMS, validate_briefing
from tests.test_case_endpoints import ingest_and_screen


@pytest.fixture
def detail(api) -> CaseDetailResponse:
    screened = ingest_and_screen(api, "phantom")
    return CaseDetailResponse.model_validate(api.get(f"/v1/cases/{screened['case_id']}").json())


def _briefing(detail, **changes):
    base = template_briefing(detail, EngineIdentity())
    return base.model_copy(update=changes)


def _ref(detail) -> EvidenceRefDto:
    return detail.reasons[0].evidence[0]


def test_an_observation_citing_an_unknown_resource_rejects_the_whole_briefing(detail) -> None:
    bad = BriefingObservation(
        statement="Kunjungan ENC-GHOST tidak tercatat.",
        kind="EVIDENCE_GAP",
        source_refs=(EvidenceRefDto(resource_type="Encounter", resource_id="ENC-GHOST", label="x"),),
        confidence="STATED",
    )
    briefing = _briefing(detail, observations=(*template_briefing(detail, EngineIdentity()).observations[:1], bad))
    verdict = validate_briefing(briefing, detail, supplied_text="ENC-GHOST")
    assert not verdict.accepted
    assert "ENC-GHOST" in (verdict.reason or "")


def test_a_number_absent_from_the_supplied_text_rejects_the_briefing(detail) -> None:
    invented = BriefingObservation(
        statement="Tiga dari 7 baris tidak berdokumen.",
        kind="COMPLETENESS",
        source_refs=(_ref(detail),),
        confidence="INFERRED",
    )
    verdict = validate_briefing(_briefing(detail, observations=(invented,)), detail, supplied_text="1/2 baris")
    assert not verdict.accepted
    assert "7" in (verdict.reason or "")


def test_a_number_present_in_the_supplied_text_is_allowed(detail) -> None:
    fine = BriefingObservation(
        statement="Baris 88.71 tidak punya catatan tindakan.",
        kind="EVIDENCE_GAP",
        source_refs=(_ref(detail),),
        confidence="STATED",
    )
    verdict = validate_briefing(_briefing(detail, observations=(fine,)), detail, supplied_text="kode 88.71 ada")
    assert verdict.accepted, verdict.reason


@pytest.mark.parametrize("word", FORBIDDEN_TERMS)
def test_forbidden_terms_reject_the_briefing(detail, word: str) -> None:
    loaded = BriefingObservation(
        statement=f"Klaim ini {word} menurut catatan.",
        kind="CORROBORATION",
        source_refs=(_ref(detail),),
        confidence="INFERRED",
    )
    verdict = validate_briefing(_briefing(detail, observations=(loaded,)), detail, supplied_text="")
    assert not verdict.accepted
    assert word in (verdict.reason or "")


def test_a_question_with_an_unknown_reference_also_rejects(detail) -> None:
    question = BriefingQuestion(
        question="Apakah catatan tindakan ada di sistem lain?",
        why_it_matters="Menentukan apakah bukti sekadar tidak terkirim.",
        source_refs=(EvidenceRefDto(resource_type="Procedure", resource_id="PROC-GHOST", label="x"),),
    )
    verdict = validate_briefing(_briefing(detail, open_questions=(question,)), detail, supplied_text="")
    assert not verdict.accepted


def test_observation_and_question_caps_are_enforced_by_the_schema(detail) -> None:
    one = template_briefing(detail, EngineIdentity()).observations[0]
    with pytest.raises(ValueError):
        _briefing(detail, observations=(one,) * 6).model_validate(_briefing(detail, observations=(one,) * 6).model_dump())


def test_an_observation_without_refs_cannot_be_constructed() -> None:
    with pytest.raises(ValueError):
        BriefingObservation(statement="x", kind="TIMELINE", source_refs=(), confidence="STATED")
