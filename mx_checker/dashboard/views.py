
from django.shortcuts import render
from django.utils import timezone
from .models import Domain


def build_domain_result(domain, expected_mx, actual_mx):
    # An MX record matches only if both priority and exchange match.
    # Sets handle DNS ordering differences and duplicate records.
    expected = {
        (mx["priority"], mx["exchange"].rstrip(".").lower())
        for mx in expected_mx
    }
    actual = {
        (mx["priority"], mx["exchange"].rstrip(".").lower())
        for mx in actual_mx
    }

    matched = expected & actual
    expected_count = len(expected)

    progress = (
        round(len(matched) / expected_count * 100)
        if expected_count else 0
    )

    if not expected:
        status = "empty"
    elif matched == expected:
        status = "correct"
    elif matched:
        status = "partial"
    else:
        status = "mismatch"

    return {
        "domain": domain,
        "expected_mx": expected_mx,
        "actual_mx": actual_mx,
        "expected_count": expected_count,
        "matched_count": len(matched),
        "progress": progress,
        "status": status,
        "progress_color": (
            "green" if status == "correct"
            else "amber" if status == "partial"
            else "red"
        ),
    }


def get_dashboard_data():
    # Replace these examples with your database and DNS resolver.
    '''
    domains = [
        {
            "domain": "example.com",
            "expected_mx": [
                {"priority": 10, "exchange": "mx1.example.com"},
                {"priority": 20, "exchange": "mx2.example.com"},
            ],
            "actual_mx": [
                {"priority": 10, "exchange": "mx1.example.com"},
                {"priority": 20, "exchange": "mx2.example.com"},
            ],
        },
        {
            "domain": "example.org",
            "expected_mx": [
                {"priority": 10, "exchange": "mx1.example.org"},
                {"priority": 20, "exchange": "mx2.example.org"},
            ],
            "actual_mx": [
                {"priority": 10, "exchange": "mx1.example.org"},
            ],
        },
    ]
    '''

    domains = Domain.objects.all()

    results = [
        build_domain_result(
            d["domain_name"], #d["expected_mx"], d["actual_mx"]
        )
        for d in domains
    ]

    total = len(results)
    correct = sum(r["status"] == "correct" for r in results)
    partial = sum(r["status"] == "partial" for r in results)
    mismatch = sum(r["status"] == "mismatch" for r in results)

    expected_total = sum(r["expected_count"] for r in results)
    matched_total = sum(r["matched_count"] for r in results)

    return {
        "domain_results": results,
        "total_domains": total,
        "correct_domains": correct,
        "partial_domains": partial,
        "mismatch_domains": mismatch,
        "overall_progress": (
            round(matched_total / expected_total * 100)
            if expected_total else 0
        ),
        "last_updated": timezone.now(),
    }


def mx_dashboard(request):
    context = get_dashboard_data()
    return render(request, "dashboard/mx_dashboard.html", context)


def mx_dashboard_data(request):
    context = get_dashboard_data()

    # Return only the content that HTMX replaces.
    return render(
        request,
        "dashboard/partials/mx_dashboard_content.html",
        context,
    )
