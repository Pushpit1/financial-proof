"""Razorpay webhook API routes."""

import json
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status

from app.api.dependencies import get_razorpay_webhook_service
from app.application.dto.razorpay_webhook import (
    RazorpayWebhookVerificationRequest,
)
from app.application.services.razorpay_webhook import RazorpayWebhookService
from app.infrastructure.razorpay_adapter import RazorpayProviderError

router = APIRouter(
    prefix="/webhooks",
    tags=["webhooks"],
)


@router.post(
    "/razorpay",
    status_code=status.HTTP_200_OK,
)
async def verify_razorpay_webhook(
    request: Request,
    signature: Annotated[
        str | None,
        Header(alias="X-Razorpay-Signature"),
    ] = None,
    service: RazorpayWebhookService = Depends(  # noqa: B008
        get_razorpay_webhook_service
    ),
) -> dict[str, bool]:
    """Verify a Razorpay webhook and reject replayed events."""
    payload = await request.body()

    if signature is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="X-Razorpay-Signature header is required.",
        )

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Webhook payload cannot be empty.",
        )

    try:
        parsed_payload = json.loads(payload)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Webhook payload must contain valid JSON.",
        ) from exc

    event_id = parsed_payload.get("id")

    if not isinstance(event_id, str) or not event_id.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Webhook event ID is required.",
        )

    try:
        result = service.verify(
            RazorpayWebhookVerificationRequest(
                payload=payload,
                signature=signature,
                event_id=event_id,
            )
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except RazorpayProviderError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc

    if result.replayed:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Webhook event has already been processed.",
        )

    if not result.valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid Razorpay webhook signature.",
        )

    return {"valid": True}

