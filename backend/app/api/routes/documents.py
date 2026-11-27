"""Document ingestion, extraction, reconciliation, and proof report export routes."""

from __future__ import annotations

import csv
import hashlib
import io
import json
import os
import re
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import get_financial_proof_service
from app.application.services.financial_proof import (
    FinancialProofApplicationService,
)
from app.db.models.financial import EvidenceModel
from app.db.session import get_db

router = APIRouter(tags=["documents-and-reports"])

MAX_UPLOAD_BYTES = 5 * 1024 * 1024  # 5 MB strict ceiling
ALLOWED_EXTENSIONS = {".csv", ".json", ".txt", ".pdf"}
_SAFE_NAME_RE = re.compile(r"[^A-Za-z0-9._-]")


class ExtractedRow(BaseModel):
    row_index: int
    reference: str | None = None
    amount: str
    currency: str
    status: str | None = None


class DocumentUploadResponse(BaseModel):
    evidence_id: UUID
    filename: str
    extension: str
    size_bytes: int
    checksum_sha256: str
    duplicate_checksum_detected: bool
    persisted: bool
    proof_id: UUID | None
    extracted_row_count: int
    total_amount: str
    extraction_confidence: str
    extracted_rows: list[ExtractedRow]
    warnings: list[str]


class ReconciliationRowInput(BaseModel):
    reference: str = Field(..., min_length=1)
    amount: Decimal
    currency: str = Field(default="INR", min_length=3, max_length=3)
    status: str = Field(default="captured", min_length=1)


class ReconciliationRunRequest(BaseModel):
    internal_records: list[ReconciliationRowInput]
    provider_records: list[ReconciliationRowInput]


class ReconciliationDiscrepancy(BaseModel):
    discrepancy_type: str
    reference: str
    expected: str
    actual: str
    exposure: str


class ReconciliationRunResponse(BaseModel):
    reconciliation_id: UUID
    matched_count: int
    discrepancy_count: int
    total_exposure: str
    discrepancies: list[ReconciliationDiscrepancy]


def _sanitize_filename(raw: str | None) -> str:
    base = os.path.basename(raw or "document.txt")
    cleaned = _SAFE_NAME_RE.sub("_", base).lstrip(".")
    return cleaned or "document.txt"


def _parse_decimal(raw: object) -> Decimal | None:
    if raw is None:
        return None
    text = str(raw).strip().replace(",", "")
    if not text:
        return None
    try:
        return Decimal(text)
    except InvalidOperation:
        return None


def _extract_document(
    ext: str, content: bytes
) -> tuple[list[ExtractedRow], list[str], str]:
    warnings: list[str] = []
    rows: list[ExtractedRow] = []

    if ext == ".csv":
        decoded = content.decode("utf-8", errors="replace")
        reader = csv.DictReader(io.StringIO(decoded))
        for idx, rec in enumerate(reader, start=1):
            norm = {str(k).strip().lower(): v for k, v in rec.items() if k}
            amt = _parse_decimal(
                norm.get("amount") or norm.get("total") or norm.get("value")
            )
            if amt is None:
                warnings.append(f"Row {idx}: missing or invalid decimal amount.")
                continue
            rows.append(
                ExtractedRow(
                    row_index=idx,
                    reference=norm.get("reference")
                    or norm.get("id")
                    or norm.get("transaction_id"),
                    amount=str(amt),
                    currency=str(norm.get("currency") or "INR").strip().upper()[:3],
                    status=norm.get("status"),
                )
            )
        return rows, warnings, "0.95" if rows else "0.25"

    if ext == ".json":
        try:
            parsed = json.loads(content.decode("utf-8"))
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=f"Invalid JSON document: {exc}",
            ) from exc
        items = parsed if isinstance(parsed, list) else parsed.get("records", [parsed])
        for idx, item in enumerate(items, start=1):
            if not isinstance(item, dict):
                continue
            amt = _parse_decimal(item.get("amount") or item.get("total"))
            if amt is None:
                warnings.append(f"Record {idx}: missing numeric amount.")
                continue
            rows.append(
                ExtractedRow(
                    row_index=idx,
                    reference=str(item.get("reference") or item.get("id") or f"row-{idx}"),
                    amount=str(amt),
                    currency=str(item.get("currency") or "INR").upper()[:3],
                    status=str(item.get("status")) if item.get("status") else None,
                )
            )
        return rows, warnings, "0.95" if rows else "0.30"

    # TXT / PDF: safe byte/text pattern scan without unsafe deserialization
    decoded = content.decode("latin-1", errors="ignore")
    matches = re.findall(r"\b(INR|USD|EUR|GBP)?\s*([0-9]+(?:\.[0-9]{1,4})?)\b", decoded)
    for idx, (cur, num) in enumerate(matches[:50], start=1):
        amt = _parse_decimal(num)
        if amt is None or amt <= Decimal("0"):
            continue
        rows.append(
            ExtractedRow(
                row_index=idx,
                reference=f"line-{idx}",
                amount=str(amt),
                currency=(cur or "INR").upper(),
                status="extracted_unverified",
            )
        )
    if ext == ".pdf":
        warnings.append(
            "PDF parsed via safe raw-text stream scan; verify extracted figures manually."
        )
    return rows, warnings, "0.60" if rows else "0.10"


