import base64
import datetime
import re
from decimal import Decimal, InvalidOperation

import requests
from django.conf import settings
from django.core.cache import cache
from django.db import transaction
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response

from sales.models import Sale
from .models import Payment

MPESA_TOKEN_CACHE_KEY = "mpesa_access_token"


def normalize_mpesa_phone(phone):
    """Return Safaricom STK format, for example 2547XXXXXXXX."""
    value = re.sub(r"\D", "", str(phone or ""))
    if value.startswith("0") and len(value) == 10:
        value = "254" + value[1:]
    elif value.startswith("7") and len(value) == 9:
        value = "254" + value
    elif value.startswith("1") and len(value) == 9:
        value = "254" + value
    if not re.fullmatch(r"254[17]\d{8}", value):
        return None
    return value


def get_mpesa_access_token():
    """
    Daraja OAuth tokens are valid for ~3600 seconds. Fetching a new one on every
    STK push adds latency and risks hitting Safaricom's rate limits, so cache it
    and only refetch shortly before it would expire.
    """
    cached_token = cache.get(MPESA_TOKEN_CACHE_KEY)
    if cached_token:
        return cached_token

    url = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
    if getattr(settings, "MPESA_ENV", "sandbox") == "production":
        url = "https://api.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"

    response = requests.get(
        url,
        auth=(settings.MPESA_CONSUMER_KEY, settings.MPESA_CONSUMER_SECRET),
        timeout=30,
    )
    response.raise_for_status()
    payload = response.json()
    token = payload["access_token"]
    # expires_in is usually "3599"; refresh a bit early to be safe.
    expires_in = int(payload.get("expires_in", 3599))
    cache.set(MPESA_TOKEN_CACHE_KEY, token, timeout=max(60, expires_in - 120))
    return token


