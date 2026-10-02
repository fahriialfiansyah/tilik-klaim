"""The template path, over every gold scenario, every intent, both languages.

This is the path the offline demo runs, so it is held to the model path's own gate: every
statement cites something, every citation opens — a case in the queue, or a resource in that
case's own source index — and nothing in it accuses, decides, or reassures.
"""
from __future__ import annotations

import pytest

from app.dto.assistant import AnswerKind, AssistantAnswer, CitationKind
from app.service.assistant.validation import forbidden_term, machine_token
from tests.test_case_endpoints import ingest_and_screen

SCENARIOS = ("phantom", "repeat", "clone", "unbundled", "clean")

QUEUE_QUESTIONS = {
    "id": (
        "Ringkas kondisi antrean",
        "Kasus mana yang perlu dibuka dulu?",
        "Kasus apa saja dengan tagihan berulang?",
        "Berapa kasus berprioritas konflik deterministik?",
        "Kasus mana yang menunggu bukti?",
    ),
    "en": (
        "Give me an overview of the queue",
        "Which case should I open first?",
        "Which cases show repeat billing?",
        "How many cases are in the deterministic conflict band?",
    ),
}

CASE_QUESTIONS = {
    "id": (
        "Ringkas kasus ini",
        "Mengapa kasus ini muncul?",
        "Bukti apa yang belum ditemukan?",
        "Apa yang melemahkan alasan ini?",
        "Bagaimana urutan kejadiannya?",
        "Dengan apa kasus ini dibandingkan?",
    ),
    "en": (
        "Summarise this case",
        "Why was this case raised?",
        "What evidence is missing?",
        "What argues against this reason?",
        "Show the timeline",
        "What is this case compared with?",
    ),
}


@pytest.fixture
def seeded(api) -> dict[str, str]:
    return {scenario: ingest_and_screen(api, scenario)["case_id"] for scenario in SCENARIOS}


def ask(api, question: str, scope: dict | None = None, locale: str = "id") -> AssistantAnswer:
    response = api.post(
        "/v1/assistant/answers?stream=false",
        json={"question": question, **({"scope": scope} if scope else {})},
        headers={"Accept-Language": locale},
    )
    assert response.status_code == 200, response.text
    return AssistantAnswer.model_validate(response.json())


def assert_every_citation_opens(api, answer: AssistantAnswer) -> None:
    queue_ids = {row["case_id"] for row in api.get("/v1/cases?page_size=200").json()["items"]}
    sources: dict[str, set[tuple[str, str]]] = {}
    for statement in answer.statements:
        assert statement.citations, statement.text
        for citation in statement.citations:
            if citation.kind is CitationKind.CASE:
                assert citation.case_id in queue_ids
            elif citation.kind is CitationKind.RESOURCE:
                case_id = str(citation.case_id)
                if case_id not in sources:
                    detail = api.get(f"/v1/cases/{case_id}").json()
                    sources[case_id] = {
                        (s["resource_type"], s["resource_id"])
                        for s in detail["sources"]
                        if s["availability"] != "MISSING"
                    }
                assert (str(citation.resource_type), citation.resource_id) in sources[case_id]
    for card in answer.cases:
        assert card.case.case_id in queue_ids


def assert_says_nothing_forbidden(answer: AssistantAnswer) -> None:
    text = " ".join([*(s.text for s in answer.statements), answer.uncertainty_note])
    assert forbidden_term(text) is None, text
    assert machine_token(text) is None, text


@pytest.mark.parametrize("locale", ["id", "en"])
def test_every_queue_answer_is_cited_and_clean(api, seeded, locale) -> None:
    for question in QUEUE_QUESTIONS[locale]:
        answer = ask(api, question, locale=locale)
        assert answer.kind is AnswerKind.ANSWER, question
        assert answer.generated_by == "TEMPLATE"
        assert_every_citation_opens(api, answer)
        assert_says_nothing_forbidden(answer)


@pytest.mark.parametrize("scenario", SCENARIOS)
@pytest.mark.parametrize("locale", ["id", "en"])
def test_every_case_answer_is_cited_and_clean(api, seeded, scenario, locale) -> None:
    scope = {"kind": "CASE", "case_id": seeded[scenario]}
    for question in CASE_QUESTIONS[locale]:
        answer = ask(api, question, scope, locale)
        assert answer.kind is AnswerKind.ANSWER, question
        assert answer.scope.case_id == seeded[scenario]
        assert_every_citation_opens(api, answer)
        assert_says_nothing_forbidden(answer)


def test_where_to_start_points_at_the_queue_order_and_never_its_own(api, seeded) -> None:
    queue = api.get("/v1/cases?page_size=200").json()["items"]
    awaiting = [row for row in queue if row["state"] in ("SCREENED", "IN_REVIEW")]
    answer = ask(api, "Kasus mana yang perlu dibuka dulu?")
    assert [card.case.case_id for card in answer.cases] == [row["case_id"] for row in awaiting[:3]]
    assert [card.queue_position for card in answer.cases] == sorted(
        card.queue_position for card in answer.cases
    )
    assert answer.statements[0].citations[0].case_id == awaiting[0]["case_id"]
    assert any("urutan" in s.text.lower() for s in answer.statements)


def test_a_filter_with_no_match_says_so_and_cites_the_queue(api, seeded) -> None:
    answer = ask(api, "Kasus mana yang sinyalnya ditolak?")
    assert answer.kind is AnswerKind.ANSWER
    assert answer.cases == ()
    assert answer.statements[0].citations[0].kind is CitationKind.QUEUE


def test_a_case_named_in_the_queue_scope_is_explained(api, seeded) -> None:
    prefix = seeded["phantom"][:12]
    answer = ask(api, f"Jelaskan {prefix}…")
    assert [card.case.case_id for card in answer.cases] == [seeded["phantom"]]
    assert_every_citation_opens(api, answer)


def test_an_unknown_case_prefix_is_an_answer_about_the_queue_not_an_error(api, seeded) -> None:
    answer = ask(api, "Jelaskan case_ffffffffffff")
    assert answer.kind is AnswerKind.ANSWER
    assert answer.cases == ()


def test_the_quiet_case_says_nothing_about_the_claim(api, seeded) -> None:
    answer = ask(api, "Mengapa kasus ini muncul?", {"kind": "CASE", "case_id": seeded["clean"]})
    assert "bukan pernyataan tentang klaimnya" in answer.statements[0].text


def test_english_answers_are_english(api, seeded) -> None:
    answer = ask(
        api, "What is this case compared with?", {"kind": "CASE", "case_id": seeded["clone"]}, "en"
    )
    joined = " ".join(s.text for s in answer.statements)
    assert "Compared with" in joined
    assert "Template-based documentation" in joined
    assert "Dokumentasi" not in joined


def test_unrecognised_is_help_and_refused_is_refusal(api, seeded) -> None:
    help_answer = ask(api, "Halo, apa kabar?")
    assert help_answer.kind is AnswerKind.HELP
    assert help_answer.statements == ()
    assert help_answer.notice

    refused = ask(api, "Apakah kasus ini fraud?")
    assert refused.kind is AnswerKind.REFUSAL
    assert refused.refusal_topic == "VERDICT"
    assert refused.tool_calls == ()