@router.post(
    "/documents/upload",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_financial_document(
    file: UploadFile = File(...),  # noqa: B008
    proof_id: UUID | None = Form(default=None),  # noqa: B008
    db: Session = Depends(get_db),  # noqa: B008
) -> DocumentUploadResponse:
    """Validate, checksum, extract structured financial lines, and optionally persist evidence."""
    filename = _sanitize_filename(file.filename)
    _, ext = os.path.splitext(filename.lower())
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"Unsupported file type '{ext}'. Allowed: {sorted(ALLOWED_EXTENSIONS)}",
        )

    content = await file.read(MAX_UPLOAD_BYTES + 1)
    if len(content) == 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Uploaded document is empty.",
        )
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail="Uploaded document exceeds 5 MB security limit.",
        )

    checksum = hashlib.sha256(content).hexdigest()
    rows, warnings, confidence = _extract_document(ext, content)
    total_amount = sum((Decimal(r.amount) for r in rows), Decimal("0"))

    duplicate = False
    persisted = False
    evidence_id = uuid4()

    try:
        existing = db.scalar(
            select(EvidenceModel).where(EvidenceModel.checksum == checksum)
        )
        duplicate = existing is not None
        model = EvidenceModel(
            id=evidence_id,
            evidence_type="bank_statement" if ext == ".csv" else "financial_document",
            source_name=filename,
            received_at=datetime.now(UTC).date(),
            proof_id=proof_id,
            status="verified" if rows else "received",
            checksum=checksum,
            source_reference=f"upload://{filename}#{checksum[:12]}",
        )
        db.add(model)
        db.commit()
        persisted = True
    except Exception as exc:
        db.rollback()
        warnings.append(f"Persistence skipped: {type(exc).__name__}")

    return DocumentUploadResponse(
        evidence_id=evidence_id,
        filename=filename,
        extension=ext,
        size_bytes=len(content),
        checksum_sha256=checksum,
        duplicate_checksum_detected=duplicate,
        persisted=persisted,
        proof_id=proof_id,
        extracted_row_count=len(rows),
        total_amount=str(total_amount),
        extraction_confidence=confidence,
        extracted_rows=rows,
        warnings=warnings,
    )


@router.get("/documents")
async def list_documents(
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),  # noqa: B008
) -> list[dict[str, object]]:
    """List persisted financial documents and evidence records."""
    rows = db.scalars(select(EvidenceModel).limit(limit)).all()
    return [
        {
            "id": str(r.id),
            "evidence_type": r.evidence_type,
            "source_name": r.source_name,
            "received_at": r.received_at.isoformat(),
            "proof_id": str(r.proof_id) if r.proof_id else None,
            "status": r.status,
            "checksum": r.checksum,
            "source_reference": r.source_reference,
        }
        for r in rows
    ]


@router.post("/reconciliation/run", response_model=ReconciliationRunResponse)
async def run_reconciliation(
    request: ReconciliationRunRequest,
) -> ReconciliationRunResponse:
    """Reconcile internal ledger rows against provider settlement records using Decimal math."""
    internal_by_ref: dict[str, ReconciliationRowInput] = {}
    discrepancies: list[ReconciliationDiscrepancy] = []
    seen_provider: dict[str, int] = {}
    matched = 0
    total_exposure = Decimal("0")

    for rec in request.internal_records:
        if rec.reference in internal_by_ref:
            discrepancies.append(
                ReconciliationDiscrepancy(
                    discrepancy_type="duplicate_internal",
                    reference=rec.reference,
                    expected="1 internal record",
                    actual="duplicate internal reference",
                    exposure=str(abs(rec.amount)),
                )
            )
            total_exposure += abs(rec.amount)
        else:
            internal_by_ref[rec.reference] = rec

    for prec in request.provider_records:
        ref = prec.reference
        seen_provider[ref] = seen_provider.get(ref, 0) + 1
        if seen_provider[ref] > 1:
            discrepancies.append(
                ReconciliationDiscrepancy(
                    discrepancy_type="duplicate_provider",
                    reference=ref,
                    expected="1 provider record",
                    actual=f"{seen_provider[ref]} provider records",
                    exposure=str(abs(prec.amount)),
                )
            )
            total_exposure += abs(prec.amount)
            continue

        irec = internal_by_ref.get(ref)
        if irec is None:
            discrepancies.append(
                ReconciliationDiscrepancy(
                    discrepancy_type="missing_internal",
                    reference=ref,
                    expected="internal record present",
                    actual="missing internally",
                    exposure=str(abs(prec.amount)),
                )
            )
            total_exposure += abs(prec.amount)
            continue

        has_issue = False
        if irec.amount != prec.amount or irec.currency.upper() != prec.currency.upper():
            diff = abs(irec.amount - prec.amount)
            discrepancies.append(
                ReconciliationDiscrepancy(
                    discrepancy_type="amount_mismatch",
                    reference=ref,
                    expected=f"{irec.amount} {irec.currency.upper()}",
                    actual=f"{prec.amount} {prec.currency.upper()}",
                    exposure=str(diff),
                )
            )
            total_exposure += diff
            has_issue = True

        if irec.status.lower() != prec.status.lower():
            discrepancies.append(
                ReconciliationDiscrepancy(
                    discrepancy_type="status_mismatch",
                    reference=ref,
                    expected=irec.status,
                    actual=prec.status,
                    exposure="0",
                )
            )
            has_issue = True

        if not has_issue:
            matched += 1

    for ref, irec in internal_by_ref.items():
        if ref not in seen_provider:
            discrepancies.append(
                ReconciliationDiscrepancy(
                    discrepancy_type="missing_provider",
                    reference=ref,
                    expected="provider record present",
                    actual="missing in provider feed",
                    exposure=str(abs(irec.amount)),
                )
            )
            total_exposure += abs(irec.amount)

    return ReconciliationRunResponse(
        reconciliation_id=uuid4(),
        matched_count=matched,
        discrepancy_count=len(discrepancies),
        total_exposure=str(total_exposure),
        discrepancies=discrepancies,
    )


