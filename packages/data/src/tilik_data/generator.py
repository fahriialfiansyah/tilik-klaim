"""Deterministic generator for the clean synthetic corpus.

Emits `CanonicalBundle` records directly — no FHIR intermediate, no Java, no external tool.
See `docs/canonical/decisions/ADR-0003-native-generator-instead-of-synthea.md` for why.

**Determinism is the whole contract.** One seed reproduces the corpus byte-for-byte. Every
random draw comes from a `Random` seeded per bundle from the run seed and the bundle index, so
generating bundle 400 alone gives the same bundle as generating it inside a run of 1,000. That
property is what lets an evaluation result be re-derived months later.

Every bundle produced here satisfies the **normal patterns** in `docs/canonical/04_data_card.md`:
each billed procedure has one completed `Procedure` in a compatible encounter and time window,
claim totals reconcile with their lines, evidence falls inside the encounter, each claim sits in
one episode, and notes vary across encounters. Those properties are what make an *injected*
deviation meaningful — a corpus that were already inconsistent would make every detector fire.

Nothing here is clinically realistic and it must never be described as such.
"""
from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from random import Random

from tilik_domain.canonical import (
    Account,
    CanonicalBundle,
    CareType,
    ChargeItem,
    ClaimHeader,
    ClaimLine,
    ClaimStatus,
    Condition,
    DocumentRef,
    Encounter,
    EncounterStatus,
    EventStatus,
    Invoice,
    MedicationEvent,
    MedicationKind,
    Procedure,
    Provenance,
    ResourceRef,
    ResourceType,
    SourceType,
    VerificationStatus,
)

from tilik_data.amounts import claim_total, line_total, money, unit_price
from tilik_data.vocab import (
    CONDITION_CODES,
    MEDICATION_CODES,
    NOTE_TEMPLATES,
    PROCEDURE_CODES,
    text_hash,
)

EPOCH = datetime(2026, 1, 5, 8, 0, tzinfo=UTC)
"""Corpus timeline starts here. Fixed so timestamps are reproducible, not wall-clock."""

MAX_ENCOUNTER_HOURS = 6
MIN_LINES, MAX_LINES = 1, 4
MEDICATION_LINE_CHANCE = 0.35
DOCUMENT_CHANCE = 0.6
"""Most encounters produce a note, but not all — a bundle without one is ordinary, not a defect."""


def bundle_seed(run_seed: int, index: int) -> int:
    """A stream per bundle, derived from the run seed.

    Deriving per-bundle rather than drawing from one shared stream means bundle *n* does not
    depend on how many bundles preceded it, so a subset regenerates identically.
    """
    return (run_seed * 1_000_003 + index * 97) % (2**63)


def generate_bundle(
    run_seed: int,
    index: int,
    *,
    participant_count: int,
    provider_count: int,
) -> CanonicalBundle:
    """One internally consistent clean bundle. Same inputs, same bytes, always."""
    rng = Random(bundle_seed(run_seed, index))

    participant = f"PSN-{rng.randrange(participant_count):04d}"
    provider = f"PRV-{rng.randrange(provider_count):02d}"
    suffix = f"{index:05d}"

    started = EPOCH + timedelta(days=rng.randrange(0, 300), hours=rng.randrange(0, 10))
    duration = timedelta(hours=rng.randint(1, MAX_ENCOUNTER_HOURS))
    encounter_id = f"ENC-{suffix}"
    care_type = rng.choice(tuple(CareType))

    encounter = Encounter(
        encounter_id=encounter_id,
        class_code="AMB" if care_type is CareType.OUTPATIENT else "IMP",
        status=EncounterStatus.FINISHED,
        start_at=started,
        end_at=started + duration,
        provider_id=provider,
        location_id=f"LOC-{provider}-{rng.randrange(3)}",
        participant_id=participant,
    )

    condition_code = rng.choice(CONDITION_CODES)
    condition = Condition(
        condition_id=f"CND-{suffix}",
        code_system="ICD-10",
        code=condition_code,
        recorded_at=started + timedelta(minutes=15),
        verification_status=VerificationStatus.CONFIRMED,
        encounter_id=encounter_id,
    )

    procedures, medications, lines, charge_items = _build_services(
        rng, suffix, encounter, started, duration
    )

    account = Account(
        account_id=f"ACC-{suffix}",
        participant_id=participant,
        provider_id=provider,
        status="active",
    )
    invoice = Invoice(
        invoice_id=f"INV-{suffix}",
        account_id=account.account_id,
        total_amount=claim_total(tuple(line.line_amount for line in lines)),
        issued_at=started + duration + timedelta(hours=1),
        charge_item_refs=tuple(
            ResourceRef(
                resource_type=ResourceType.CHARGE_ITEM, resource_id=item.charge_item_id
            )
            for item in charge_items
        ),
    )

    documents = _build_documents(rng, suffix, encounter_id, started, condition_code)

    claim = ClaimHeader(
        claim_id=f"CLM-{suffix}",
        participant_id=participant,
        provider_id=provider,
        encounter_id=encounter_id,
        episode_id=f"EPS-{suffix}",
        care_type=care_type,
        submitted_at=started + duration + timedelta(days=rng.randint(1, 5)),
        status=ClaimStatus.ACTIVE,
        total_amount=invoice.total_amount,
    )

    return CanonicalBundle(
        bundle_id=f"BND-{suffix}",
        claim=claim,
        lines=lines,
        encounters=(encounter,),
        conditions=(condition,),
        procedures=procedures,
        medications=medications,
        documents=documents,
        accounts=(account,),
        charge_items=charge_items,
        invoices=(invoice,),
        provenance=_build_provenance(claim, encounter, procedures, documents),
    )


