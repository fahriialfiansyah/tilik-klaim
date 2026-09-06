"""The versioned rule interface every detector implements.

A rule takes a bundle, its history, and the derived evidence graph, and returns reasons. Each
reason carries four things without exception:

* the **evidence** it rests on, as resource references a reviewer can open;
* the **counter-evidence** that argues against it, returned alongside — never as a second
  lookup the UI might skip;
* the **component scores** that produced it, not just an aggregate;
* the **version** of the rule that emitted it, so an old case keeps meaning what it meant.

Counter-evidence is not a courtesy. `docs/canonical/01_product_decision.md` makes showing the
argument against a signal part of the product, because a reviewer who only sees the case for a
signal cannot weigh it.
"""
from __future__ import annotations

from typing import Protocol

from pydantic import BaseModel, ConfigDict
from tilik_domain.canonical import CanonicalBundle, ResourceRef
from tilik_domain.locale import DEFAULT_LOCALE, Locale
from tilik_domain.notes import NoteCode
from tilik_domain.notes import render as render_note
from tilik_domain.reasons import ReasonCode, RiskMode, definition_for
from tilik_domain.versioning import RULESET_VERSION

from app.service.evidence_graph import EvidenceGraph


class CounterEvidence(BaseModel):
    """A fact that argues against the reason it accompanies."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    note_id: str
    """The argument in Indonesian, composed when the rule fired.

    Kept as the stored, canonical text so every case already screened stays readable and every
    existing assertion keeps holding. It is no longer what the API renders when a reader asks
    for English — `note_code` is.
    """
    note_code: NoteCode | None = None
    """Which catalogued argument this is, so it can be rendered in either language.

    Optional only for records screened before the catalog existed. Rules raised from here on
    always set it; `test_rules_gold` asserts every note a rule emits carries one.
    """
    note_params: tuple[tuple[str, str], ...] = ()
    """Facts the note's template needs, as ordered pairs.

    Ordered rather than a dict for the same reason `component_scores` is: the hit is frozen and
    stored, and two screenings of one bundle must serialise identically.
    """
    refs: tuple[ResourceRef, ...] = ()

    def render(self, locale: Locale = DEFAULT_LOCALE) -> str:
        """This argument in one language, falling back to the stored Indonesian sentence."""
        return render_note(self.note_code, self.note_id, locale, **dict(self.note_params))

    @classmethod
    def of(
        cls,
        code: NoteCode,
        *,
        refs: tuple[ResourceRef, ...] = (),
        **params: object,
    ) -> CounterEvidence:
        """Build a counter-evidence note from the catalog.

        Rules name the argument and supply its facts; the wording comes from `notes.py`. This
        is the only way a rule should construct one — writing the sentence at the call site
        again would put a second copy of the catalog in the rules, free to drift from the copy
        the API renders, and the reviewer would have no way to tell which one they were reading.

        `note_id` is filled with the Indonesian rendering because that is the canonical stored
        text: the hit is persisted, and a case must stay readable even if the catalog is later
        reworded. Re-rendering by code is what serves any *other* language.
        """
        stringified = tuple(sorted((key, str(value)) for key, value in params.items()))
        return cls(
            note_id=render_note(code, "", DEFAULT_LOCALE, **params),
            note_code=code,
            note_params=stringified,
            refs=refs,
        )


class ReasonHit(BaseModel):
    """One reason a case was raised, with everything needed to review it."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    code: ReasonCode
    mode: RiskMode
    sentence_id: str
    evidence: tuple[ResourceRef, ...]
    counter_evidence: tuple[CounterEvidence, ...] = ()
    component_scores: tuple[tuple[str, float], ...] = ()
    """Every component that fed this reason, as ordered pairs so the record stays comparable."""
    deterministic: bool
    rule_id: str
    ruleset_version: str = RULESET_VERSION

    def score(self, name: str) -> float | None:
        return next((value for key, value in self.component_scores if key == name), None)


class RuleContext(BaseModel):
    """Everything a rule may read. Nothing here reveals the fixture's answer key."""

    model_config = ConfigDict(frozen=True, extra="forbid", arbitrary_types_allowed=True)

    bundle: CanonicalBundle
    history: tuple[CanonicalBundle, ...] = ()
    graph: EvidenceGraph


class Rule(Protocol):
    """A detector for one risk mode."""

    rule_id: str
    mode: RiskMode

    def evaluate(self, context: RuleContext) -> tuple[ReasonHit, ...]:
        """Return every reason this rule observes. An empty tuple means nothing observed."""
        ...


def make_hit(
    code: ReasonCode,
    *,
    rule_id: str,
    evidence: tuple[ResourceRef, ...],
    counter_evidence: tuple[CounterEvidence, ...] = (),
    component_scores: tuple[tuple[str, float], ...] = (),
) -> ReasonHit:
    """Build a hit from the catalog, so wording and mode can never drift from the contract."""
    definition = definition_for(code)
    return ReasonHit(
        code=code,
        mode=definition.mode,
        sentence_id=definition.sentence_id,
        evidence=evidence,
        counter_evidence=counter_evidence,
        component_scores=component_scores,
        deterministic=definition.deterministic,
        rule_id=rule_id,
        ruleset_version=definition.ruleset_version,
    )


class RuleRegistry:
    """The ordered set of rules a screening run applies.

    Order is fixed at registration so two runs of the same bundle produce reasons in the same
    sequence — a screening result that reorders itself is not reproducible.
    """

    def __init__(self, rules: tuple[Rule, ...]) -> None:
        seen = [rule.rule_id for rule in rules]
        duplicates = {rule_id for rule_id in seen if seen.count(rule_id) > 1}
        if duplicates:
            raise ValueError(f"duplicate rule ids would make results ambiguous: {duplicates}")
        self._rules = rules

    @property
    def rules(self) -> tuple[Rule, ...]:
        return self._rules

    def rule_ids(self) -> tuple[str, ...]:
        return tuple(rule.rule_id for rule in self._rules)

    def evaluate(self, context: RuleContext) -> tuple[ReasonHit, ...]:
        return tuple(hit for rule in self._rules for hit in rule.evaluate(context))
