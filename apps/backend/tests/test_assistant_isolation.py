"""The assistant sits outside the risk path, and this file is what makes that a fact.

ADR-0007 § 2 and the kill criterion "anything reaches the risk path": the assistant imports
*from* the briefing and the DTOs; nothing in the risk path imports the assistant, and the
assistant reaches no store, no rule, and no screening code — the router hands it everything.
Read from syntax trees, like the briefing's guard, so a docstring naming the forbidden thing
does not trip it.
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

ASSISTANT_PACKAGE = sorted((APP / "service" / "assistant").glob("*.py"))


def _imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
    return names


def test_the_risk_path_never_imports_the_assistant() -> None:
    """If this fails, the feature reverts — ADR-0007 § Kill criteria."""
    for path in RISK_PATH:
        for name in _imports(path):
            assert "assistant" not in name, f"{path.name} imports {name}"


def test_the_assistant_reaches_no_store_no_rule_and_no_screening() -> None:
    assert ASSISTANT_PACKAGE, "the assistant package should exist"
    forbidden = (
        "app.store",
        "app.service.screening",
        "app.service.rules",
        "app.service.disposition",
        "app.service.case_query",
        "app.service.case_sources",
        "app.service.case_loader",
        "app.service.users",
        "app.service.evaluation_artifacts",
        "app.router",
    )
    for path in ASSISTANT_PACKAGE:
        for name in _imports(path):
            for prefix in forbidden:
                assert not name.startswith(prefix), f"{path.name} imports {name}"


def test_the_assistant_names_no_scoring_or_disposition_identifier() -> None:
    """It may *pass through* the band a queue row already carries; it may not name a score.

    Narrower than the briefing's guard on purpose, and recorded in ADR-0007 § 2: the queue scope
    shows the band verbatim, so `band` is allowed — `score`, a disposition, and money are not.
    """
    forbidden = ("score", "disposition", "state_after", "payment", "sanction")
    for path in ASSISTANT_PACKAGE:
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


def test_the_router_reads_through_the_same_functions_as_the_queue_and_detail() -> None:
    """The privacy argument is that the assistant sees what those endpoints show — no more."""
    imports = _imports(APP / "router" / "assistant.py")
    assert "app.service.case_loader" in imports
    assert "app.service.case_query" in imports
    assert not any(name.startswith("app.store") for name in imports)