def _metadata_value(callback_metadata, name):
    for item in callback_metadata.get("Item", []):
        if item.get("Name") == name:
            return item.get("Value")
    return None


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def cash_payment(request):
    sale_id = request.data.get("sale_id")
    amount_paid = request.data.get("amount_paid")

    if not sale_id or amount_paid in (None, ""):
        return Response({"error": "sale_id and amount_paid are required"}, status=400)

    try:
        amount_paid = Decimal(str(amount_paid))
    except (InvalidOperation, TypeError):
        return Response({"error": "amount_paid must be a valid number"}, status=400)

    try:
        with transaction.atomic():
            sale = Sale.objects.select_for_update().get(id=sale_id)

            if sale.status == "PAID":
                existing = sale.payments.filter(status="PAID").order_by("-created_at").first()
                return Response({
                    "message": "Sale is already paid",
                    "payment_id": existing.id if existing else None,
                    "sale_id": sale.id,
                    "status": "PAID",
                    "amount": str(sale.total_amount),
                    "amount_paid": str(existing.amount_paid if existing else sale.total_amount),
                    "change_due": str(existing.change_due if existing else Decimal("0")),
                }, status=200)

            total = Decimal(str(sale.total_amount))
            if amount_paid < total:
                return Response({"error": "Amount paid is less than sale total"}, status=400)

            payment = Payment.objects.create(
                sale=sale,
                method="CASH",
                status="PAID",
                amount=total,
                amount_paid=amount_paid,
                change_due=amount_paid - total,
            )
            sale.status = "PAID"
            sale.payment_method = "CASH"
            sale.save(update_fields=["status", "payment_method"])
    except Sale.DoesNotExist:
        return Response({"error": "Sale not found"}, status=404)

    return Response({
        "message": "Cash payment recorded",
        "payment_id": payment.id,
        "sale_id": sale.id,
        "status": payment.status,
        "amount": str(total),
        "amount_paid": str(amount_paid),
        "change_due": str(payment.change_due),
    }, status=201)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def mpesa_cash_payment(request):
    """
    Record an M-PESA payment that the cashier confirmed manually (e.g. paid to a
    paybill/till and read out over the counter) rather than through an STK push.
    Since there's no callback from Safaricom for this flow, the confirmation code
    from the customer's SMS is required so there's an audit trail to check against
    later if a payment is ever disputed.
    """
    sale_id = request.data.get("sale_id")
    amount_paid = request.data.get("amount_paid")
    mpesa_reference = (request.data.get("mpesa_reference") or "").strip().upper()

    if not sale_id or amount_paid in (None, ""):
        return Response({"error": "sale_id and amount_paid are required"}, status=400)

    if not mpesa_reference:
        return Response(
            {"error": "mpesa_reference is required — enter the M-PESA confirmation code from the customer's SMS."},
            status=400,
        )

    try:
        amount_paid = Decimal(str(amount_paid))
    except (InvalidOperation, TypeError):
        return Response({"error": "amount_paid must be a valid number"}, status=400)

    try:
        with transaction.atomic():
            sale = Sale.objects.select_for_update().get(id=sale_id)

            if sale.status == "PAID":
                existing = sale.payments.filter(status="PAID").order_by("-created_at").first()
                return Response({
                    "message": "Sale is already paid",
                    "payment_id": existing.id if existing else None,
                    "sale_id": sale.id,
                    "status": "PAID",
                    "amount": str(sale.total_amount),
                    "amount_paid": str(existing.amount_paid if existing else sale.total_amount),
                    "change_due": str(existing.change_due if existing else Decimal("0")),
                }, status=200)

            total = Decimal(str(sale.total_amount))
            if amount_paid < total:
                return Response({"error": "Amount paid is less than sale total"}, status=400)

            payment = Payment.objects.create(
                sale=sale,
                method="MPESA",  # Categorized as M-PESA
                status="PAID",
                amount=total,
                amount_paid=amount_paid,
                change_due=amount_paid - total,
                mpesa_reference=mpesa_reference,
            )
            sale.status = "PAID"
            sale.payment_method = "MPESA"  # Sale shows as M-PESA
            sale.save(update_fields=["status", "payment_method"])
    except Sale.DoesNotExist:
        return Response({"error": "Sale not found"}, status=404)

    return Response({
        "message": "M-PESA cash payment recorded",
        "payment_id": payment.id,
        "sale_id": sale.id,
        "status": payment.status,
        "amount": str(total),
        "amount_paid": str(amount_paid),
        "change_due": str(payment.change_due),
        "mpesa_reference": payment.mpesa_reference,
    }, status=201)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def stk_push(request):
    sale_id = request.data.get("sale_id")
    phone = normalize_mpesa_phone(request.data.get("phone"))

    if not sale_id or not phone:
        return Response({"error": "A valid sale_id and Safaricom phone number are required. Use 07XXXXXXXX or 2547XXXXXXXX."}, status=400)

    try:
        sale = Sale.objects.get(id=sale_id)
    except Sale.DoesNotExist:
        return Response({"error": "Sale not found"}, status=404)

    required = [settings.MPESA_CONSUMER_KEY, settings.MPESA_CONSUMER_SECRET, settings.MPESA_PASSKEY, settings.MPESA_SHORTCODE, settings.MPESA_CALLBACK_URL]
    if not all(required):
        return Response({"error": "M-PESA credentials are not fully configured in Railway variables."}, status=400)

    try:
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        password = base64.b64encode((settings.MPESA_SHORTCODE + settings.MPESA_PASSKEY + timestamp).encode()).decode()
        token = get_mpesa_access_token()
        url = "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest"
        if getattr(settings, "MPESA_ENV", "sandbox") == "production":
            url = "https://api.safaricom.co.ke/mpesa/stkpush/v1/processrequest"

        payload = {
            "BusinessShortCode": settings.MPESA_SHORTCODE,
            "Password": password,
            "Timestamp": timestamp,
            "TransactionType": "CustomerPayBillOnline",
            "Amount": int(Decimal(str(sale.total_amount))),
            "PartyA": phone,
            "PartyB": settings.MPESA_SHORTCODE,
            "PhoneNumber": phone,
            "CallBackURL": settings.MPESA_CALLBACK_URL,
            "AccountReference": f"QubitsSale{sale.id}",
            "TransactionDesc": "Qubits Cyber Services POS payment",
        }

        res = requests.post(url, json=payload, headers={"Authorization": f"Bearer {token}"}, timeout=30)
        try:
            data = res.json()
        except ValueError:
            return Response({"error": "Safaricom returned a non-JSON response", "details": res.text[:300]}, status=502)

        if res.status_code >= 400 or data.get("ResponseCode") not in ("0", 0, None):
            return Response({"error": "M-PESA STK Push was rejected", "mpesa_response": data}, status=400)

        payment = Payment.objects.create(
            sale=sale,
            method="MPESA",
            status="PENDING",
            amount=sale.total_amount,
            phone_number=phone,
            checkout_request_id=data.get("CheckoutRequestID"),
            merchant_request_id=data.get("MerchantRequestID"),
        )
        sale.payment_method = "MPESA"
        sale.customer_phone = phone
        sale.status = "PENDING"
        sale.save(update_fields=["payment_method", "customer_phone", "status"])
    except requests.RequestException as exc:
        return Response({"error": "Could not connect to Safaricom M-PESA API", "details": str(exc)}, status=502)

    return Response({
        "message": "STK Push initiated",
        "payment_id": payment.id,
        "sale_id": sale.id,
        "checkout_request_id": payment.checkout_request_id,
        "merchant_request_id": payment.merchant_request_id,
        "status": payment.status,
        "mpesa_response": data,
    })