@router.get("/proofs/{proof_id}/report")
async def export_proof_report(
    proof_id: UUID,
    format: str = Query(default="json", pattern="^(json|csv|markdown)$"),
    service: FinancialProofApplicationService = Depends(  # noqa: B008
        get_financial_proof_service
    ),
):
    """Export a persisted Financial Proof report in JSON, CSV, or Markdown format."""
    aggregate = service.get_proof_aggregate(proof_id)
    if aggregate is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Financial proof {proof_id} was not found.",
        )

    proof = aggregate.proof
    generated_at = datetime.now(UTC).isoformat()

    if format == "csv":
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(["proof_id", "subject", "status", "overall_confidence", "generated_at"])
        writer.writerow([
            str(proof.id),
            proof.subject,
            proof.status.value,
            str(proof.overall_confidence.value),
            generated_at,
        ])
        writer.writerow([])
        writer.writerow([
            "claim_id",
            "claim_type",
            "subject",
            "amount",
            "currency",
            "status",
            "confidence",
        ])
        for c in aggregate.claims:
            writer.writerow([
                str(c.id),
                c.claim_type.value,
                c.subject,
                str(c.amount.amount) if c.amount else "",
                c.amount.currency if c.amount else "",
                c.verification_status.value,
                str(c.confidence.value),
            ])
        return PlainTextResponse(
            content=buf.getvalue(),
            media_type="text/csv",
            headers={
                "Content-Disposition": f'attachment; filename="proof-{str(proof.id)[:8]}.csv"'
            },
        )

    if format == "markdown":
        lines = [
            f"# Financial Proof Report — {proof.subject}",
            f"- **Proof ID**: `{proof.id}`",
            f"- **Status**: `{proof.status.value.upper()}`",
            f"- **Overall Confidence**: `{proof.overall_confidence.value}`",
            f"- **Generated At (UTC)**: `{generated_at}`",
            "",
            "## Claims",
        ]
        for c in aggregate.claims:
            amt = f"{c.amount.amount} {c.amount.currency}" if c.amount else "N/A"
            lines.append(
                f"- `{c.claim_type.value}` | {c.subject} | {amt} | "
                f"**{c.verification_status.value}** (conf {c.confidence.value})"
            )
        lines.append("")
        lines.append("## Evidence")
        for ev in aggregate.evidence:
            lines.append(
                f"- `{ev.source_name}` ({ev.evidence_type.value}) "
                f"checksum=`{ev.checksum}` status=`{ev.status.value}`"
            )
        return PlainTextResponse(content="\n".join(lines), media_type="text/markdown")

    return {
        "report_version": "1.0",
        "generated_at": generated_at,
        "proof": {
            "id": str(proof.id),
            "subject": proof.subject,
            "status": proof.status.value,
            "overall_confidence": str(proof.overall_confidence.value),
            "evaluation_reasons": list(proof.evaluation_reasons),
        },
        "claims": [
            {
                "id": str(c.id),
                "claim_type": c.claim_type.value,
                "subject": c.subject,
                "amount": str(c.amount.amount) if c.amount else None,
                "currency": c.amount.currency if c.amount else None,
                "verification_status": c.verification_status.value,
                "confidence": str(c.confidence.value),
            }
            for c in aggregate.claims
        ],
        "evidence": [
            {
                "id": str(ev.id),
                "evidence_type": ev.evidence_type.value,
                "source_name": ev.source_name,
                "checksum": ev.checksum,
                "status": ev.status.value,
                "source_reference": ev.source_reference,
            }
            for ev in aggregate.evidence
        ],
        "links": [
            {
                "id": str(lk.id),
                "claim_id": str(lk.claim_id),
                "evidence_id": str(lk.evidence_id),
                "verification_status": lk.verification_status.value,
                "confidence": str(lk.confidence.value),
                "explanation": lk.explanation,
            }
            for lk in aggregate.evidence_links
        ],
    }
