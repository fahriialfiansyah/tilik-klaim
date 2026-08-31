"""The queue and the case detail.

Two properties get the most attention, because both are promises to people who are not in the
room: the queue must never carry clinical narrative, and every evidence reference in the detail
must resolve to something a reviewer can actually open.
"""
from __future__ import annotations

import pytest

from tests.fixtures import SCENARIOS, load

JSON = {"content-type": "application/json"}


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


# --------------------------------------------------------------------------------------
# The queue
# --------------------------------------------------------------------------------------


def test_queue_lists_every_screened_case(seeded) -> None:
    body = seeded.get("/v1/cases").json()
    assert body["page"]["total_items"] == len(SCENARIOS)
    assert len(body["items"]) == len(SCENARIOS)


def test_queue_response_carries_no_raw_medical_text(seeded) -> None:
    """A list screen never needs narrative, so it must never carry any.

    Asserted against the serialised response rather than field by field: a future field that
    accidentally included a note would slip past a field-name check.

    Distinctive four-word phrases rather than single words — the reason sentences come from the
    catalog and legitimately share common Indonesian words with the notes. Matching on "dengan"
    would fail on the catalog's own wording and prove nothing about leakage.
    """
    note = load("clone").bundle.documents[0].text
    assert note, "precondition: the clone fixture carries note text"

    raw = seeded.get("/v1/cases").text
    assert note not in raw, "the whole note appeared in the queue"

    words = note.split()
    phrases = [" ".join(words[i : i + 4]) for i in range(len(words) - 3)]
    assert phrases, "precondition: the note is long enough to phrase-check"
    for phrase in phrases:
        assert phrase not in raw, f"queue leaked narrative phrase {phrase!r}"


def test_queue_row_leads_with_the_reason_sentence(seeded) -> None:
    """The first column is why, not a score. A row that opens with a number reads as a verdict."""
    items = seeded.get("/v1/cases").json()["items"]
    for row in items:
        assert row["reason_sentence"], "every row must say why it is there"
    fields = list(items[0].keys())
    assert fields.index("reason_sentence") < fields.index("band")


def test_a_case_without_reasons_is_never_called_clean(seeded) -> None:
    rows = seeded.get("/v1/cases").json()["items"]
    quiet = [row for row in rows if row["band"] == "NO_OBSERVED_RISK"]
    assert quiet, "the clean fixture should produce one"
    for row in quiet:
        sentence = row["reason_sentence"].lower()
        assert "tidak ada risiko teramati" in sentence
        for forbidden in ("bersih", "aman", "valid", "clean", "safe"):
            assert forbidden not in sentence


def test_queue_metrics_are_exactly_the_five_agreed(seeded) -> None:
    """Anything that does not change what a reviewer does next is excluded by decision."""
    metrics = seeded.get("/v1/cases").json()["metrics"]
    assert set(metrics) == {
        "awaiting_review",
        "deterministic_conflicts",
        "evidence_requested",
        "median_time_in_queue_hours",
        "versions",
    }


def test_deterministic_conflicts_sort_above_quieter_bands(seeded) -> None:
    bands = [row["band"] for row in seeded.get("/v1/cases").json()["items"]]
    order = {
        "DETERMINISTIC_CONFLICT": 0,
        "HIGH_PRIORITY_SIGNAL": 1,
        "NEEDS_CONTEXT": 2,
        "NO_OBSERVED_RISK": 3,
    }
    assert bands == sorted(bands, key=lambda band: order[band])


@pytest.mark.parametrize("field,value", [("band", "DETERMINISTIC_CONFLICT"), ("state", "SCREENED")])
def test_filters_narrow_the_queue(seeded, field: str, value: str) -> None:
    body = seeded.get(f"/v1/cases?{field}={value}").json()
    assert body["items"], f"filter {field}={value} matched nothing"
    for row in body["items"]:
        assert row[field] == value


def test_reason_filter_selects_only_matching_cases(seeded) -> None:
    body = seeded.get("/v1/cases?reason=LINE_WITHOUT_COMPLETED_PROCEDURE").json()
    assert body["page"]["total_items"] == 1


def test_mode_filter_selects_every_reason_belonging_to_that_mode(seeded) -> None:
    """A mode spans several reason codes, so it cannot be expressed as a `reason` filter.

    The queue's mode filter has to narrow server-side: filtering the current page in the client
    would silently drop matches sitting on later pages, which is worse than no filter at all.
    """
    body = seeded.get("/v1/cases?mode=PHANTOM_OR_NO_PROCEDURE_EVIDENCE").json()
    assert body["page"]["total_items"] == 1
    for row in body["items"]:
        assert "PHANTOM_OR_NO_PROCEDURE_EVIDENCE" in row["modes"]