@api_view(["POST"])
@permission_classes([AllowAny])
def mpesa_callback(request):
    body = request.data.get("Body", {})
    stk = body.get("stkCallback", {})
    checkout_id = stk.get("CheckoutRequestID")
    result_code = str(stk.get("ResultCode"))
    result_desc = stk.get("ResultDesc")

    if not checkout_id:
        return Response({"message": "CheckoutRequestID missing"}, status=400)

    try:
        payment = Payment.objects.select_related("sale").get(checkout_request_id=checkout_id)
    except Payment.DoesNotExist:
        return Response({"message": "Payment not found"}, status=404)

    payment.result_code = result_code
    payment.result_description = result_desc
    payment.raw_callback = request.data

    if result_code == "0":
        metadata = stk.get("CallbackMetadata", {})
        amount = _metadata_value(metadata, "Amount")
        receipt = _metadata_value(metadata, "MpesaReceiptNumber")
        transaction_date = _metadata_value(metadata, "TransactionDate")
        phone = _metadata_value(metadata, "PhoneNumber")

        payment.status = "PAID"
        payment.amount_paid = Decimal(str(amount)) if amount is not None else payment.amount
        payment.change_due = Decimal("0")
        payment.mpesa_receipt_number = receipt
        payment.mpesa_transaction_date = str(transaction_date) if transaction_date else None
        if phone:
            payment.phone_number = str(phone)

        payment.sale.status = "PAID"
        payment.sale.payment_method = "MPESA"
        if phone:
            payment.sale.customer_phone = str(phone)
        payment.sale.save(update_fields=["status", "payment_method", "customer_phone"])
    else:
        payment.status = "FAILED"
        payment.sale.status = "FAILED"
        payment.sale.save(update_fields=["status"])

    payment.save()
    return Response({"message": "Callback processed"})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def payment_status(request, checkout_request_id):
    try:
        payment = Payment.objects.select_related("sale").get(checkout_request_id=checkout_request_id)
    except Payment.DoesNotExist:
        return Response({"error": "Payment not found"}, status=404)

    return Response({
        "payment_id": payment.id,
        "sale_id": payment.sale_id,
        "sale_status": payment.sale.status,
        "method": payment.method,
        "status": payment.status,
        "amount": str(payment.amount),
        "amount_paid": str(payment.amount_paid),
        "phone_number": payment.phone_number,
        "checkout_request_id": payment.checkout_request_id,
        "merchant_request_id": payment.merchant_request_id,
        "mpesa_receipt_number": payment.mpesa_receipt_number,
        "mpesa_reference": payment.mpesa_reference,
        "result_code": payment.result_code,
        "result_description": payment.result_description,
        "mpesa_transaction_date": payment.mpesa_transaction_date,
        "updated_at": payment.updated_at,
    })
