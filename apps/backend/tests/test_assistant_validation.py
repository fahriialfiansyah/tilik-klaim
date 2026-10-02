"""The gate, check by check — ADR-0007 § 4.4.

Constructed answers rather than model output, so each test fails for exactly one reason.
"""
from __future__ import annotations

import pytest
from pydantic import ValidationError
from tilik_domain.canonical import ResourceType

from app.dto.assistant import (
    AnswerIntent,
    AnswerKind,
    AssistantAnswer,
    AssistantScope,
    AssistantStatement,
    Citation,
    CitationKind,
    GeneratedBy,
    ScopeKind,
)
from app.dto.common import VersionStamp
from app.service.assistant.validation import (
    Citable,
    forbidden_term,
    machine_token,
    validate_answer,
)

CASE_ID = "case_0123456789abcdef"
VERSIONS = VersionStamp(
    schema_version="0.1.0", ruleset_version="0.1.0", engine_version="0.1.0", dataset_version="t"
)
CITABLE = Citable(
    case_ids=frozenset({CASE_ID}),
    resources=frozenset({(CASE_ID, "Encounter", "ENC-1"), (CASE_ID, "ClaimLine", "LN-2")}),
    queue_allowed=True,
)
SUPPLIED = '{"supported_lines": 1, "total_lines": 2, "resource_id": "ENC-1"}'


def case_ref() -> Citation:
    return Citation(kind=CitationKind.CASE, case_id=CASE_ID, label="Kasus")


def resource_ref(resource_id: str = "ENC-1", case_id: str = CASE_ID) -> Citation:
    return Citation(
        kind=CitationKind.RESOURCE,
        case_id=case_id,
        resource_type=ResourceType.ENCOUNTER,
        resource_id=resource_id,
        label=f"kunjungan {resource_id}",
    )


def answer(text: str, *citations: Citation, note: str = "Hanya dari bukti yang terkirim.") -> AssistantAnswer:
    return AssistantAnswer(
        question="q",
        scope=AssistantScope(kind=ScopeKind.QUEUE),
        kind=AnswerKind.ANSWER,
        intent=AnswerIntent.OPEN_QUESTION,
        statements=(AssistantStatement(text=text, citations=citations or (case_ref(),)),),
        uncertainty_note=note,
        generated_by=GeneratedBy.LLM,
        prompt_version="t",
        versions=VERSIONS,
    )


def test_a_cited_factual_answer_passes() -> None:
    verdict = validate_answer(answer("1 dari 2 baris tagihan didukung bukti.", resource_ref()), CITABLE, SUPPLIED)
    assert verdict.accepted, verdict.reason


def test_a_statement_without_a_citation_cannot_even_be_built() -> None:
    with pytest.raises(ValidationError):
        AssistantStatement(text="Tanpa rujukan.", citations=())


def test_a_citation_to_a_resource_that_was_not_read_is_rejected() -> None:
    verdict = validate_answer(answer("Ada catatan.", resource_ref("ENC-999")), CITABLE, SUPPLIED)
    assert not verdict.accepted
    assert "ENC-999" in (verdict.reason or "")


def test_a_citation_to_a_case_outside_the_queue_is_rejected() -> None:
    other = Citation(kind=CitationKind.CASE, case_id="case_elsewhere", label="Kasus")
    assert not validate_answer(answer("Ada kasus.", other), CITABLE, SUPPLIED).accepted


def test_a_queue_citation_is_rejected_inside_a_case_scope() -> None:
    queue = Citation(kind=CitationKind.QUEUE, label="Antrean Review")
    case_only = Citable(case_ids=CITABLE.case_ids, resources=CITABLE.resources, queue_allowed=False)
    assert not validate_answer(answer("Antrean.", queue), case_only, SUPPLIED).accepted


def test_a_number_the_tools_never_supplied_is_rejected() -> None:
    verdict = validate_answer(answer("7 dari 9 baris didukung.", resource_ref()), CITABLE, SUPPLIED)
    assert not verdict.accepted
    assert "unsupported number" in (verdict.reason or "")


