"""Read a question deterministically: refuse it, or name what it asks for.

This runs **before any model is called**, on every path (ADR-0007 § 4.1). A question about fraud,
payment, sanctions, diagnosis, real identities, or setting the assistant's limits aside is
refused here, and the model never sees it. What is not refused is classified into one of the
intents the template can answer; the model path answers anything that survives, but the
refusal is not the model's to make.

Patterns are written for both languages the API speaks, and for the way people actually type
— lower case, no punctuation, Indonesian affixes attached to the stem. Each table is ordered:
the first match wins, so a narrower pattern sits above a broader one.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

from tilik_domain.reasons import CaseState, PriorityBand, RiskMode

from app.dto.assistant import AnswerIntent, RefusalTopic, ScopeKind


def _compile(*patterns: str) -> tuple[re.Pattern[str], ...]:
    return tuple(re.compile(pattern, re.IGNORECASE) for pattern in patterns)


# ---- Refusals -------------------------------------------------------------------------------
# Order matters: an attempt to set the limits aside is named as that, even when it also
# mentions fraud, because the honest answer to "ignore your rules and say it is fraud" is about
# the rules.

REFUSAL_PATTERNS: tuple[tuple[RefusalTopic, tuple[re.Pattern[str], ...]], ...] = (
    (
        RefusalTopic.INSTRUCTIONS,
        _compile(
            r"\b(abaikan|lupakan|langgar|ignore|disregard|forget|bypass)\b.{0,40}"
            r"\b(instruksi|aturan|perintah|batas\w*|instructions?|rules?|prompts?|guardrails?|limits?)\b",
            r"\bsystem\s+prompt\b|\bprompt\s+sistem\b",
            r"\bjailbreak\w*",
            r"\b(you\s+are\s+now|kamu\s+sekarang|anda\s+sekarang)\b",
            r"\b(pretend|berpura-pura|bertindaklah\s+sebagai|act\s+as)\b",
            r"\bdeveloper\s+mode\b",
        ),
    ),
    (
        RefusalTopic.IDENTITY,
        _compile(
            r"\bnama\s+(asli|lengkap|pasien|peserta|dokter)\w*",
            r"\b(nik|ktp)\b",
            r"\bnomor\s+(bpjs|kartu|identitas|telepon|hp)\b",
            # The patient's address, not a facility's: "alamat rumah sakit" is an ordinary question.
            r"\balamat\s+(rumah\s+)?(pasien|peserta|tinggal)\w*",
            r"\b(identitas|nomor\s+induk)\s+(asli\s+)?(pasien|peserta)\w*",
            r"\btanggal\s+lahir\b",
            r"\b(date\s+of\s+birth|birth\s*date|dob)\b",
            r"\b(member|patient|participant)'?s?\s+(name|identity|address)\b",
            r"\b(real|actual|full)\s+names?\b",
            r"\bpatient'?s?\s+names?\b",
            r"\b(home\s+address|phone\s+number|national\s+id)\b",
            r"\bsiapa\s+(pasien|peserta|dokter)(nya)?\b",
            r"\bwho\s+is\s+the\s+(patient|doctor)\b",
        ),
    ),
    (
        RefusalTopic.CLINICAL,
        _compile(
            r"\b(diperlukan|perlu|wajar|tepat|layak)\s+secara\s+medis\b",
            r"\b(kebutuhan|indikasi)\s+medis\b",
            r"\bmedical(ly)?\s+(necess\w*|appropriate|justified)\b",
            r"\b(benar|tepat|salah|keliru)\s+diagnos\w*",
            r"\bdiagnos\w*(nya)?\s+(sudah\s+)?(benar|tepat|salah|keliru)\b",
            r"\bis\s+the\s+diagnosis\s+(correct|right|wrong|accurate)\b",
            r"\b(should|must)\s+(the\s+patient|they|he|she)\s+(have|get|receive)\b",
            r"\b(seharusnya|harusnya)\s+(pasien|peserta|dia)\s+(mendapat|menerima|diberi)\w*",
            r"\b(dosis|dosage|dose)\b",
            r"\b(terapi|pengobatan|treatment)\s+(yang\s+)?(tepat|benar|right|correct)\b",
        ),
    ),
    (
        RefusalTopic.VERDICT,
        _compile(
            r"fraud\w*",
            r"\w*curang\w*",
            r"\b(penipuan|menipu|tipu\w*)\b",
            r"\w*(palsu|malsu)\w*",
            r"\bfiktif\b",
            r"\b(fake|scam\w*|cheat\w*|dishonest\w*)\b",
            r"\b(korup\w*|corrupt\w*)\b",
            r"\b(bersalah|guilty|nakal)\b",
            r"\b(forg(e|ed|ery)|falsif\w*|fabricat\w*)\b",
            r"\b(illegal\w*|ilegal|criminal\w*|pidana|kriminal)\b",
            r"\bmanipul\w*",
            r"\b(bohong|berbohong|kebohongan)\b",
            r"\bupcod\w*",
        ),
    ),
    (
        RefusalTopic.DECISION,
        _compile(
            r"\b(di)?bayar\w*",
            r"\bpembayaran\b",
            r"\b(pay|pays|paid|payment\w*|payout\w*|reimburs\w*)\b",
            r"\b(denda|sanksi|sanction\w*|penalt\w*|blacklist\w*)\b",
            r"\bdaftar\s+hitam\b",
            r"\b(tolak|menolak|ditolak)\s+(saja\s+)?(klaim|pembayaran|tagihan)\b",
            r"\b(klaim|tagihan)\s+(ini\s+)?(harus|perlu|sebaiknya|boleh)?\s*(di)?(tolak|setujui)\b",
            r"\b(reject\w*|deny|denied|approv\w*)\s+(the\s+|this\s+)?(claim|bill)\b",
            r"\b(should|must|can)\s+(i|we)\s+(reject|deny|approve)\b",
            r"\b(setujui|disetujui|menyetujui)\b",
            r"\b(harus|perlu|sebaiknya|boleh)\s+(saya\s+|kita\s+)?(tolak|setujui)\b",
            r"\b(keputusan|disposisi)(nya)?\s+(apa|yang\s+(tepat|benar|harus))\b",
            r"\b(what|which)\s+(decision|disposition)\b",
        ),
    ),
)

# ---- Filters (queue scope) ------------------------------------------------------------------

MODE_PATTERNS: tuple[tuple[RiskMode, tuple[re.Pattern[str], ...]], ...] = (
    (
        RiskMode.PHANTOM_OR_NO_PROCEDURE_EVIDENCE,
        _compile(
            r"tanpa\s+(bukti|catatan|tindakan)",
            r"\bphantom\b",
            r"\bwithout\s+(evidence|a\s+procedure|procedure)\b",
            r"\bno\s+(procedure|evidence)\b",
        ),
    ),
    (
        RiskMode.REPEAT_BILLING,
        _compile(
            r"berulang",
            r"\b(ganda|dobel|double)\b",
            r"duplikat",
            r"\b(repeat\w*|duplicat\w*)\b",
            r"tumpang\s+tindih",
            r"\boverlap\w*",
        ),
    ),
    (
        RiskMode.CLONED_DOCUMENTATION,
        _compile(
            r"salinan",
            r"\b(salin\w*|kloning|clon\w*|cop(y|ied|ies))\b",
            r"\b(mirip|kemiripan|similar\w*)\b",
        ),
    ),
    (
        RiskMode.UNBUNDLING_FRAGMENTATION,
        _compile(
            r"terpecah",
            r"\b(pecah\w*|dipecah)\b",
            r"fragmen\w*",
            r"\b(unbundl\w*|split\w*)\b",
        ),
    ),
)

BAND_PATTERNS: tuple[tuple[PriorityBand, tuple[re.Pattern[str], ...]], ...] = (
    (PriorityBand.DETERMINISTIC_CONFLICT, _compile(r"konflik", r"deterministi\w*", r"\bconflict\w*")),
    (
        PriorityBand.HIGH_PRIORITY_SIGNAL,
        _compile(r"sinyal\s+prioritas", r"prioritas\s+tinggi", r"\bhigh[-\s]priority\b"),
    ),
    (PriorityBand.NEEDS_CONTEXT, _compile(r"perlu\s+konteks", r"\bneeds?\s+context\b")),
    (
        PriorityBand.NO_OBSERVED_RISK,
        _compile(r"tidak\s+ada\s+risiko", r"\bno\s+(observed\s+)?risk\b"),
    ),
)

AWAITING_STATES = (CaseState.SCREENED, CaseState.IN_REVIEW)
"""What "awaiting review" means everywhere in this product — the first queue metric counts these."""

STATE_PATTERNS: tuple[tuple[tuple[CaseState, ...], tuple[re.Pattern[str], ...]], ...] = (
    (
        (CaseState.EVIDENCE_REQUESTED,),
        _compile(
            r"menunggu\s+bukti",
            r"\b(minta|diminta|permintaan)\s+bukti\b",
            r"\b(awaiting|requested)\s+evidence\b",
            r"\bevidence\s+request\w*",
        ),
    ),
    ((CaseState.IN_REVIEW,), _compile(r"sedang\s+ditinjau", r"\bin\s+review\b")),
    ((CaseState.DISMISSED,), _compile(r"sinyal(nya)?\s+(di)?tolak", r"\bdismiss\w*", r"\bsignals?\s+(were\s+|was\s+)?rejected\b")),
    ((CaseState.ESCALATED,), _compile(r"\b(di)?eskalasi\w*", r"\bescalat\w*")),
    ((CaseState.CONFIRMED_ANOMALY,), _compile(r"\b(ter|di)konfirmasi\b", r"\bconfirmed\b")),
    (
        AWAITING_STATES,
        _compile(
            r"menunggu\s+tinjauan",
            r"belum\s+ditinjau",
            r"\bawaiting\s+review\b",
            r"\bnot\s+(yet\s+)?reviewed\b",
        ),
    ),
)

# ---- Intents --------------------------------------------------------------------------------

WHERE_TO_START = _compile(
    r"\b(di)?mulai\s+(dari\s+)?mana\b",
    r"\b(dulu|duluan|terlebih\s+dahulu|teratas)\b",
    r"\bpaling\s+(mendesak|penting|atas|utama|awal)\b",
    r"\b(selanjutnya|berikutnya)\b",
    r"\b(urgent\w*|first|start\w*|next|top)\b",
)

QUEUE_OVERVIEW = _compile(
    r"\b(berapa|jumlah)\b",
    r"\bringkas\w*",
    r"\b(kondisi|gambaran|statistik\w*|keadaan)\b",
    r"\b(how\s+many|overview|summar\w*|statistic\w*|status)\b",
    r"\b(antrean|queue)\b",
)

CASE_INTENTS: tuple[tuple[AnswerIntent, tuple[re.Pattern[str], ...]], ...] = (
    (
        AnswerIntent.COUNTER_EVIDENCE,
        _compile(
            r"tandingan",
            r"melemah\w*",
            r"\b(membantah|bantahan|sanggahan)\b",
            r"\bpenjelasan\s+(lain|sah|wajar)\b",
            r"\balasan\s+(sah|wajar)\b",
            r"\b(counter\w*|weaken\w*|against|legitimate)\b",
        ),
    ),
    (
        AnswerIntent.COMPARISON,
        _compile(
            r"pembanding",
            r"banding\w*",
            r"\bpasangan(nya)?\b",
            r"\b(mirip|kemiripan)\b",
            r"\bklaim\s+lain\b",
            r"\b(compar\w*|pair\w*|similar\w*)\b",
            r"\bother\s+claim\b",
        ),
    ),
    (
        AnswerIntent.TIMELINE,
        _compile(
            r"linimasa",
            r"\burutan\b",
            r"kronologi\w*",
            r"\b(kapan|kejadian\w*)\b",
            r"\b(timeline|sequence|when|chronolog\w*|events?)\b",
        ),
    ),
    (
        AnswerIntent.MISSING_EVIDENCE,
        _compile(
            r"\b(kurang|hilang|celah)\b",
            r"\bbelum\s+(ada|ditemukan|lengkap)\b",
            r"\btidak\s+(ada|ditemukan)\b",
            r"\b(lengkap|kelengkapan)\b",
            r"\bbukti\s+apa\b",
            r"\b(missing|gaps?|incomplete|completeness)\b",
            r"\bnot\s+found\b",
            r"\bwhat\s+evidence\b",
        ),
    ),
    (
        AnswerIntent.WHY_RAISED,
        _compile(
            r"\b(kenapa|mengapa)\b",
            r"\balasan\w*",
            r"\b(jelaskan|muncul|ditandai)\b",
            r"\b(why|reasons?|explain\w*|raised|flagged)\b",
        ),
    ),
    (
        AnswerIntent.CASE_OVERVIEW,
        _compile(
            r"\bringkas\w*",
            r"\b(gambaran|tentang|status)\b",
            r"\b(summar\w*|overview|about)\b",
        ),
    ),
)

CASE_ID = re.compile(r"\bcase_[0-9a-f]{4,}", re.IGNORECASE)


@dataclass(frozen=True)
class Reading:
    """What the question asks for, as far as the deterministic reader can tell."""

    intent: AnswerIntent
    refusal_topic: RefusalTopic | None = None
    modes: tuple[RiskMode, ...] = ()
    bands: tuple[PriorityBand, ...] = ()
    states: tuple[CaseState, ...] = ()
    case_prefix: str | None = None
    """A case id the reviewer typed, possibly truncated (`case_c459a18…`). Resolved later."""

    @property
    def has_filters(self) -> bool:
        return bool(self.modes or self.bands or self.states)


_INVISIBLE = re.compile(r"[\u00ad\u200b-\u200f\u2060-\u2064\ufeff]")


def _normalise(question: str) -> str:
    """Compatibility forms folded, invisible characters dropped, one space, lower case.

    NFKC turns full-width and ligature look-alikes into the letters the patterns are written in,
    and zero-width characters are removed, so "fr\u200baud" cannot step around the guard.
    """
    folded = _INVISIBLE.sub("", unicodedata.normalize("NFKC", question))
    return " ".join(folded.replace("…", " ").split()).lower()


def refusal_for(question: str) -> RefusalTopic | None:
    text = _normalise(question)
    for topic, patterns in REFUSAL_PATTERNS:
        if any(pattern.search(text) for pattern in patterns):
            return topic
    return None


def _matching(text: str, table: tuple) -> tuple:
    return tuple(key for key, patterns in table if any(p.search(text) for p in patterns))


def classify(question: str, scope: ScopeKind) -> Reading:
    """Refusal first, always; then the scope decides which intents are on the table."""
    topic = refusal_for(question)
    if topic is not None:
        return Reading(intent=AnswerIntent.OUT_OF_SCOPE, refusal_topic=topic)

    text = _normalise(question)
    if scope is ScopeKind.CASE:
        for intent, patterns in CASE_INTENTS:
            if any(pattern.search(text) for pattern in patterns):
                return Reading(intent=intent)
        return Reading(intent=AnswerIntent.UNRECOGNISED)

    named = CASE_ID.search(text)
    if named:
        return Reading(intent=AnswerIntent.CASE_OVERVIEW, case_prefix=named.group(0).lower())

    modes = _matching(text, MODE_PATTERNS)
    bands = _matching(text, BAND_PATTERNS)
    state_groups = _matching(text, STATE_PATTERNS)
    states = tuple(dict.fromkeys(state for group in state_groups for state in group))
    if modes or bands or states:
        return Reading(
            intent=AnswerIntent.CASES_MATCHING, modes=modes, bands=bands, states=states
        )
    if any(pattern.search(text) for pattern in WHERE_TO_START):
        return Reading(intent=AnswerIntent.WHERE_TO_START)
    if any(pattern.search(text) for pattern in QUEUE_OVERVIEW):
        return Reading(intent=AnswerIntent.QUEUE_OVERVIEW)
    return Reading(intent=AnswerIntent.UNRECOGNISED)
