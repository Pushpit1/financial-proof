from enum import StrEnum


class EvidenceType(StrEnum):
    BANK_STATEMENT = "bank_statement"
    PAYSLIP = "payslip"
    TAX_DOCUMENT = "tax_document"
    INVOICE = "invoice"
    PAYMENT_RECORD = "payment_record"
    ACCOUNTING_RECORD = "accounting_record"
    OTHER = "other"


class EvidenceStatus(StrEnum):
    RECEIVED = "received"
    EXTRACTING = "extracting"
    EXTRACTED = "extracted"
    VERIFIED = "verified"
    REJECTED = "rejected"


class ClaimType(StrEnum):
    INCOME = "income"
    EXPENSE = "expense"
    BALANCE = "balance"
    TRANSACTION = "transaction"
    EMPLOYMENT = "employment"
    TAX = "tax"
    CASH_FLOW = "cash_flow"
    FINANCIAL_HEALTH = "financial_health"


class VerificationStatus(StrEnum):
    UNVERIFIED = "unverified"
    SUPPORTED = "supported"
    PARTIALLY_SUPPORTED = "partially_supported"
    CONTRADICTED = "contradicted"
    VERIFIED = "verified"


class ProofStatus(StrEnum):
    DRAFT = "draft"
    PROCESSING = "processing"
    READY = "ready"
    NEEDS_REVIEW = "needs_review"
    INVALID = "invalid"


class ConfidenceLevel(StrEnum):
    VERY_LOW = "very_low"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


class EvaluationReason(StrEnum):
    NO_CLAIMS = "no_claims"
    CONTRADICTED_CLAIM = "contradicted_claim"
    UNVERIFIED_CLAIM = "unverified_claim"
    PARTIALLY_SUPPORTED_CLAIM = "partially_supported_claim"
    CONFIDENCE_BELOW_REVIEW_THRESHOLD = (
        "confidence_below_review_threshold"
    )
    CONFIDENCE_BELOW_READY_THRESHOLD = (
        "confidence_below_ready_threshold"
    )
    SUPPORTED_CLAIM_RATIO_BELOW_THRESHOLD = (
        "supported_claim_ratio_below_threshold"
    )
    EVALUATION_PASSED = "evaluation_passed"