def test_mode_filter_combines_with_the_other_filters(seeded) -> None:
    body = seeded.get(
        "/v1/cases?mode=PHANTOM_OR_NO_PROCEDURE_EVIDENCE&band=NO_OBSERVED_RISK"
    ).json()
    assert body["items"] == []


@pytest.mark.parametrize("key", ["band", "age", "amount", "evidence"])
def test_every_sort_key_is_accepted_and_orders_the_whole_queue(seeded, key: str) -> None:
    """Sorting has to happen server-side for the same reason filtering does.

    Re-ordering an already-paginated page would shuffle rows *within* the page while leaving
    the page boundaries decided by a different order — a reviewer sorting by amount would not
    be looking at the largest amounts at all.
    """
    body = seeded.get(f"/v1/cases?sort={key}").json()
    assert body["page"]["total_items"] == len(SCENARIOS)
    assert len(body["items"]) == len(SCENARIOS)


def test_sort_by_amount_descending_puts_the_largest_first(seeded) -> None:
    body = seeded.get("/v1/cases?sort=amount&order=desc").json()
    amounts = [float(row["total_amount"]) for row in body["items"]]
    assert amounts == sorted(amounts, reverse=True)


def test_sort_by_amount_ascending_reverses_it(seeded) -> None:
    body = seeded.get("/v1/cases?sort=amount&order=asc").json()
    amounts = [float(row["total_amount"]) for row in body["items"]]
    assert amounts == sorted(amounts)


def test_band_order_is_never_reversed_by_the_order_flag(seeded) -> None:
    """`order=asc` on the band sort must not surface the quietest cases first.

    The default queue order is the product's answer to "what do I review next"; letting a
    query parameter invert it would put NO_OBSERVED_RISK at the top of the work list.
    """
    ascending = [row["band"] for row in seeded.get("/v1/cases?sort=band&order=asc").json()["items"]]
    descending = [
        row["band"] for row in seeded.get("/v1/cases?sort=band&order=desc").json()["items"]
    ]
    assert ascending == descending
    assert ascending[0] == "DETERMINISTIC_CONFLICT"


def test_an_unknown_sort_key_is_refused_rather_than_silently_ignored(seeded) -> None:
    """Silently falling back to the default would show a wrong order that looks right."""
    assert seeded.get("/v1/cases?sort=nonsense").status_code == 422


def test_queue_and_detail_report_the_same_evidence_completeness(seeded) -> None:
    """Two screens must never describe the same case differently.

    The queue derived its billed-line count from the number of *unsupported* lines, so
    `supported_lines` was zero by construction and a fully supported case rendered as "no
    billed lines at all". A reviewer comparing the list to the case would have found the
    system contradicting itself about its own evidence.
    """
    for row in seeded.get("/v1/cases").json()["items"]:
        detail = seeded.get(f"/v1/cases/{row['case_id']}").json()
        assert row["evidence_completeness"] == detail["evidence_completeness"], row["case_id"]


def test_queue_counts_every_billed_line_not_only_the_unsupported_ones(seeded) -> None:
    for row in seeded.get("/v1/cases").json()["items"]:
        detail = seeded.get(f"/v1/cases/{row['case_id']}").json()
        assert row["evidence_completeness"]["total_lines"] == len(detail["lines"])


def test_sorting_by_age_descending_puts_the_oldest_case_first(seeded) -> None:
    """"Descending" has to mean the same thing in every column.

    Age is displayed as `now - screened_at`, which moves opposite to the raw timestamp. Sorting
    on the timestamp directly made `order=desc` surface the *newest* case — the smallest number
    in the column — while `order=desc` on amount surfaces the largest. Same control, opposite
    meaning.
    """
    body = seeded.get("/v1/cases?sort=age&order=desc").json()
    stamps = [row["created_at"] for row in body["items"]]
    assert stamps == sorted(stamps), "oldest first means ascending screened_at"


def test_sorting_by_age_ascending_puts_the_newest_case_first(seeded) -> None:
    body = seeded.get("/v1/cases?sort=age&order=asc").json()
    stamps = [row["created_at"] for row in body["items"]]
    assert stamps == sorted(stamps, reverse=True)


def test_search_narrows_the_whole_queue_not_just_the_current_page(seeded) -> None:
    """Searching client-side would strand matches on later pages.

    With the term applied to one already-paginated page, a case whose identifier sat on page 2
    was unreachable: the page came back empty, and the empty state offered only "clear the
    filters" — no way to page forward carrying the term.
    """
    everything = seeded.get("/v1/cases").json()["items"]
    target = everything[-1]["case_id"]

    body = seeded.get(f"/v1/cases?search={target[-8:]}&page_size=1").json()
    assert body["page"]["total_items"] == 1
    assert body["items"][0]["case_id"] == target


