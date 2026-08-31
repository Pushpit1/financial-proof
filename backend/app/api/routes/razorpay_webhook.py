"""Razorpay webhook API routes."""

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
    """Verify a Razorpay webhook signature."""
    payload = await request.body()

    if signature is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="X-Razorpay-Signature header is required.",
        )

    try:
        result = service.verify(
            RazorpayWebhookVerificationRequest(
                payload=payload,
                signature=signature,
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

    if not result.valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid Razorpay webhook signature.",
        )

    return {"valid": True}
