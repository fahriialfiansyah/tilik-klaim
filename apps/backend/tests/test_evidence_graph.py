"""The evidence graph makes "what supports this billed line?" answerable.

Every assertion here defends one property the review UI depends on: an edge a reviewer can
follow back to a real resource, a gap recorded rather than hidden, and a derivation that
gives the same answer twice.
"""
from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest
from tilik_domain.canonical import (
    CanonicalBundle,
    CareType,
    ClaimHeader,
    ClaimLine,
    ClaimStatus,
    DocumentRef,
    Encounter,
    EncounterStatus,
    ResourceRef,
    ResourceType,
)
from tilik_domain.edges import INFERRED_EDGE_TYPES, EdgeType

from app.service.evidence_graph import (
    SIMILARITY_CANDIDATE_FLOOR,
    EvidenceGraph,
    GapReason,
    build_evidence_graph,
)
from tests.fixtures import SCENARIOS, load

STRUCTURAL_EDGE_TYPES = frozenset(EdgeType) - INFERRED_EDGE_TYPES


def graph_for(scenario: str) -> EvidenceGraph:
    fixture = load(scenario)
    return build_evidence_graph(fixture.bundle, history=fixture.history)


# --------------------------------------------------------------------------------------
# Resolution — an edge that points at nothing is worse than no edge at all
# --------------------------------------------------------------------------------------


@pytest.mark.parametrize("scenario", SCENARIOS)
def test_every_edge_resolves_to_real_source_resources(scenario: str) -> None:
    """The product promise: every reason traces to a resource a reviewer can open."""
    fixture = load(scenario)
    graph = graph_for(scenario)
    known: set[tuple[str, str]] = set()
    for bundle in (*fixture.history, fixture.bundle):
        known |= {
            (str(ref.resource_type), ref.resource_id) for ref in _every_ref(bundle)
        }

    for edge in graph.edges:
        for ref in (edge.source, edge.target):
            if not ref.resource_type.is_stored_resource:
                continue  # episodes and practitioners are referenced, never stored
            assert (str(ref.resource_type), ref.resource_id) in known, (
                f"{scenario}: {edge.edge_type} points at absent {ref.resource_type}"
                f"/{ref.resource_id}"
            )


def _every_ref(bundle: CanonicalBundle) -> tuple[ResourceRef, ...]:
    index = bundle.resource_index()
    return tuple(
        ResourceRef(resource_type=ResourceType(rtype), resource_id=rid)
        for rtype, rid in index
    )


@pytest.mark.parametrize("scenario", SCENARIOS)
def test_graph_derives_edges_for_every_fixture(scenario: str) -> None:
    assert graph_for(scenario).edges, f"{scenario} produced no edges at all"


def test_all_edge_types_are_derived_somewhere_in_the_corpus() -> None:
    """Each of the canonical edge types must actually be reachable, not just declared."""
    seen = {edge.edge_type for scenario in SCENARIOS for edge in graph_for(scenario).edges}
    assert seen == set(EdgeType), f"never derived: {sorted(set(EdgeType) - seen)}"


# --------------------------------------------------------------------------------------
# Provenance — an edge has to say where it came from
# --------------------------------------------------------------------------------------


@pytest.mark.parametrize("scenario", SCENARIOS)
def test_every_edge_carries_its_derivation_and_version(scenario: str) -> None:
    for edge in graph_for(scenario).edges:
        assert edge.derivation_rule, f"{edge.edge_type} has no derivation rule"
        assert edge.ruleset_version, f"{edge.edge_type} has no ruleset version"


@pytest.mark.parametrize("scenario", SCENARIOS)
def test_inferred_edges_carry_confidence_and_stated_edges_do_not(scenario: str) -> None:
    """Inferred relations must show their uncertainty; stated ones must not invent any."""
    for edge in graph_for(scenario).edges:
        if edge.edge_type in INFERRED_EDGE_TYPES:
            assert edge.confidence is not None
            assert 0.0 <= edge.confidence <= 1.0
        else:
            assert edge.confidence is None


