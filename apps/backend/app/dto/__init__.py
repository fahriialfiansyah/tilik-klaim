"""Wire models for the seven endpoints in `docs/canonical/03_architecture.md`.

This package *is* the frozen contract. The frontend builds against the fixtures generated
from these models, which is what lets M1 and M2 work in parallel instead of serially.
Changing a field here breaks that parallelism — treat it as a contract change, not a refactor.
"""
from app.dto.bundles import (
    IngestBundleResponse,
    ResourceCount,
    ScreenRequest,
    ScreenResponse,
    ValidationStatus,
)
from app.dto.cases import (
    CaseDetailResponse,
    CaseQueueResponse,
    CaseSummary,
    ClaimLineView,
    ComparisonCandidate,
    ComparisonField,
    EvidenceCompleteness,
    QueueMetrics,
    TimelineEvent,
)
from app.dto.common import (
    BandExplanation,
    Dto,
    EvidenceRefDto,
    PageInfo,
    ReasonDto,
    VersionStamp,
)
from app.dto.dispositions import (
    AuditEvent,
    AuditResponse,
    DispositionRequest,
    DispositionResponse,
)
from app.dto.evaluations import (
    BaselineMetrics,
    EvaluationResponse,
    LimitationsCard,
    ModeMetrics,
    RunManifest,
)

__all__ = [
    "AuditEvent",
    "AuditResponse",
    "BandExplanation",
    "BaselineMetrics",
    "CaseDetailResponse",
    "CaseQueueResponse",
    "CaseSummary",
    "ClaimLineView",
    "ComparisonCandidate",
    "ComparisonField",
    "DispositionRequest",
    "DispositionResponse",
    "Dto",
    "EvaluationResponse",
    "EvidenceCompleteness",
    "EvidenceRefDto",
    "IngestBundleResponse",
    "LimitationsCard",
    "ModeMetrics",
    "PageInfo",
    "QueueMetrics",
    "ReasonDto",
    "ResourceCount",
    "RunManifest",
    "ScreenRequest",
    "ScreenResponse",
    "TimelineEvent",
    "ValidationStatus",
    "VersionStamp",
]
