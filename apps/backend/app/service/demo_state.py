"""Is this system ready to be demonstrated right now?

`docs/canonical/08_demo_runbook.md` § Demo reliability asks for a health check that runs before
anyone presents. The question it has to answer is not "is the process alive" but "will the
ninety-second flow work" — a running service pointed at an empty database passes the first and
fails the second, on stage.

**Readiness never changes the HTTP status of `/healthz`.** `railway.json` uses that path as its
platform health probe, so making it fail when the database is unreachable would restart the
container in a loop precisely when the database is the thing having trouble. Liveness stays
`ok`; readiness reports separately, and `scripts/demo_reset.py --check` is what exits non-zero.
"""
from __future__ import annotations

from dataclasses import dataclass

from tilik_domain.reasons import CaseState, ReasonCode

from app.config import get_settings
from app.store.engine import is_database_available
from app.store.registry import get_case_store, use_database

EXPECTED_CASE_COUNT = 5
"""The five gold scenarios: clean, phantom, repeat, clone, unbundled."""

DEMO_REASON = ReasonCode.LINE_WITHOUT_COMPLETED_PROCEDURE
"""The reason the runbook's ideal case must raise — a billed line with no completed procedure."""

READY_STATES: frozenset[CaseState] = frozenset({CaseState.SCREENED, CaseState.NEW})
"""A demo starts from screened cases nobody has opened yet."""


@dataclass(frozen=True)
class Readiness:
    """What a presenter needs to know before starting, and nothing they cannot act on."""

    ready: bool
    database_reachable: bool
    persistence: str
    case_count: int
    expected_case_count: int
    demo_case_present: bool
    """True when a case raising the runbook's ideal reason is screened and untouched."""
    untouched_cases: int
    problems: tuple[str, ...]

    engine_version: str
    ruleset_version: str
    dataset_version: str

    def as_payload(self) -> dict[str, object]:
        return {
            "ready": self.ready,
            "database_reachable": self.database_reachable,
            "persistence": self.persistence,
            "case_count": self.case_count,
            "expected_case_count": self.expected_case_count,
            "demo_case_present": self.demo_case_present,
            "untouched_cases": self.untouched_cases,
            "problems": list(self.problems),
        }

    def summary(self) -> str:
        if self.ready:
            return (
                f"siap — {self.case_count} kasus tersemai, kasus demo tersedia, "
                f"penyimpanan {self.persistence}"
            )
        return f"belum siap — {'; '.join(self.problems)}"


def check_readiness() -> Readiness:
    """Assess the current state. Reads; changes nothing."""
    settings = get_settings()
    reachable = is_database_available()
    persistence = "postgres" if use_database() else "in-memory"

    problems: list[str] = []
    if not reachable:
        # Not fatal by itself: the service deliberately runs without a database so the demo can
        # be rehearsed offline. It is worth naming, because an in-memory run loses its state
        # when the process restarts — which is a surprise nobody needs mid-demo.
        problems.append(
            "basis data tidak terjangkau; layanan berjalan di memori dan kehilangan "
            "keadaannya bila proses dimulai ulang"
        )

    if reachable and persistence != "postgres":
        # The exact failure this check caught in the wild: the process started while the
        # database was still coming up, chose the in-memory stores, and `use_database()` caches
        # that answer for the life of the process — deliberately, so two stores can never
        # disagree about where an ingestion lives. The consequence is that a seed script writing
        # to Postgres and an API serving memory are two different worlds, and every screen looks
        # plausibly wrong. Re-seeding does not help; only a restart does.
        problems.append(
            "basis data terjangkau tetapi proses ini memakai penyimpanan memori — ia dimulai "
            "sebelum basis data siap. Mulai ulang API; menyemai ulang saja tidak menolong, "
            "karena skrip menulis ke Postgres dan proses ini tidak membacanya"
        )

    cases = get_case_store().list_all()
    untouched = [case for case in cases if case.state in READY_STATES]
    if len(cases) < EXPECTED_CASE_COUNT:
        problems.append(
            f"hanya {len(cases)} kasus tersemai, seharusnya {EXPECTED_CASE_COUNT}; "
            "jalankan scripts/demo_reset.py"
        )

    demo_case_present = any(
        reason.code is DEMO_REASON
        for case in untouched
        for reason in case.result.reasons
    )
    if not demo_case_present:
        problems.append(
            "kasus demo (baris tagihan tanpa catatan tindakan selesai) tidak ada atau sudah "
            "dibuka; jalankan scripts/demo_reset.py"
        )

    return Readiness(
        ready=not problems,
        database_reachable=reachable,
        persistence=persistence,
        case_count=len(cases),
        expected_case_count=EXPECTED_CASE_COUNT,
        demo_case_present=demo_case_present,
        untouched_cases=len(untouched),
        problems=tuple(problems),
        engine_version=settings.engine_version,
        ruleset_version=settings.ruleset_version,
        dataset_version=settings.dataset_version,
    )
