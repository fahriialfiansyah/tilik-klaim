"""TilikKlaim API entrypoint.

Scope guard — this service must never:
  * declare fraud, reject a claim, stop payment, impose sanctions, or alter codes;
  * decide medical necessity;
  * call an LLM anywhere in the risk decision path.
See docs/canonical/01_product_decision.md and decisions/ADR-0002-no-llm-in-risk-score.md.
"""
from fastapi import FastAPI

from app.config import get_settings
from app.router import contract, health

settings = get_settings()

app = FastAPI(
    title="TilikKlaim API",
    version=settings.engine_version,
    description="Claim evidence integrity screening. Synthetic data only.",
)

app.include_router(health.router)
app.include_router(contract.router)
