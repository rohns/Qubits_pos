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


def money(value):
    return float(value or 0)


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
    return Response([
        {"date": str(i["day"]), "total_sales": money(i["total_sales"]), "transactions": i["transactions"]}
        for i in data
    ])


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def payment_methods(request):
    qs = date_filter(Payment.objects.filter(status="PAID"), request)
    data = qs.values("method").annotate(total=Sum("amount"), transactions=Count("id")).order_by("method")
    return Response([
        {"method": i["method"], "total": money(i["total"]), "transactions": i["transactions"]}
        for i in data
    ])


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def top_services(request):
    qs = date_filter(SaleItem.objects.filter(sale__status="PAID"), request, field="sale__created_at__date")
    data = (
        qs.values("product__name")
        .annotate(quantity_sold=Sum("quantity"), revenue=Sum("line_total"))
        .order_by("-quantity_sold")[:10]
    )
    return Response([
        {"service": i["product__name"], "quantity_sold": i["quantity_sold"] or 0, "revenue": money(i["revenue"])}
        for i in data
    ])


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
    return Response([
        {"month": i["month_date"].strftime("%Y-%m") if i["month_date"] else "", "total_sales": money(i["total_sales"]), "transactions": i["transactions"]}
        for i in data
    ])


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def daily_expenses(request):
    qs = date_filter(Expense.objects.all(), request, field="date")
    data = (
        qs.values("date")
        .annotate(total_expenses=Sum("amount"), transactions=Count("id"))
        .order_by("date")
    )
    return Response([
        {"date": str(i["date"]), "total_expenses": money(i["total_expenses"]), "transactions": i["transactions"]}
        for i in data
    ])


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def profit_summary(request):
    sales_qs = date_filter(Sale.objects.filter(status="PAID"), request)
    expenses_qs = date_filter(Expense.objects.all(), request, field="date")

    sales = sales_qs.annotate(day=TruncDate("created_at")).values("day").annotate(revenue=Sum("total_amount"))
    expenses = expenses_qs.values("date").annotate(expenses=Sum("amount"))

    summary = defaultdict(lambda: {"revenue": 0, "expenses": 0})
    for i in sales:
        summary[str(i["day"])] ["revenue"] = money(i["revenue"])
    for i in expenses:
        summary[str(i["date"])] ["expenses"] = money(i["expenses"])

    return Response([
        {"date": d, "revenue": v["revenue"], "expenses": v["expenses"], "profit": v["revenue"] - v["expenses"]}
        for d, v in sorted(summary.items())
    ])


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

    exp_agg = Expense.objects.filter(date=target_date).aggregate(t=Sum("amount"), c=Count("id"))

    return Response({
        "date": target_date,
        "total_revenue": money(agg["total"]),
        "total_transactions": agg["count"] or 0,
        "cash_collected": money(cash_agg["t"]),
        "mpesa_collected": money(mpesa_agg["t"]),
        "total_expenses": money(exp_agg["t"]),
        "net_profit": money(agg["total"]) - money(exp_agg["t"]),
        "top_services": [{"service": i["product__name"], "quantity": i["qty"] or 0, "revenue": money(i["rev"])} for i in top],
    })
