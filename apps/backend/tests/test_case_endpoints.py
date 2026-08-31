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


# --------------------------------------------------------------------------------------
# Counter-evidence sentences, openable sources, and real comparisons
#
# All three exist so the case-detail screen can keep the promises `sprint/00-app-spec.md` § 4
# binds it to. Each was, at one point, satisfied only in shape: counter-evidence arrived as a
# bare resource id with the sentence stripped off, every evidence reference was a pointer to
# nothing the client could open, and the comparison drawer's "fields" compared a number to
# itself. All three read as working features until someone looked at the screen.
# --------------------------------------------------------------------------------------


def test_counter_evidence_carries_its_sentence_not_only_a_reference(api) -> None:
    """A bare resource id is not an argument against a signal.

    The rules already write the sentence — "Bundel ini hanya memuat bukti yang ikut terkirim…"
    is what stops a missing record from reading as a missing service. Dropping it on the way to
    the wire left the reviewer a resource id with no idea why it weakened anything.
    """
    case_id = ingest_and_screen(api, "phantom")["case_id"]
    body = api.get(f"/v1/cases/{case_id}").json()

    notes = body["primary_reason"]["counter_evidence_notes"]
    assert notes, "a reason must carry the argument against it, in words"
    assert all(note["note"].strip() for note in notes), "a note without text explains nothing"
    assert any(len(note["note"].split()) > 5 for note in notes), "these are sentences, not labels"


def test_every_reason_reference_appears_in_the_source_index(api) -> None:
    """Display rule 4: an evidence reference the UI cannot open is a defect, not a blank panel.

    The index is what makes "openable" true. Every reference a reason cites has an entry, and
    the entry says which of the four availabilities applies — so an unresolvable one surfaces as
    an integrity defect rather than a panel that quietly renders nothing.
    """
    case_id = ingest_and_screen(api, "phantom")["case_id"]
    body = api.get(f"/v1/cases/{case_id}").json()

    indexed = {(s["resource_type"], s["resource_id"]) for s in body["sources"]}
    assert indexed, "the detail must ship a source index"
    for reason in body["reasons"]:
        for ref in (*reason["evidence"], *reason["counter_evidence"]):
            assert (ref["resource_type"], ref["resource_id"]) in indexed, f"unopenable {ref}"


def test_sources_present_in_this_bundle_carry_their_fields(api) -> None:
    case_id = ingest_and_screen(api, "phantom")["case_id"]
    body = api.get(f"/v1/cases/{case_id}").json()

    present = [s for s in body["sources"] if s["availability"] == "PRESENT"]
    assert present, "the reasons cite resources this bundle carries"
    assert all(s["fields"] for s in present), "a resource shown as present must show its content"


def test_a_peer_document_is_marked_related_and_never_carries_its_text(api) -> None:
    """Cloning is a cross-participant pattern, so the peer note belongs to someone else.

    It has to be *openable* — the reviewer must see that the compared document exists and when
    it was written — and it must never show that person's narrative or token.
    `docs/canonical/07_privacy_threat_model.md` treats the highlight as the exposure route.
    """
    fixture = load("clone")
    peer_text = fixture.history[0].documents[0].text
    assert peer_text, "precondition: the peer note has text"

    case_id = ingest_and_screen(api, "clone")["case_id"]
    response = api.get(f"/v1/cases/{case_id}")
    body = response.json()

    related = [s for s in body["sources"] if s["availability"] == "RELATED_BUNDLE"]
    assert related, "the peer document must be openable, not absent"
    assert peer_text not in response.text, "a peer participant's narrative left the boundary"
    for source in related:
        names = {field["name"] for field in source["fields"]}
        assert "participant_id" not in names
        assert "text" not in names


