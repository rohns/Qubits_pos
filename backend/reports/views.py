from collections import defaultdict
from datetime import date as date_cls

from django.db.models import Sum, Count
from django.db.models.functions import TruncDate, TruncMonth
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from sales.models import Sale, SaleItem
from payments.models import Payment
from expenses.models import Expense

CURRENCY = "KES"


def money(value):
    return round(float(value or 0), 2)


def pct(part, whole):
    """Percentage of `whole` that `part` represents, rounded to 1 decimal place."""
    whole = float(whole or 0)
    if whole == 0:
        return 0.0
    return round(float(part or 0) / whole * 100, 1)


def format_kes(value):
    """e.g. 45320.5 -> 'KES 45,320.50' — for display fields alongside the raw number."""
    return f"{CURRENCY} {float(value or 0):,.2f}"


def date_filter(qs, request, field="created_at__date"):
    from_date = request.query_params.get("from_date")
    to_date = request.query_params.get("to_date")
    if from_date:
        qs = qs.filter(**{f"{field}__gte": from_date})
    if to_date:
        qs = qs.filter(**{f"{field}__lte": to_date})
    return qs


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def daily_sales(request):
    qs = date_filter(Sale.objects.filter(status="PAID"), request)
    data = (
        qs.annotate(day=TruncDate("created_at"))
        .values("day")
        .annotate(total_sales=Sum("total_amount"), transactions=Count("id"))
        .order_by("day")
    )
    return Response({
        "currency": CURRENCY,
        "results": [
            {
                "date": str(i["day"]),
                "total_sales": money(i["total_sales"]),
                "total_sales_display": format_kes(i["total_sales"]),
                "transactions": i["transactions"],
            }
            for i in data
        ],
    })


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def payment_methods(request):
    qs = date_filter(Payment.objects.filter(status="PAID"), request)
    data = list(qs.values("method").annotate(total=Sum("amount"), transactions=Count("id")).order_by("method"))
    grand_total = sum(money(i["total"]) for i in data)

    return Response({
        "currency": CURRENCY,
        "grand_total": grand_total,
        "grand_total_display": format_kes(grand_total),
        "results": [
            {
                "method": i["method"],
                "total": money(i["total"]),
                "total_display": format_kes(i["total"]),
                "transactions": i["transactions"],
                "percentage": pct(i["total"], grand_total),
            }
            for i in data
        ],
    })


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def top_services(request):
    qs = date_filter(SaleItem.objects.filter(sale__status="PAID"), request, field="sale__created_at__date")
    data = (
        qs.values("product__name")
        .annotate(quantity_sold=Sum("quantity"), revenue=Sum("line_total"))
        .order_by("-quantity_sold")[:10]
    )
    return Response({
        "currency": CURRENCY,
        "results": [
            {
                "service": i["product__name"],
                "quantity_sold": i["quantity_sold"] or 0,
                "revenue": money(i["revenue"]),
                "revenue_display": format_kes(i["revenue"]),
            }
            for i in data
        ],
    })


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def monthly_sales(request):
    qs = date_filter(Sale.objects.filter(status="PAID"), request)
    data = (
        qs.annotate(month_date=TruncMonth("created_at"))
        .values("month_date")
        .annotate(total_sales=Sum("total_amount"), transactions=Count("id"))
        .order_by("month_date")
    )
    return Response({
        "currency": CURRENCY,
        "results": [
            {
                "month": i["month_date"].strftime("%Y-%m") if i["month_date"] else "",
                "total_sales": money(i["total_sales"]),
                "total_sales_display": format_kes(i["total_sales"]),
                "transactions": i["transactions"],
            }
            for i in data
        ],
    })


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def daily_expenses(request):
    qs = date_filter(Expense.objects.all(), request, field="date")
    data = (
        qs.values("date")
        .annotate(total_expenses=Sum("amount"), transactions=Count("id"))
        .order_by("date")
    )
    return Response({
        "currency": CURRENCY,
        "results": [
            {
                "date": str(i["date"]),
                "total_expenses": money(i["total_expenses"]),
                "total_expenses_display": format_kes(i["total_expenses"]),
                "transactions": i["transactions"],
            }
            for i in data
        ],
    })


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def profit_summary(request):
    sales_qs = date_filter(Sale.objects.filter(status="PAID"), request)
    expenses_qs = date_filter(Expense.objects.all(), request, field="date")

    sales = sales_qs.annotate(day=TruncDate("created_at")).values("day").annotate(revenue=Sum("total_amount"))
    expenses = expenses_qs.values("date").annotate(expenses=Sum("amount"))

    summary = defaultdict(lambda: {"revenue": 0, "expenses": 0})
    for i in sales:
        summary[str(i["day"])]["revenue"] = money(i["revenue"])
    for i in expenses:
        summary[str(i["date"])]["expenses"] = money(i["expenses"])

    return Response({
        "currency": CURRENCY,
        "results": [
            {
                "date": d,
                "revenue": v["revenue"],
                "expenses": v["expenses"],
                "profit": round(v["revenue"] - v["expenses"], 2),
                "revenue_display": format_kes(v["revenue"]),
                "expenses_display": format_kes(v["expenses"]),
                "profit_display": format_kes(v["revenue"] - v["expenses"]),
            }
            for d, v in sorted(summary.items())
        ],
    })


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def eod_summary(request):
    target_date = request.query_params.get("date", str(date_cls.today()))

    sales_qs = Sale.objects.filter(status="PAID", created_at__date=target_date)
    agg = sales_qs.aggregate(total=Sum("total_amount"), count=Count("id"))

    cash_agg = Payment.objects.filter(status="PAID", method="CASH", created_at__date=target_date).aggregate(t=Sum("amount"))
    mpesa_agg = Payment.objects.filter(status="PAID", method="MPESA", created_at__date=target_date).aggregate(t=Sum("amount"))

    top = (
        SaleItem.objects.filter(sale__status="PAID", sale__created_at__date=target_date)
        .values("product__name")
        .annotate(qty=Sum("quantity"), rev=Sum("line_total"))
        .order_by("-qty")[:5]
    )

    # Every transaction for the day — largest amount first — so a manager can
    # scan the full day's activity, not just the top services.
    day_sales = (
        sales_qs
        .select_related("cashier")
        .prefetch_related("items__product")
        .order_by("-total_amount", "-created_at")
    )
    transactions = [
        {
            "receipt_number": sale.receipt_number,
            "time": sale.created_at.strftime("%H:%M"),
            "cashier": sale.cashier.username if sale.cashier else None,
            "payment_method": sale.payment_method,
            "amount": money(sale.total_amount),
            "amount_display": format_kes(sale.total_amount),
            "items": [
                {"service": item.product.name, "quantity": item.quantity}
                for item in sale.items.all()
            ],
        }
        for sale in day_sales
    ]

    exp_agg = Expense.objects.filter(date=target_date).aggregate(t=Sum("amount"), c=Count("id"))

    # Snapshot of the tab/credit ledger as of now (not date-scoped — this is
    # "how much is currently owed to you", useful to see alongside the day's
    # cash numbers even though it isn't part of today's revenue).
    credit_agg = Sale.objects.filter(payment_method="CREDIT", status="PENDING").aggregate(t=Sum("total_amount"), c=Count("id"))
    outstanding_credit = money(credit_agg["t"])

    cash_total = money(cash_agg["t"])
    mpesa_total = money(mpesa_agg["t"])
    collected_total = cash_total + mpesa_total
    total_revenue = money(agg["total"])
    total_expenses = money(exp_agg["t"])
    net_profit = round(total_revenue - total_expenses, 2)

    return Response({
        "date": target_date,
        "currency": CURRENCY,

        "total_revenue": total_revenue,
        "total_revenue_display": format_kes(total_revenue),
        "total_transactions": agg["count"] or 0,

        "cash_collected": cash_total,
        "cash_collected_display": format_kes(cash_total),
        "cash_percentage": pct(cash_total, collected_total),

        "mpesa_collected": mpesa_total,
        "mpesa_collected_display": format_kes(mpesa_total),
        "mpesa_percentage": pct(mpesa_total, collected_total),

        "total_expenses": total_expenses,
        "total_expenses_display": format_kes(total_expenses),

        "net_profit": net_profit,
        "net_profit_display": format_kes(net_profit),

        "outstanding_credit": outstanding_credit,
        "outstanding_credit_display": format_kes(outstanding_credit),
        "outstanding_credit_count": credit_agg["c"] or 0,

        "top_services": [
            {
                "service": i["product__name"],
                "quantity": i["qty"] or 0,
                "revenue": money(i["rev"]),
                "revenue_display": format_kes(i["rev"]),
            }
            for i in top
        ],

        "transactions": transactions,
    })
