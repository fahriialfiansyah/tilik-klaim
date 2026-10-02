"""The connective text the assistant composes itself, in both languages the API speaks.

Findings come from the catalogs — reason sentences, counter-evidence notes, band bases — and are
rendered by the response the assistant reads. What is left is the frame around them, and the
names of modes, bands and states. Those names are the web app's own words, mirrored here so a
template answer and the screen it sits on never call one thing two names;
`tests/test_assistant_wording.py` reads the web locale files and fails the moment they drift.

Nothing here accuses, decides, or reassures: every string passes the same lexicon the validator
applies to model output, and a test runs them through it.
"""
from __future__ import annotations

from tilik_domain.locale import Locale
from tilik_domain.reasons import CaseState, PriorityBand, RiskMode

from app.dto.assistant import RefusalTopic


def pick(locale: Locale, indonesian: str, english: str) -> str:
    return english if locale is Locale.EN else indonesian


MODE_LABELS: dict[Locale, dict[RiskMode, str]] = {
    Locale.ID: {
        RiskMode.PHANTOM_OR_NO_PROCEDURE_EVIDENCE: "Tagihan tanpa bukti",
        RiskMode.REPEAT_BILLING: "Tagihan berulang",
        RiskMode.CLONED_DOCUMENTATION: "Dokumentasi salinan",
        RiskMode.UNBUNDLING_FRAGMENTATION: "Episode terpecah",
    },
    Locale.EN: {
        RiskMode.PHANTOM_OR_NO_PROCEDURE_EVIDENCE: "Billed without evidence",
        RiskMode.REPEAT_BILLING: "Repeat billing",
        RiskMode.CLONED_DOCUMENTATION: "Cloned documentation",
        RiskMode.UNBUNDLING_FRAGMENTATION: "Split episode",
    },
}

BAND_LABELS: dict[Locale, dict[PriorityBand, str]] = {
    Locale.ID: {
        PriorityBand.DETERMINISTIC_CONFLICT: "Konflik deterministik",
        PriorityBand.HIGH_PRIORITY_SIGNAL: "Sinyal prioritas tinggi",
        PriorityBand.NEEDS_CONTEXT: "Perlu konteks",
        PriorityBand.NO_OBSERVED_RISK: "Tidak ada risiko teramati",
    },
    Locale.EN: {
        PriorityBand.DETERMINISTIC_CONFLICT: "Deterministic conflict",
        PriorityBand.HIGH_PRIORITY_SIGNAL: "High-priority signal",
        PriorityBand.NEEDS_CONTEXT: "Needs context",
        PriorityBand.NO_OBSERVED_RISK: "No risk observed",
    },
}

STATE_LABELS: dict[Locale, dict[CaseState, str]] = {
    Locale.ID: {
        CaseState.NEW: "Baru",
        CaseState.SCREENED: "Tersaring",
        CaseState.IN_REVIEW: "Sedang ditinjau",
        CaseState.EVIDENCE_REQUESTED: "Menunggu bukti",
        CaseState.DISMISSED: "Sinyal ditolak",
        CaseState.CONFIRMED_ANOMALY: "Anomali dikonfirmasi",
        CaseState.ESCALATED: "Dieskalasi",
        CaseState.INVALID_INPUT: "Input tidak valid",
    },
    Locale.EN: {
        CaseState.NEW: "New",
        CaseState.SCREENED: "Screened",
        CaseState.IN_REVIEW: "In review",
        CaseState.EVIDENCE_REQUESTED: "Awaiting evidence",
        CaseState.DISMISSED: "Signal rejected",
        CaseState.CONFIRMED_ANOMALY: "Anomaly confirmed",
        CaseState.ESCALATED: "Escalated",
        CaseState.INVALID_INPUT: "Invalid input",
    },
}

RESOURCE_LABELS: dict[Locale, dict[str, str]] = {
    Locale.ID: {
        "Claim": "klaim",
        "ClaimLine": "baris tagihan",
        "Encounter": "kunjungan",
        "Condition": "diagnosis",
        "Procedure": "catatan tindakan",
        "Medication": "catatan obat",
        "Diagnostic": "pemeriksaan penunjang",
        "Document": "catatan klinis",
        "Account": "akun tagihan",
        "ChargeItem": "item biaya",
        "Invoice": "faktur",
        "Episode": "episode",
        "Practitioner": "tenaga kesehatan",
    },
    Locale.EN: {
        "Claim": "claim",
        "ClaimLine": "claim line",
        "Encounter": "encounter",
        "Condition": "diagnosis",
        "Procedure": "procedure record",
        "Medication": "medication record",
        "Diagnostic": "diagnostic report",
        "Document": "clinical note",
        "Account": "billing account",
        "ChargeItem": "charge item",
        "Invoice": "invoice",
        "Episode": "episode",
        "Practitioner": "practitioner",
    },
}


def mode_label(mode: RiskMode, locale: Locale) -> str:
    return MODE_LABELS[locale][mode]


def band_label(band: PriorityBand, locale: Locale) -> str:
    return BAND_LABELS[locale][band]


def state_label(state: CaseState, locale: Locale) -> str:
    return STATE_LABELS[locale][state]


def resource_label(resource_type: object, locale: Locale) -> str:
    return RESOURCE_LABELS[locale].get(str(resource_type), str(resource_type))


def joined(items: list[str], locale: Locale) -> str:
    """"a, b, dan c" / "a, b, and c" — a list read aloud, not a comma dump."""
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    conjunction = pick(locale, "dan", "and")
    if len(items) == 2:
        return f"{items[0]} {conjunction} {items[1]}"
    return f"{', '.join(items[:-1])}, {conjunction} {items[-1]}"


