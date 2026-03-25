"""
Payment service for HandCraft.

Abstracts payment gateway interactions (Stripe-like interface).
In production, replace the stub implementations with real gateway calls.
"""

import logging
import uuid
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from typing import Optional

from django.conf import settings

logger = logging.getLogger(__name__)


class PaymentStatus(Enum):
    PENDING = "pending"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    REFUNDED = "refunded"


@dataclass
class PaymentResult:
    """Immutable result object returned by payment operations."""

    success: bool
    transaction_id: str
    status: PaymentStatus
    amount: Decimal
    currency: str
    error_message: Optional[str] = None


class PaymentService:
    """
    Service for processing payments, refunds, and payouts.

    All public methods return a PaymentResult so callers never need
    to handle gateway-specific exceptions directly.
    """

    CURRENCY = "USD"

    # ── Charge ───────────────────────────────────────────────────

    @classmethod
    def create_charge(
        cls,
        amount: Decimal,
        payment_method_id: str,
        customer_email: str,
        description: str = "",
        metadata: Optional[dict] = None,
    ) -> PaymentResult:
        """
        Charge a payment method.

        Parameters
        ----------
        amount : Decimal
            Amount in dollars (e.g. Decimal('49.99')).
        payment_method_id : str
            Token or ID from the front-end payment form.
        customer_email : str
        description : str
        metadata : dict | None
            Extra key-value pairs to attach to the transaction.
        """
        transaction_id = f"txn_{uuid.uuid4().hex[:16]}"

        try:
            # --- In production, call the real gateway here ---
            # stripe.Charge.create(
            #     amount=int(amount * 100),
            #     currency=cls.CURRENCY,
            #     source=payment_method_id,
            #     description=description,
            #     receipt_email=customer_email,
            #     metadata=metadata or {},
            # )

            logger.info(
                "Payment charged: %s %s %s for %s",
                transaction_id,
                amount,
                cls.CURRENCY,
                customer_email,
            )
            return PaymentResult(
                success=True,
                transaction_id=transaction_id,
                status=PaymentStatus.SUCCEEDED,
                amount=amount,
                currency=cls.CURRENCY,
            )
        except Exception as exc:
            logger.exception("Payment charge failed: %s", str(exc))
            return PaymentResult(
                success=False,
                transaction_id=transaction_id,
                status=PaymentStatus.FAILED,
                amount=amount,
                currency=cls.CURRENCY,
                error_message=str(exc),
            )

    # ── Refund ───────────────────────────────────────────────────

    @classmethod
    def create_refund(
        cls,
        original_transaction_id: str,
        amount: Optional[Decimal] = None,
        reason: str = "",
    ) -> PaymentResult:
        """
        Refund a previous charge (full or partial).

        If *amount* is None the full charge is refunded.
        """
        refund_id = f"ref_{uuid.uuid4().hex[:16]}"

        try:
            refund_amount = amount or Decimal("0.00")
            logger.info(
                "Refund processed: %s for original txn %s (amount=%s, reason=%s)",
                refund_id,
                original_transaction_id,
                refund_amount,
                reason,
            )
            return PaymentResult(
                success=True,
                transaction_id=refund_id,
                status=PaymentStatus.REFUNDED,
                amount=refund_amount,
                currency=cls.CURRENCY,
            )
        except Exception as exc:
            logger.exception("Refund failed: %s", str(exc))
            return PaymentResult(
                success=False,
                transaction_id=refund_id,
                status=PaymentStatus.FAILED,
                amount=amount or Decimal("0.00"),
                currency=cls.CURRENCY,
                error_message=str(exc),
            )

    # ── Payout ───────────────────────────────────────────────────

    @classmethod
    def create_payout(
        cls,
        artisan_id: str,
        amount: Decimal,
        description: str = "Artisan payout",
    ) -> PaymentResult:
        """
        Initiate a payout to an artisan's connected bank account.
        """
        payout_id = f"po_{uuid.uuid4().hex[:16]}"

        try:
            commission_pct = getattr(settings, "ARTISAN_COMMISSION_PERCENT", 10)
            commission = (amount * Decimal(commission_pct)) / Decimal(100)
            net_payout = amount - commission

            logger.info(
                "Payout created: %s to artisan %s (gross=%s, commission=%s, net=%s)",
                payout_id,
                artisan_id,
                amount,
                commission,
                net_payout,
            )
            return PaymentResult(
                success=True,
                transaction_id=payout_id,
                status=PaymentStatus.SUCCEEDED,
                amount=net_payout,
                currency=cls.CURRENCY,
            )
        except Exception as exc:
            logger.exception("Payout failed: %s", str(exc))
            return PaymentResult(
                success=False,
                transaction_id=payout_id,
                status=PaymentStatus.FAILED,
                amount=amount,
                currency=cls.CURRENCY,
                error_message=str(exc),
            )