# --------------------------------------------------------------------------------------
# Determinism — the same bundle at the same version must screen identically
# --------------------------------------------------------------------------------------


@pytest.mark.parametrize("scenario", SCENARIOS)
def test_derivation_is_deterministic(scenario: str) -> None:
    first, second = graph_for(scenario), graph_for(scenario)
    assert first.edges == second.edges
    assert first.gaps == second.gaps


@pytest.mark.parametrize("scenario", SCENARIOS)
def test_edge_order_is_stable_regardless_of_resource_order(scenario: str) -> None:
    """Reordering the input must not reorder the output, or diffs become unreadable."""
    fixture = load(scenario)
    reversed_bundle = fixture.bundle.model_copy(
        update={
            "lines": tuple(reversed(fixture.bundle.lines)),
            "procedures": tuple(reversed(fixture.bundle.procedures)),
            "documents": tuple(reversed(fixture.bundle.documents)),
        }
    )
    baseline = build_evidence_graph(fixture.bundle, history=fixture.history)
    shuffled = build_evidence_graph(reversed_bundle, history=fixture.history)
    assert baseline.edges == shuffled.edges


# --------------------------------------------------------------------------------------
# The scenarios each fixture exists to prove
# --------------------------------------------------------------------------------------


def test_clean_bundle_supports_every_billed_line() -> None:
    graph = graph_for("clean")
    fixture = load("clean")
    supported = graph.supported_line_ids()
    assert supported == {line.line_id for line in fixture.bundle.lines}
    assert not graph.unsupported_line_ids()


def test_phantom_bundle_leaves_the_unevidenced_line_unsupported() -> None:
    """`LN-P2` bills a procedure the bundle never evidences. That gap is the whole signal."""
    graph = graph_for("phantom")
    assert graph.unsupported_line_ids() == {"LN-P2"}
    assert "LN-P1" in graph.supported_line_ids()

    gaps = [gap for gap in graph.gaps if gap.reason is GapReason.LINE_WITHOUT_SUPPORT]
    assert [gap.source.resource_id for gap in gaps] == ["LN-P2"]


def test_repeat_bundle_links_the_prior_claim_as_a_possible_duplicate() -> None:
    graph = graph_for("repeat")
    duplicates = graph.edges_of(EdgeType.POSSIBLE_DUPLICATE_OF)
    assert duplicates, "repeat billing needs the prior claim linked to be reviewable"
    assert {edge.target.resource_id for edge in duplicates} == {"CLM-RP-A"}


def test_clone_bundle_links_the_near_duplicate_documents() -> None:
    graph = graph_for("clone")
    similar = graph.edges_of(EdgeType.SIMILAR_TO)
    assert similar, "cloning needs the two notes linked to be reviewable"
    pair = {(edge.source.resource_id, edge.target.resource_id) for edge in similar}
    assert pair == {("DOC-CL-2", "DOC-CL-1")}
    assert all(edge.confidence >= SIMILARITY_CANDIDATE_FLOOR for edge in similar)


def test_unbundled_claims_group_into_one_episode() -> None:
    graph = graph_for("unbundled")
    episode_edges = graph.edges_of(EdgeType.PART_OF_EPISODE)
    assert {edge.target.resource_id for edge in episode_edges} == {"EPS-U1"}
    assert {edge.source.resource_id for edge in episode_edges} == {"CLM-UB-A", "CLM-UB-B"}


# --------------------------------------------------------------------------------------
# Episode grouping: a documented follow-up is a legitimate reason to stay separate
# --------------------------------------------------------------------------------------