@pytest.mark.parametrize(
    "text",
    [
        "Fasilitas ini melakukan kecurangan.",
        "Dokumen ini dipalsukan.",
        "Klaim ini terbukti bermasalah.",
        "Klaim harus ditolak.",
        "This provider committed fraud.",
        "The claim should be rejected.",
        "This claim is clean.",
        "The record was forged.",
    ],
)
def test_accusation_and_directive_are_rejected_in_both_languages(text: str) -> None:
    verdict = validate_answer(answer(text, resource_ref()), CITABLE, SUPPLIED)
    assert not verdict.accepted, text
    assert "forbidden term" in (verdict.reason or "")


@pytest.mark.parametrize(
    "text",
    [
        "Hal ini belum terbukti dari bundel.",
        "Ketiadaan catatan tidak pasti berarti layanan tidak diberikan.",
        "That a service was missed is not proven by the bundle.",
        "Kunjungan ENC-1 tercatat.",
    ],
)
def test_hedges_and_identifiers_are_not_accusations(text: str) -> None:
    assert forbidden_term(text) is None, text


def test_a_resource_id_containing_a_forbidden_word_is_an_identifier() -> None:
    assert forbidden_term("Encounter ENC-CLEAN-1 recorded at 15:00.") is None


def test_a_blank_uncertainty_note_is_rejected() -> None:
    verdict = validate_answer(answer("Ada kunjungan.", resource_ref(), note="   "), CITABLE, SUPPLIED)
    assert not verdict.accepted


def test_a_refusal_is_never_a_generated_answer() -> None:
    refusal = AssistantAnswer(
        question="q",
        scope=AssistantScope(),
        kind=AnswerKind.HELP,
        intent=AnswerIntent.UNRECOGNISED,
        notice="Tidak dikenali.",
        uncertainty_note="-",
        generated_by=GeneratedBy.LLM,
        prompt_version="t",
        versions=VERSIONS,
    )
    assert not validate_answer(refusal, CITABLE, SUPPLIED).accepted


def test_answer_shape_follows_its_kind() -> None:
    with pytest.raises(ValidationError):
        AssistantAnswer(
            question="q",
            scope=AssistantScope(),
            kind=AnswerKind.ANSWER,
            intent=AnswerIntent.OPEN_QUESTION,
            uncertainty_note="-",
            generated_by=GeneratedBy.TEMPLATE,
            prompt_version="t",
            versions=VERSIONS,
        )
    with pytest.raises(ValidationError):
        Citation(kind=CitationKind.RESOURCE, case_id=CASE_ID, label="half-built")
    with pytest.raises(ValidationError):
        AssistantScope(kind=ScopeKind.CASE)


@pytest.mark.parametrize(
    "text",
    [
        "Kasus ini berprioritas DETERMINISTIC_CONFLICT.",
        "Semua kasus berstatus SCREENED.",
        "Polanya REPEAT_BILLING.",
        "Alasannya LINE_WITHOUT_COMPLETED_PROCEDURE.",
    ],
)
def test_a_raw_machine_token_is_rejected(text: str) -> None:
    """The owner's rule: codes never reach the reading surface — measured leaking on 2 Oct."""
    verdict = validate_answer(answer(text, resource_ref()), CITABLE, SUPPLIED + text)
    assert not verdict.accepted
    assert "machine token" in (verdict.reason or "")


def test_human_labels_and_identifiers_are_not_machine_tokens() -> None:
    assert machine_token("Kasus berprioritas Konflik deterministik, kunjungan ENC-1.") is None


def test_a_digit_does_not_launder_an_accusation() -> None:
    """Only id-shaped tokens are masked; "fraud2" is still the word fraud."""
    assert forbidden_term("This looks like fraud2 to me.") is not None


def test_numbers_match_as_whole_values_not_as_substrings() -> None:
    supplied = '{"year": 2017, "hours": 144.04}'
    assert not validate_answer(answer("7 kasus.", resource_ref()), CITABLE, supplied).accepted
    assert validate_answer(answer("Median 144,04 jam.", resource_ref()), CITABLE, supplied).accepted


def test_digits_inside_ids_are_not_numbers() -> None:
    text = "Kasus case_c459a18… merujuk ENC-1."
    assert validate_answer(answer(text, resource_ref()), CITABLE, '{"x": 0}').accepted
