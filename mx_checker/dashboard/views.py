
from django.shortcuts import render
from django.utils import timezone
from .models import Domain, MXCheck, Record, ExpectedMX
from django.db.models import OuterRef, Subquery, Prefetch

def dashboard_view(request):
    latest_check = MXCheck.objects.filter(
        domain_id=OuterRef("pk")
    ).order_by("-checked_at", "-pk")

    latest_check_id = Subquery(latest_check.values("id")[:1])

    domains = (
        Domain.objects
        .annotate(
            last_check_id=latest_check_id,
            last_check_status=Subquery(
                latest_check.values("status")[:1]
            ),
            last_comparison_status=Subquery(
                latest_check.values("comparison_status")[:1]
            ),
            last_checked_at=Subquery(
                latest_check.values("checked_at")[:1]
            ),
        )
        .prefetch_related(
            Prefetch(
                "expected_mx_records",
                queryset=ExpectedMX.objects.order_by(
                    "priority", "exchange"
                ),
                to_attr="expected_mx_list",
            ),
            Prefetch(
                "checks",
                queryset=MXCheck.objects.filter(
                    pk__in=Subquery(
                        MXCheck.objects.filter(
                            domain_id=OuterRef("domain_id")
                        )
                        .order_by("-checked_at", "-pk")
                        .values("pk")[:1]
                    )
                ).prefetch_related(
                    Prefetch(
                        "records",
                        queryset=Record.objects.order_by(
                            "priority", "mx_entry"
                        ),
                        to_attr="mx_record_list",
                    )
                ),
                to_attr="latest_checks",
            ),
        )
        .order_by("domain_name")
    )

    total = domains.count()
    migrated = pending = failures = unchecked = 0

    for domain in domains:
        domain.latest_check = (
            domain.latest_checks[0] if domain.latest_checks else None
        )

        if domain.latest_check is None:
            unchecked += 1
        elif domain.last_check_status != "success":
            failures += 1
        elif domain.last_comparison_status == "ok":
            migrated += 1
        elif domain.last_comparison_status == "mismatch":
            pending += 1
        else:
            unchecked += 1

    evaluated = migrated + pending
    progress = round(migrated / evaluated * 100, 1) if evaluated else 0

    return render(
        request,
        "dashboard/dashboard.html",
        {
            "domains": domains,
            "total": total,
            "migrated": migrated,
            "pending": pending,
            "failures": failures,
            "unchecked": unchecked,
            "progress": progress,
        },
    )
