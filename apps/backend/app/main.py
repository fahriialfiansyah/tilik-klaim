"""TilikKlaim API entrypoint.

Scope guard — this service must never:
  * declare fraud, reject a claim, stop payment, impose sanctions, or alter codes;
  * decide medical necessity;
  * call an LLM anywhere in the risk decision path.
See docs/canonical/01_product_decision.md and decisions/ADR-0002-no-llm-in-risk-score.md.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.router import bundles, cases, dispositions, evaluations, health

settings = get_settings()

app = FastAPI(
    title="TilikKlaim API",
    version=settings.engine_version,
    description="Claim evidence integrity screening. Synthetic data only.",
)

# Web dan API berjalan di host berbeda saat di-deploy (Vercel dan Railway), jadi setiap
# panggilan dari peramban bersifat lintas-origin. Origin yang diizinkan datang dari
# konfigurasi dan tidak pernah `*`: yang dibatasi di sini adalah *siapa* yang boleh membaca
# jawaban, sedangkan metode dan header dibiarkan terbuka karena keduanya bukan batas
# keamanan — menyempitkannya hanya membuat endpoint berikutnya gagal dengan galat peramban
# yang tidak menyebut sebabnya. Tanpa origin maupun pola, middleware tidak dipasang sama
# sekali, sehingga API tetap bisa dipakai dari luar peramban (curl, test, server lain).
if settings.cors_origins or settings.cors_allow_origin_regex:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.cors_origins),
        allow_origin_regex=settings.cors_allow_origin_regex or None,
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(health.router)
app.include_router(evaluations.router)
app.include_router(bundles.router)
app.include_router(cases.router)
app.include_router(dispositions.router)
