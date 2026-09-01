"""The comparison drawer: what it links to, and what it deliberately does not.

A drawer that puts two claims side by side without a route from one to the other makes the
reviewer find the second one in the queue by hand — on the screen that is most expensive to
misread. These tests hold the link, and hold the line on the two pairs that must *not* have one.
"""
from __future__ import annotations

from tests.fixtures import load


def _ingest(api, bundle) -> str:
    return api.post("/v1/bundles", json=bundle.model_dump(mode="json")).json()["ingestion_id"]


def _screen(api, ingestion_id: str) -> str:
    return api.post(f"/v1/bundles/{ingestion_id}/screen", json={}).json()["case_id"]


def test_a_repeat_comparison_links_to_the_prior_claims_own_case(api) -> None:
    """The drawer must offer a way in, not just name a claim the reviewer then hunts for.

    `candidate_case_id` shipped as `null` on every comparison: the builder had the prior
    *bundle* but no way to resolve it back to the case raised for it, so the drawer showed two
    claims side by side and no route from one to the other.
    """
    fixture = load("repeat")
    prior_case_ids = {_screen(api, _ingest(api, prior)) for prior in fixture.history}
    case_id = _screen(api, _ingest(api, fixture.bundle))

    detail = api.get(f"/v1/cases/{case_id}").json()

    linked = [row for row in detail["comparisons"] if row["candidate_case_id"]]
    assert linked, "no repeat comparison resolved its candidate to a case"
    target = linked[0]["candidate_case_id"]

    assert target != case_id, "a case must not be compared against itself"
    assert target in prior_case_ids, "the link points at a case that is not the prior claim's"
    # The link has to lead somewhere: the case it names must actually be openable.
    assert api.get(f"/v1/cases/{target}").status_code == 200


def test_an_unscreened_prior_claim_has_no_case_to_link_to(api) -> None:
    """`null` here is correct, not a regression of the defect above.

    A bundle that was accepted but never screened has no case, so there is nothing to open. The
    seeded demo is in exactly this state — its history bundles are ingested only — which is why
    the drawer shows no link there and why that is not a bug to chase.
    """
    fixture = load("repeat")
    for prior in fixture.history:
        _ingest(api, prior)  # accepted, deliberately not screened
    case_id = _screen(api, _ingest(api, fixture.bundle))

    detail = api.get(f"/v1/cases/{case_id}").json()

    assert detail["comparisons"], "the repeat fixture raised no comparison at all"
    assert all(row["candidate_case_id"] is None for row in detail["comparisons"])


def test_a_clone_comparison_leaves_the_candidate_case_unset(api) -> None:
    """Cloning crosses participants, and this layer is handed the note — never the bundle.

    Resolving it would mean walking a document back to somebody else's submission. The drawer
    does not need that badly enough to build the path, so the field stays absent rather than
    being filled by a lookup nobody asked for.
    """
    fixture = load("clone")
    for prior in fixture.history:
        _screen(api, _ingest(api, prior))
    case_id = _screen(api, _ingest(api, fixture.bundle))

    detail = api.get(f"/v1/cases/{case_id}").json()

    clone_rows = [row for row in detail["comparisons"] if row.get("template_caveat") is not None]
    assert clone_rows, "the clone fixture raised no comparison at all"
    assert all(row["candidate_case_id"] is None for row in clone_rows)
