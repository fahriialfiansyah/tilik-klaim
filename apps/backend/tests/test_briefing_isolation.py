"""The briefing sits outside the risk path, and this file is what makes that a fact.

ADR-0005 § Decision 1: the briefing module imports *from* the risk path; nothing in the risk
path imports the briefing. Read from syntax trees rather than text, like the disposition
guard in `test_disposition.py`, so a docstring naming the forbidden thing does not trip it.
"""
from __future__ import annotations

import ast
from pathlib import Path

APP = Path(__file__).resolve().parents[1] / "app"

RISK_PATH = (
    APP / "service" / "screening.py",
    APP / "service" / "disposition.py",
    APP / "service" / "case_query.py",
    APP / "service" / "case_sources.py",
    APP / "service" / "evidence_graph.py",
    *sorted((APP / "service" / "rules").glob("*.py")),
    *sorted((APP / "store").glob("*.py")),
)

BRIEFING_PACKAGE = sorted((APP / "service" / "briefing").glob("*.py"))


def _imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
    return names


def test_the_risk_path_never_imports_the_briefing() -> None:
    """The single most important test in the feature. If it fails, the feature reverts."""
    for path in RISK_PATH:
        for name in _imports(path):
            assert "briefing" not in name, f"{path.name} imports {name}"
            assert "llm_provider" not in name, f"{path.name} imports {name}"


def test_the_briefing_reaches_no_store_and_no_rule() -> None:
    """Its whole tool surface is the already-built detail response; nothing else is reachable."""
    assert BRIEFING_PACKAGE, "the briefing package should exist"
    forbidden = ("app.store", "app.service.screening", "app.service.rules",
                 "app.service.disposition", "app.service.case_query", "app.service.case_sources")
    for path in BRIEFING_PACKAGE:
        for name in _imports(path):
            for prefix in forbidden:
                assert not name.startswith(prefix), f"{path.name} imports {name}"


def test_briefing_module_names_no_scoring_or_disposition_identifier() -> None:
    """A briefing that could *name* a score is one step from writing about it."""
    forbidden = ("band", "score", "priority", "disposition", "state_after", "payment", "sanction")
    for path in BRIEFING_PACKAGE:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        identifiers: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                identifiers.add(node.id.lower())
            elif isinstance(node, ast.Attribute):
                identifiers.add(node.attr.lower())
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                identifiers.add(node.name.lower())
            elif isinstance(node, ast.arg):
                identifiers.add(node.arg.lower())
        for name in sorted(identifiers):
            for word in forbidden:
                assert word not in name, f"{path.name} names {name!r}"