# ---- Fixed notes ----------------------------------------------------------------------------

def uncertainty_queue(locale: Locale) -> str:
    return pick(
        locale,
        "Jawaban ini hanya membaca antrean dan alasan yang sudah tampil untuk peran Anda. Urutan "
        "kasus adalah urutan antrean itu sendiri; asisten tidak menyusun prioritas baru, dan "
        "tidak mengubah status atau keputusan apa pun.",
        "This answer reads only the queue and the reasons already shown to your role. The order "
        "of cases is the queue's own; the assistant sets no new priority and changes no status "
        "or decision.",
    )


def uncertainty_case(locale: Locale) -> str:
    return pick(
        locale,
        "Jawaban ini disusun hanya dari bukti yang ikut terkirim dalam bundel kasus ini. Ketiadaan "
        "catatan bukan bukti bahwa layanan tidak diberikan. Keputusan tetap pada peninjau.",
        "This answer is composed only from the evidence sent in this case's bundle. A missing "
        "record is not evidence that a service was not provided. The decision stays with the "
        "reviewer.",
    )


def template_caveat(locale: Locale) -> str:
    """The clone caveat, in the reader's language.

    `case_sources.TEMPLATE_CAVEAT` is a single Indonesian constant on the comparison candidate;
    its meaning never varies, so it is rendered here rather than echoed in the wrong language.
    """
    return pick(
        locale,
        "Dokumentasi berbasis templat menghasilkan kemiripan tinggi tanpa ada yang disalin. "
        "Baca ini sebelum mengambil keputusan.",
        "Template-based documentation produces high similarity without anything having been "
        "copied. Read this before deciding.",
    )


def uncertainty_notice(locale: Locale) -> str:
    return pick(
        locale,
        "Tidak ada data yang dibaca untuk menjawab ini.",
        "No data was read to answer this.",
    )


REFUSALS: dict[RefusalTopic, tuple[str, str]] = {
    RefusalTopic.VERDICT: (
        (
            "Pertanyaan ini meminta kesimpulan tentang niat atau kesalahan pihak tertentu. Sistem ini "
            "tidak menarik kesimpulan seperti itu: ia melaporkan risiko atau anomali yang perlu "
            "ditinjau, lengkap dengan buktinya, dan keputusan tetap pada peninjau."
        ),
        (
            "This question asks for a conclusion about someone's intent or fault. This system does "
            "not draw that conclusion: it reports risks or anomalies that need review, with their "
            "evidence, and the decision stays with the reviewer."
        ),
    ),
    RefusalTopic.DECISION: (
        (
            "Keputusan pembayaran, penolakan klaim, atau tindak lanjut terhadap fasilitas bukan "
            "wewenang asisten ini, dan tidak pernah diambil otomatis oleh sistem ini. Yang bisa "
            "saya tunjukkan adalah alasan dan bukti yang menjadi bahan keputusan peninjau."
        ),
        (
            "Payment, claim rejection, or action against a facility is not this assistant's call, "
            "and this system never takes it automatically. What I can show is the reasons and "
            "evidence the reviewer decides on."
        ),
    ),
    RefusalTopic.CLINICAL: (
        (
            "Diagnosis dan kebutuhan medis berada di luar cakupan sistem ini: tidak ada pakar klinis "
            "maupun jalur diagnostik tervalidasi di baliknya. Saya hanya bisa menunjukkan catatan "
            "yang ada di bundel dan bagaimana catatan itu dirujuk."
        ),
        (
            "Diagnosis and medical necessity are outside this system's scope: no clinical expert or "
            "validated diagnostic pathway stands behind it. I can only show the records in the "
            "bundle and how they are referenced."
        ),
    ),
    RefusalTopic.IDENTITY: (
        (
            "Sistem ini tidak menyimpan identitas asli. Semua peserta dan fasilitas memakai token "
            "pseudonim, dan seluruh datanya sintetik."
        ),
        (
            "This system holds no real identities. Every participant and facility is a pseudonymous "
            "token, and all of the data is synthetic."
        ),
    ),
    RefusalTopic.INSTRUCTIONS: (
        (
            "Batas asisten ini tidak bisa diubah dari dalam percakapan. Saya tetap hanya membaca "
            "antrean dan kasus yang tampil untuk peran Anda, dan setiap jawaban tetap merujuk sumbernya."
        ),
        (
            "This assistant's limits cannot be changed from inside the conversation. I still read "
            "only the queue and cases shown to your role, and every answer still cites its sources."
        ),
    ),
}


def refusal(topic: RefusalTopic, locale: Locale) -> str:
    indonesian, english = REFUSALS[topic]
    return pick(locale, indonesian, english)


def help_notice(locale: Locale, *, in_case: bool) -> str:
    if in_case:
        return pick(
            locale,
            "Saya belum mengenali pertanyaan ini. Untuk kasus ini saya bisa menjelaskan mengapa ia "
            "muncul, bukti apa yang belum ditemukan, apa yang melemahkan alasannya, urutan "
            "kejadiannya, dan pasangan pembandingnya.",
            "I don't recognise this question yet. For this case I can explain why it was raised, "
            "which evidence was not found, what argues against its reasons, the sequence of "
            "events, and its comparison pair.",
        )
    return pick(
        locale,
        "Saya belum mengenali pertanyaan ini. Dari antrean saya bisa meringkas kondisinya, "
        "menunjukkan kasus mana yang paling atas, dan mencari kasus menurut pola risiko, "
        "prioritas, atau status. Sebut ID kasus untuk menelusurinya.",
        "I don't recognise this question yet. From the queue I can summarise where things stand, "
        "point to the case at the top, and find cases by risk pattern, band, or status. Name a "
        "case ID to look into it.",
    )
