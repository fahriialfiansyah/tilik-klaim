"""Reading the same case in either language.

The property under test is not "English works" — it is that **only the wording changes**. A
reviewer and an English-reading judge looking at one case must see the same reasons, the same
evidence, the same band and the same numbers, because a case that read differently in another
language would be a different case, and the audit trail cites only one of them.
"""
from __future__ import annotations

import pytest

from tests.fixtures import SCENARIOS, load

ENGLISH = {"Accept-Language": "en-US,en;q=0.9"}
INDONESIAN = {"Accept-Language": "id"}


def ingest_and_screen(api, scenario: str) -> dict:
    fixture = load(scenario)
    for prior in fixture.history:
        api.post("/v1/bundles", json=prior.model_dump(mode="json"))
    ingested = api.post("/v1/bundles", json=fixture.bundle.model_dump(mode="json")).json()
    return api.post(f"/v1/bundles/{ingested['ingestion_id']}/screen", json={}).json()


@pytest.fixture
def seeded(api):
    for scenario in SCENARIOS:
        ingest_and_screen(api, scenario)
    return api


def _by_id(items: list[dict]) -> dict[str, dict]:
    return {item["case_id"]: item for item in items}


# --------------------------------------------------------------------------------------
# The queue
# --------------------------------------------------------------------------------------


def test_queue_reason_sentences_are_english_when_english_is_asked_for(seeded) -> None:
    body = seeded.get("/v1/cases", headers=ENGLISH).json()
    sentences = " ".join(item["reason_sentence"] for item in body["items"])
    assert "record" in sentences or "claim" in sentences
    assert "Baris" not in sentences and "Klaim lain" not in sentences


def test_queue_defaults_to_the_working_language(seeded) -> None:
    """No header is not a request for English. Existing clients send none."""
    body = seeded.get("/v1/cases").json()
    sentences = " ".join(item["reason_sentence"] for item in body["items"])
    assert any(word in sentences for word in ("Baris", "Klaim", "Dokumentasi", "Layanan"))


def test_language_changes_the_wording_and_nothing_else(seeded) -> None:
    """Every field but the prose is identical across the two renderings."""
    indonesian = _by_id(seeded.get("/v1/cases", headers=INDONESIAN).json()["items"])
    english = _by_id(seeded.get("/v1/cases", headers=ENGLISH).json()["items"])

    assert set(indonesian) == set(english), "the queue held different cases per language"
    for case_id, row in indonesian.items():
        other = english[case_id]
        assert row["reason_sentence"] != other["reason_sentence"], f"{case_id} was not translated"
        for field in ("band", "state", "modes", "total_amount", "currency", "case_version"):
            assert row[field] == other[field], f"{case_id} disagreed about {field}"


# --------------------------------------------------------------------------------------
# The case detail
# --------------------------------------------------------------------------------------


def test_detail_renders_reasons_counter_evidence_and_band_in_english(seeded) -> None:
    """All three, because a screen that translates two of them is the worst outcome."""
    case_id = seeded.get("/v1/cases").json()["items"][0]["case_id"]
    detail = seeded.get(f"/v1/cases/{case_id}", headers=ENGLISH).json()

    assert detail["reasons"], "precondition: the case was raised for a reason"
    assert "Bundel" not in detail["band"]["basis"]
    assert "alasan teramati" not in detail["band"]["basis"]

    notes = " ".join(
        note["note"] for reason in detail["reasons"] for note in reason["counter_evidence_notes"]
    )
    assert notes, "precondition: reasons carry counter-evidence"
    assert "Bundel ini" not in notes and "bukan bukti" not in notes


def test_detail_evidence_and_scores_do_not_move_with_language(seeded) -> None:
    """The finding is one finding. Only its sentence has two forms."""
    case_id = seeded.get("/v1/cases").json()["items"][0]["case_id"]
    indonesian = seeded.get(f"/v1/cases/{case_id}", headers=INDONESIAN).json()
    english = seeded.get(f"/v1/cases/{case_id}", headers=ENGLISH).json()

    assert [r["code"] for r in indonesian["reasons"]] == [r["code"] for r in english["reasons"]]
    for left, right in zip(indonesian["reasons"], english["reasons"], strict=True):
        assert left["component_scores"] == right["component_scores"]
        assert left["evidence"] == right["evidence"]
        assert left["expected_support"] == right["expected_support"]
        assert left["deterministic"] == right["deterministic"]
        assert left["sentence"] != right["sentence"], f"{left['code']} was not translated"


def test_timeline_labels_follow_the_requested_language(seeded) -> None:
    case_id = seeded.get("/v1/cases").json()["items"][0]["case_id"]
    english = seeded.get(f"/v1/cases/{case_id}", headers=ENGLISH).json()
    labels = " ".join(event["label"] for event in english["timeline"])
    if labels:
        assert "Kunjungan" not in labels and "Tindakan" not in labels


def test_an_unsupported_language_reads_as_the_working_language(seeded) -> None:
    case_id = seeded.get("/v1/cases").json()["items"][0]["case_id"]
    french = seeded.get(f"/v1/cases/{case_id}", headers={"Accept-Language": "fr-FR"}).json()
    default = seeded.get(f"/v1/cases/{case_id}").json()
    assert french["reasons"][0]["sentence"] == default["reasons"][0]["sentence"]


# --------------------------------------------------------------------------------------
# Screening
# --------------------------------------------------------------------------------------


def test_screen_response_honours_the_language_too(api) -> None:
    """The ingest screen shows reasons the moment a bundle is screened, in the same language."""
    fixture = load("phantom")
    for prior in fixture.history:
        api.post("/v1/bundles", json=prior.model_dump(mode="json"))
    ingested = api.post("/v1/bundles", json=fixture.bundle.model_dump(mode="json")).json()
    screened = api.post(
        f"/v1/bundles/{ingested['ingestion_id']}/screen", json={}, headers=ENGLISH
    ).json()

    assert screened["reasons"], "precondition: the phantom fixture raises a reason"
    assert "Baris" not in screened["reasons"][0]["sentence"]
    assert "alasan teramati" not in screened["band"]["basis"]
