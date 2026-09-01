"""Character n-gram TF-IDF similarity between clinical notes — the transparent baseline.

`docs/canonical/05_model_card.md` names this as the baseline for cloned documentation, and
ADR-0002 forbids anything learned or generative in the risk path. Character n-grams are chosen
over word tokens because Indonesian clinical notes are heavily abbreviated and inconsistently
spaced, and because a reviewer can be shown the matched fragments.

**What a high score is not.** Shared forms and templates produce very high similarity between
notes nobody copied, and a patient with a recurring complaint produces near-identical notes
legitimately. The score is an argument for a look, never a finding — `ranking.py` enforces that
by capping what similarity alone can reach, and the reason catalog's counter-evidence says the
templating caveat out loud on screen.

Comparison is against **peer** notes: other participants at the same facility. Cloning is a
facility-level pattern, and scoring a participant against their own history would flag ordinary
continuity of care.
"""
from __future__ import annotations

from collections.abc import Sequence

from pydantic import BaseModel, ConfigDict
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from tilik_domain.canonical import DocumentRef

from tilik_model.version import SIMILARITY_VERSION

NGRAM_RANGE = (3, 5)
"""Character n-gram sizes. Short enough to survive abbreviation, long enough to carry phrasing."""

MINIMUM_NOTE_CHARACTERS = 12
"""Below this, a note carries too little text to say anything about copying.

Two notes reading "ok" are identical and mean nothing. Scoring them would manufacture a signal
out of an empty record, which is the exact failure this project exists to avoid.
"""

MINIMUM_DOCUMENT_FREQUENCY = 1


class SimilarityScore(BaseModel):
    """One bundle's similarity to its facility peers, with what produced it."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    value: float = 0.0
    matched_document_id: str | None = None
    """The peer note that produced the score, so a reviewer can open it."""
    comparisons: int = 0
    """How many peer notes were actually compared. Zero means the score is an absence."""

    version: str = SIMILARITY_VERSION


class NoteSimilarity:
    """A fitted character n-gram vectoriser and the scoring it supports.

    Fitted on **training** notes only. A vocabulary built over the whole corpus would carry
    test-set phrasing into the representation, which is a quiet way to make an evaluation
    flatter than it should be.
    """

    def __init__(self, vectorizer: TfidfVectorizer | None) -> None:
        self._vectorizer = vectorizer

    @property
    def is_fitted(self) -> bool:
        """False when there was nothing usable to fit on; scoring then returns a plain zero."""
        return self._vectorizer is not None

    @classmethod
    def fit(cls, notes: Sequence[str]) -> NoteSimilarity:
        usable = [note for note in notes if _is_usable(note)]
        if not usable:
            # No vocabulary. An inert model that says "no opinion" beats an exception at
            # scoring time, because a corpus with no notes is a legitimate input.
            return cls(None)

        vectorizer = TfidfVectorizer(
            analyzer="char_wb",
            ngram_range=NGRAM_RANGE,
            min_df=MINIMUM_DOCUMENT_FREQUENCY,
            lowercase=True,
        )
        vectorizer.fit(usable)
        return cls(vectorizer)

    def score(
        self,
        documents: Sequence[DocumentRef],
        peer_documents: Sequence[DocumentRef],
    ) -> SimilarityScore:
        """Highest similarity between any note on this claim and any peer note."""
        mine = [document for document in documents if _is_usable(document.text)]
        theirs = [document for document in peer_documents if _is_usable(document.text)]
        if not self.is_fitted or not mine or not theirs:
            return SimilarityScore()

        assert self._vectorizer is not None  # narrowed by is_fitted
        left = self._vectorizer.transform([document.text or "" for document in mine])
        right = self._vectorizer.transform([document.text or "" for document in theirs])
        matrix = cosine_similarity(left, right)

        best_row, best_column = _argmax(matrix)
        return SimilarityScore(
            value=float(min(max(matrix[best_row][best_column], 0.0), 1.0)),
            matched_document_id=theirs[best_column].document_id,
            comparisons=len(mine) * len(theirs),
        )


def _is_usable(text: str | None) -> bool:
    """A note is usable when it exists and carries enough characters to judge."""
    return bool(text) and len(text.strip()) >= MINIMUM_NOTE_CHARACTERS  # type: ignore[arg-type]


def _argmax(matrix) -> tuple[int, int]:
    """Row and column of the largest entry, chosen deterministically on ties."""
    flat = int(matrix.argmax())
    return divmod(flat, matrix.shape[1])