def test_search_matches_nothing_outside_the_case_identifier(seeded) -> None:
    """There is no name or national-ID field in this system to search by."""
    assert seeded.get("/v1/cases?search=Budi").json()["page"]["total_items"] == 0


def test_pagination_bounds_hold(seeded) -> None:
    first = seeded.get("/v1/cases?page=1&page_size=2").json()
    assert len(first["items"]) == 2
    assert first["page"]["total_pages"] == 3
    assert first["page"]["total_items"] == 5

    last = seeded.get("/v1/cases?page=3&page_size=2").json()
    assert len(last["items"]) == 1


def test_paging_past_the_end_returns_empty_not_an_error(seeded) -> None:
    body = seeded.get("/v1/cases?page=99&page_size=2").json()
    assert body["items"] == []
    assert body["page"]["total_items"] == 5


def test_page_size_is_capped(seeded) -> None:
    assert seeded.get("/v1/cases?page_size=5000").status_code == 422


def test_pages_do_not_overlap_or_skip(seeded) -> None:
    seen = []
    for page in (1, 2, 3):
        seen.extend(
            row["case_id"] for row in seeded.get(f"/v1/cases?page={page}&page_size=2").json()["items"]
        )
    assert len(seen) == len(set(seen)) == 5


# --------------------------------------------------------------------------------------
# The detail
# --------------------------------------------------------------------------------------


def test_detail_returns_reasons_evidence_and_counter_evidence(api) -> None:
    case_id = ingest_and_screen(api, "phantom")["case_id"]
    body = api.get(f"/v1/cases/{case_id}").json()

    assert body["primary_reason"]["code"] == "LINE_WITHOUT_COMPLETED_PROCEDURE"
    assert body["primary_reason"]["counter_evidence"], "a reason must argue against itself too"
    assert body["lines"], "the reviewer needs the billed lines"
    assert body["timeline"], "and the episode in time order"
    assert body["versions"]["ruleset_version"]


def test_every_evidence_reference_in_the_detail_resolves(api) -> None:
    """A reference pointing at nothing is a dead end in the UI, not an empty panel."""
    fixture = load("phantom")
    case_id = ingest_and_screen(api, "phantom")["case_id"]
    body = api.get(f"/v1/cases/{case_id}").json()

    known = {rid for _, rid in fixture.bundle.resource_index()}
    for bundle in fixture.history:
        known |= {rid for _, rid in bundle.resource_index()}

    unstored = {"Episode", "Practitioner"}
    for reason in body["reasons"]:
        for ref in (*reason["evidence"], *reason["counter_evidence"]):
            if ref["resource_type"] in unstored:
                continue
            assert ref["resource_id"] in known, f"unresolvable {ref}"


def test_queue_and_detail_never_disagree_about_why(api) -> None:
    """Both read the same catalog entry; a mismatch would leave a reviewer unable to tell which."""
    case_id = ingest_and_screen(api, "phantom")["case_id"]
    row = next(
        item
        for item in api.get("/v1/cases").json()["items"]
        if item["case_id"] == case_id
    )
    detail = api.get(f"/v1/cases/{case_id}").json()
    assert row["reason_sentence"] == detail["primary_reason"]["sentence"]


def test_detail_distinguishes_unassessable_from_unsupported(api) -> None:
    """"We could not judge" and "the evidence is absent" lead to different actions."""
    fixture = load("clean")
    bare = tuple(line.model_copy(update={"supporting_refs": ()}) for line in fixture.bundle.lines)
    thin = fixture.bundle.model_copy(
        update={"lines": bare, "procedures": (), "medications": (), "provenance": ()}
    )
    ingested = api.post("/v1/bundles", json=thin.model_dump(mode="json")).json()
    assert ingested["completeness_notes"], "precondition: this bundle is thin"
    case_id = api.post(f"/v1/bundles/{ingested['ingestion_id']}/screen", json={}).json()["case_id"]

    body = api.get(f"/v1/cases/{case_id}").json()
    states = {line["support_state"] for line in body["lines"]}
    assert "NOT_ASSESSABLE" in states
    assert body["evidence_completeness"]["bundle_complete"] is False


def test_clone_comparison_carries_the_template_caveat(api) -> None:
    """Shared templates produce high similarity too, and the reviewer must read that first."""
    case_id = ingest_and_screen(api, "clone")["case_id"]
    body = api.get(f"/v1/cases/{case_id}").json()
    caveats = [c["template_caveat"] for c in body["comparisons"] if c["template_caveat"]]
    assert caveats, "a clone comparison without its caveat invites a wrong conclusion"
    assert "templat" in caveats[0].lower()


def test_unknown_case_returns_a_named_error(api) -> None:
    response = api.get("/v1/cases/case_nope")
    assert response.status_code == 404
    assert response.json()["code"] == "CASE_NOT_FOUND"
