"""Asisten Bukti — the bounded, evidence-cited assistant page (ADR-0007).

Sits *outside* the risk path, beside the briefing it borrows from: it reads projections the
router built from responses the same role already receives, and writes nothing. The public
surface is `answer_question` and `stream_answer` in `service.py`; the deterministic classifier
and its refusals are `intents.py`; the LLM-free default is `template.py`; the gate is
`validation.py`; the model loop is `runner.py`.
"""