def _minimal_bundle(
    bundle_id: str,
    claim_id: str,
    episode_id: str,
    *,
    documents: tuple[DocumentRef, ...] = (),
) -> CanonicalBundle:
    when = datetime(2026, 3, 1, 9, 0, tzinfo=UTC)
    encounter_id = f"ENC-{claim_id}"
    return CanonicalBundle(
        bundle_id=bundle_id,
        claim=ClaimHeader(
            claim_id=claim_id,
            participant_id="PX-1",
            provider_id="PRV-1",
            encounter_id=encounter_id,
            episode_id=episode_id,
            care_type=CareType.OUTPATIENT,
            submitted_at=when,
            status=ClaimStatus.ACTIVE,
            total_amount=Decimal("100.00"),
        ),
        lines=(
            ClaimLine(
                line_id=f"LN-{claim_id}",
                claim_id=claim_id,
                code_system="ICD-9-CM",
                code="00.00",
                description="tindakan contoh",
                quantity=Decimal(1),
                unit_price=Decimal("100.00"),
                line_amount=Decimal("100.00"),
                service_at=when,
            ),
        ),
        encounters=(
            Encounter(
                encounter_id=encounter_id,
                class_code="AMB",
                status=EncounterStatus.FINISHED,
                start_at=when,
                provider_id="PRV-1",
                participant_id="PX-1",
            ),
        ),
        documents=documents,
    )


def test_claims_sharing_an_episode_are_grouped() -> None:
    prior = _minimal_bundle("BND-A", "CLM-A", "EPS-1")
    current = _minimal_bundle("BND-B", "CLM-B", "EPS-1")
    graph = build_evidence_graph(current, history=(prior,))
    grouped = {edge.source.resource_id for edge in graph.edges_of(EdgeType.PART_OF_EPISODE)}
    assert grouped == {"CLM-A", "CLM-B"}


def test_a_documented_follow_up_keeps_claims_out_of_one_episode() -> None:
    """A legitimate follow-up must not read as a split episode — that is a false positive."""
    when = datetime(2026, 3, 8, 9, 0, tzinfo=UTC)
    follow_up = DocumentRef(
        document_id="DOC-FU",
        kind="follow-up",
        text_hash="hash-fu",
        authored_at=when,
        encounter_id="ENC-CLM-B",
    )
    prior = _minimal_bundle("BND-A", "CLM-A", "EPS-1")
    current = _minimal_bundle("BND-B", "CLM-B", "EPS-1", documents=(follow_up,))
    graph = build_evidence_graph(current, history=(prior,))
    grouped = {edge.source.resource_id for edge in graph.edges_of(EdgeType.PART_OF_EPISODE)}
    assert grouped == {"CLM-B"}, "the prior claim should not be pulled into this episode"


# --------------------------------------------------------------------------------------
# Incomplete bundles degrade into recorded gaps, never into an exception
# --------------------------------------------------------------------------------------


def test_incomplete_bundle_builds_with_gaps_instead_of_failing() -> None:
    """An incomplete record is not evidence of wrongdoing, so it must not break the graph."""
    dangling = ResourceRef(resource_type=ResourceType.PROCEDURE, resource_id="PROC-MISSING")
    base = _minimal_bundle("BND-INC", "CLM-INC", "EPS-INC")
    line = base.lines[0].model_copy(update={"supporting_refs": (dangling,)})
    incomplete = base.model_copy(update={"lines": (line,), "encounters": ()})

    graph = build_evidence_graph(incomplete)

    assert graph.gaps, "an unresolvable reference must be recorded, not silently dropped"
    reasons = {gap.reason for gap in graph.gaps}
    assert GapReason.DANGLING_REFERENCE in reasons
    assert all(
        edge.target.resource_id != "PROC-MISSING" for edge in graph.edges
    ), "a dangling reference must not become an edge"


def test_bundle_with_no_history_still_builds() -> None:
    graph = build_evidence_graph(_minimal_bundle("BND-S", "CLM-S", "EPS-S"))
    assert graph.edges
    assert not graph.edges_of(EdgeType.POSSIBLE_DUPLICATE_OF)
