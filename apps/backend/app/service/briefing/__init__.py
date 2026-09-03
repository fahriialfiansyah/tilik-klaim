"""The bounded, read-only Case Briefing (ADR-0005).

Sits *outside* the risk path: it reads the already-built case detail and writes nothing. The
public surface is `build_briefing` and `stream_briefing` in `runner.py`; the tool surface is
`tools.py`; the LLM-free default is `template.py`; the gate is `validation.py`.
"""
