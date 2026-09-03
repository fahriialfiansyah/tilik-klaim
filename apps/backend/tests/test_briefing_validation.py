"""The five gates. Any failure rejects the whole briefing; nothing is trimmed."""
from __future__ import annotations

import pytest
from tilik_domain.versioning import EngineIdentity

from app.dto.briefing import BriefingObservation, BriefingQuestion
from app.dto.cases import CaseDetailResponse
from app.dto.common import EvidenceRefDto
from app.service.briefing.template import template_briefing
from app.service.briefing.validation import validate_briefing
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


@pytest.mark.parametrize(
    "word", ["fraud", "curang", "kecurangan", "palsu", "pemalsuan", "sanksi", "denda", "terbukti"]
)
def test_an_accusing_word_rejects_the_briefing(detail, word: str) -> None:
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


class TestTheLexiconIsPreciseEnoughToBeUsable:
    """Indonesian attaches affixes to the stem, so a substring rule cannot tell an accusation
    from an ordinary word.

    Measured against the real gateway: matching the bare stem "bayar" rejected legitimate
    factual output on the repeat-billing and unbundling cases — the two modes where billing
    vocabulary is unavoidable — and silently degraded both to the template. What the canon
    forbids is an accusation or a directive, not the noun.
    """

    @pytest.mark.parametrize(
        "statement",
        [
            "Klaim ini diajukan untuk pembayaran layanan yang sama pada episode tersebut.",
            "Kedua klaim memiliki total tagihan yang sama dan waktu pengiriman berbeda.",
            "Diperlukan pemeriksaan untuk memastikan kelengkapan berkas pendukung.",
            "Catatan keamanan sistem tidak termasuk dalam bundel ini.",
            "Layanan tersebut sudah dibayarkan pada klaim sebelumnya menurut catatan.",
        ],
    )
    def test_ordinary_factual_language_is_not_rejected(self, detail, statement: str) -> None:
        observation = BriefingObservation(
            statement=statement,
            kind="COMPARISON",
            source_refs=(_ref(detail),),
            confidence="STATED",
        )
        verdict = validate_briefing(
            _briefing(detail, observations=(observation,)), detail, supplied_text=statement
        )
        assert verdict.accepted, verdict.reason

    @pytest.mark.parametrize(
        "statement",
        [
            "Pola ini mengindikasikan kecurangan pada fasilitas tersebut.",
            "Dokumen tersebut adalah hasil pemalsuan.",
            "Klaim ini harus ditolak oleh peninjau.",
            "Hentikan pembayaran untuk klaim ini.",
            "Fasilitas ini sebaiknya dikenakan sanksi.",
            "Sudah pasti bahwa layanan tidak diberikan.",
            "Klaim ini bersih dan tidak perlu ditinjau.",
            "Pembayaran klaim ini tidak boleh dibayarkan.",
        ],
    )
    def test_an_accusation_or_a_directive_is_still_rejected(self, detail, statement: str) -> None:
        observation = BriefingObservation(
            statement=statement,
            kind="COMPARISON",
            source_refs=(_ref(detail),),
            confidence="INFERRED",
        )
        verdict = validate_briefing(
            _briefing(detail, observations=(observation,)), detail, supplied_text=statement
        )
        assert not verdict.accepted, f"allowed: {statement}"

    def test_the_reason_quotes_what_was_written(self, detail) -> None:
        observation = BriefingObservation(
            statement="Pola ini mengindikasikan kecurangan.",
            kind="COMPARISON",
            source_refs=(_ref(detail),),
            confidence="INFERRED",
        )
        verdict = validate_briefing(
            _briefing(detail, observations=(observation,)), detail, supplied_text=""
        )
        assert "kecurangan" in (verdict.reason or "")


class TestHedgingIsNotAnAssertion:
    """The briefing is asked to state uncertainty. Banning the bare certainty word banned the
    hedge along with the assertion — measured, and it pushed good output to the template."""

    @pytest.mark.parametrize(
        "statement",
        [
            "Belum pasti apakah layanan tersebut diberikan pada kunjungan itu.",
            "Hal ini tidak terbukti dari bukti yang tersedia dalam bundel.",
            "Kaitan antara kedua klaim tidak dapat dipastikan dari catatan ini.",
            "Kelengkapan berkas belum terbukti dari sumber daya yang dirujuk.",
        ],
    )
    def test_a_negated_certainty_word_is_allowed(self, detail, statement: str) -> None:
        observation = BriefingObservation(
            statement=statement, kind="COMPLETENESS", source_refs=(_ref(detail),), confidence="INFERRED"
        )
        verdict = validate_briefing(
            _briefing(detail, observations=(observation,)), detail, supplied_text=statement
        )
        assert verdict.accepted, verdict.reason

    @pytest.mark.parametrize(
        "statement",
        [
            "Sudah pasti bahwa layanan tersebut tidak diberikan.",
            "Hal ini terbukti dari catatan yang tersedia.",
            "Klaim ini bersih menurut pemeriksaan.",
        ],
    )
    def test_an_asserted_certainty_word_is_still_rejected(self, detail, statement: str) -> None:
        observation = BriefingObservation(
            statement=statement, kind="COMPLETENESS", source_refs=(_ref(detail),), confidence="STATED"
        )
        verdict = validate_briefing(
            _briefing(detail, observations=(observation,)), detail, supplied_text=statement
        )
        assert not verdict.accepted, f"allowed: {statement}"