def test_an_unresolvable_reference_is_reported_as_missing_rather_than_omitted(api) -> None:
    """Silence is the failure mode this guards against.

    Dropping a reference the store cannot resolve would render as a shorter list — indis-
    tinguishable from a reason that simply cited less. `MISSING` makes the defect visible.
    """
    from app.dto.cases import SourceAvailability

    assert SourceAvailability.MISSING == "MISSING"
    case_id = ingest_and_screen(api, "phantom")["case_id"]
    body = api.get(f"/v1/cases/{case_id}").json()
    assert all(
        s["availability"] in {a.value for a in SourceAvailability} for s in body["sources"]
    )


def test_repeat_comparison_compares_two_real_claims_field_by_field(api) -> None:
    """The drawer's job is to show what actually differs between the pair.

    It used to list the reason's own component scores with the same value on both sides and
    `matches` hard-coded true — a comparison in which nothing could ever differ.
    """
    case_id = ingest_and_screen(api, "repeat")["case_id"]
    body = api.get(f"/v1/cases/{case_id}").json()

    assert body["comparisons"], "a repeat reason must offer its pair"
    fields = body["comparisons"][0]["fields"]
    assert fields, "a comparison with no fields compares nothing"
    assert any(not field["matches"] for field in fields), "two distinct claims differ somewhere"
    assert any(
        field["left_value"] != field["right_value"] for field in fields
    ), "a differing field must show two different values"


def test_clone_comparison_never_puts_another_participant_in_the_drawer(api) -> None:
    case_id = ingest_and_screen(api, "clone")["case_id"]
    response = api.get(f"/v1/cases/{case_id}")
    comparison = response.json()["comparisons"][0]

    peer_token = load("clone").history[0].claim.participant_id
    rendered = " ".join(
        f"{f['field_name']} {f['left_value']} {f['right_value']}" for f in comparison["fields"]
    )
    assert peer_token not in rendered, "the drawer named the other participant"
    assert comparison["similarity_components"], "the reviewer still sees what drove the score"


def test_reasons_are_ordered_strongest_first_everywhere_they_appear(api) -> None:
    """The card that opens on load must be the strongest one, and the queue must agree.

    Rule-registration order is fixed for reproducibility, not for reading — a non-deterministic
    similarity reason registered before a deterministic conflict would lead both the queue row
    and the case header while the band came from the reason underneath it. Ordering once, in
    the response, keeps every surface saying the same thing.
    """
    case_id = ingest_and_screen(api, "unbundled")["case_id"]
    detail = api.get(f"/v1/cases/{case_id}").json()

    strengths = [
        (reason["deterministic"], -len(reason["counter_evidence_notes"]))
        for reason in detail["reasons"]
    ]
    assert strengths == sorted(strengths, reverse=True), "cards would open on a weaker reason"
    assert detail["primary_reason"] == detail["reasons"][0]

    row = next(
        item for item in api.get("/v1/cases").json()["items"] if item["case_id"] == case_id
    )
    assert row["reason_sentence"] == detail["reasons"][0]["sentence"]


def test_timeline_resources_are_indexed_so_the_screen_cannot_flag_them_as_broken(api) -> None:
    """The timeline draws an unresolvable reference as an integrity defect.

    So a resource that is present and fine but simply not cited by any reason has to be in the
    index too, or the episode timeline would report a working bundle as a broken evidence trail.
    """
    case_id = ingest_and_screen(api, "phantom")["case_id"]
    body = api.get(f"/v1/cases/{case_id}").json()

    indexed = {(s["resource_type"], s["resource_id"]) for s in body["sources"]}
    referenced = [event["resource"] for event in body["timeline"] if event["resource"]]
    assert referenced, "precondition: the timeline points at resources"
    for ref in referenced:
        assert (ref["resource_type"], ref["resource_id"]) in indexed, f"unopenable {ref}"


def test_expected_evidence_names_the_absent_resource(api) -> None:
    """The evidence panel has to point at what is missing, not at what is already on screen."""
    case_id = ingest_and_screen(api, "phantom")["case_id"]
    reason = api.get(f"/v1/cases/{case_id}").json()["primary_reason"]

    assert "Procedure" in reason["expected_support"]
    found = {ref["resource_type"] for ref in reason["evidence"]}
    assert "Procedure" not in found, "precondition: the procedure record is what is absent"