def _build_services(
    rng: Random,
    suffix: str,
    encounter: Encounter,
    started: datetime,
    duration: timedelta,
) -> tuple[
    tuple[Procedure, ...], tuple[MedicationEvent, ...], tuple[ClaimLine, ...],
    tuple[ChargeItem, ...],
]:
    """Build billed lines and the completed events that evidence them.

    Evidence is created *with* the line and inside the encounter window, which is what makes the
    clean corpus clean: the phantom injector later removes evidence, and that removal is only
    meaningful because it was here to begin with.
    """
    procedures: list[Procedure] = []
    medications: list[MedicationEvent] = []
    lines: list[ClaimLine] = []
    charge_items: list[ChargeItem] = []

    for position in range(rng.randint(MIN_LINES, MAX_LINES)):
        # Evidence sits strictly inside the encounter window, never at or past its end.
        offset = timedelta(
            minutes=rng.randint(20, max(21, int(duration.total_seconds() // 60) - 10))
        )
        performed_at = started + offset
        is_medication = rng.random() < MEDICATION_LINE_CHANCE
        line_id = f"LN-{suffix}-{position}"

        if is_medication:
            code_system, code = "KFA", rng.choice(MEDICATION_CODES)
            quantity = Decimal(rng.randint(1, 20))
            price = unit_price(rng, (15_000, 400_000))
            event = MedicationEvent(
                medication_id=f"MED-{suffix}-{position}",
                kind=MedicationKind.DISPENSE,
                code_system=code_system,
                code=code,
                status=EventStatus.COMPLETED,
                quantity=quantity,
                occurred_at=performed_at,
                encounter_id=encounter.encounter_id,
            )
            medications.append(event)
            evidence_ref = ResourceRef(
                resource_type=ResourceType.MEDICATION, resource_id=event.medication_id
            )
        else:
            code_system, code = "ICD-9-CM", rng.choice(PROCEDURE_CODES)
            quantity = Decimal("1")
            price = unit_price(rng, (150_000, 2_500_000))
            event = Procedure(
                procedure_id=f"PRC-{suffix}-{position}",
                code_system=code_system,
                code=code,
                status=EventStatus.COMPLETED,
                performed_at=performed_at,
                performer_id=f"PRACT-{rng.randrange(20):02d}",
                location_id=encounter.location_id,
                encounter_id=encounter.encounter_id,
            )
            procedures.append(event)
            evidence_ref = ResourceRef(
                resource_type=ResourceType.PROCEDURE, resource_id=event.procedure_id
            )

        amount = line_total(quantity, price)
        charge_item = ChargeItem(
            charge_item_id=f"CHI-{suffix}-{position}",
            account_id=f"ACC-{suffix}",
            code_system=code_system,
            code=code,
            quantity=quantity,
            unit_price=price,
            total_amount=amount,
            occurred_at=performed_at,
            encounter_id=encounter.encounter_id,
        )
        charge_items.append(charge_item)

        lines.append(
            ClaimLine(
                line_id=line_id,
                claim_id=f"CLM-{suffix}",
                code_system=code_system,
                code=code,
                description=f"Layanan {code}",
                quantity=quantity,
                unit_price=price,
                line_amount=amount,
                service_at=performed_at,
                charge_item_ref=ResourceRef(
                    resource_type=ResourceType.CHARGE_ITEM,
                    resource_id=charge_item.charge_item_id,
                ),
                supporting_refs=(evidence_ref,),
            )
        )

    return tuple(procedures), tuple(medications), tuple(lines), tuple(charge_items)


def _build_documents(
    rng: Random,
    suffix: str,
    encounter_id: str,
    started: datetime,
    condition_code: str,
) -> tuple[DocumentRef, ...]:
    """A clinical note, worded differently per encounter.

    Variation is deliberate. If every clean note read alike, the clone detector would fire on
    the whole corpus and its precision measurement would be meaningless.
    """
    if rng.random() >= DOCUMENT_CHANCE:
        return ()

    template = rng.choice(NOTE_TEMPLATES)
    text = template.format(
        days=rng.randint(1, 10),
        code=condition_code,
        finding=rng.choice(("membaik", "stabil", "belum ada perubahan berarti")),
        plan=rng.choice(("kontrol ulang", "lanjutkan terapi", "observasi di rumah")),
    )
    return (
        DocumentRef(
            document_id=f"DOC-{suffix}",
            kind="clinical-note",
            text=text,
            text_hash=text_hash(text),
            author_id=f"PRACT-{rng.randrange(20):02d}",
            authored_at=started + timedelta(minutes=45),
            encounter_id=encounter_id,
        ),
    )


def _build_provenance(
    claim: ClaimHeader,
    encounter: Encounter,
    procedures: tuple[Procedure, ...],
    documents: tuple[DocumentRef, ...],
) -> tuple[Provenance, ...]:
    """Where each resource came from.

    Every entry is `SYNTHETIC_GENERATOR`, and that is the point: provenance records how a record
    entered *this* system, so a generated bundle must never claim to have come from an EMR.
    Timestamps are derived from the bundle's own timeline, never from the wall clock.
    """
    entries = [
        Provenance(
            resource_id=claim.claim_id,
            resource_type=ResourceType.CLAIM,
            source_type=SourceType.SYNTHETIC_GENERATOR,
            last_updated_at=claim.submitted_at,
        ),
        Provenance(
            resource_id=encounter.encounter_id,
            resource_type=ResourceType.ENCOUNTER,
            source_type=SourceType.SYNTHETIC_GENERATOR,
            last_updated_at=encounter.end_at or encounter.start_at,
        ),
    ]
    entries.extend(
        Provenance(
            resource_id=procedure.procedure_id,
            resource_type=ResourceType.PROCEDURE,
            source_type=SourceType.SYNTHETIC_GENERATOR,
            last_updated_at=procedure.performed_at,
        )
        for procedure in procedures
    )
    entries.extend(
        Provenance(
            resource_id=document.document_id,
            resource_type=ResourceType.DOCUMENT,
            source_type=SourceType.SYNTHETIC_GENERATOR,
            last_updated_at=document.authored_at,
        )
        for document in documents
    )
    return tuple(entries)


def generate_corpus(
    run_seed: int,
    count: int,
    *,
    participant_count: int,
    provider_count: int,
) -> tuple[CanonicalBundle, ...]:
    """The clean corpus. Deterministic for a given seed and count."""
    return tuple(
        generate_bundle(
            run_seed,
            index,
            participant_count=participant_count,
            provider_count=provider_count,
        )
        for index in range(count)
    )


def corpus_hash(bundles: tuple[CanonicalBundle, ...]) -> str:
    """A digest over the whole corpus, for the determinism assertion and the manifest."""
    import hashlib
    import json

    payload = json.dumps(
        [bundle.model_dump(mode="json") for bundle in bundles],
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def money_guard(value: Decimal) -> Decimal:
    """Re-export so injectors mutate amounts through the same rounding rule."""
    return money(value)
