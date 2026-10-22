
import dns.exception
import dns.resolver

from django.core.management.base import BaseCommand
from django.db import transaction

from dashboard.models import Domain, ExpectedMX, MXCheck, Record


class Command(BaseCommand):
    help = "Checks MX records and compares them with expected configuration."

    def handle(self, *args, **options):
        domains = Domain.objects.all().order_by("id")
        total = domains.count()

        self.stdout.write(
            self.style.NOTICE(
                f"Starting MX checks for {total} domains..."
            )
        )

        for index, domain in enumerate(domains.iterator(), start=1):
            result = self.lookup_mx(domain.domain_name)

            expected_records = set(
                ExpectedMX.objects.filter(domain=domain).values_list(
                    "priority", "exchange"
                )
            )

            found_records = {
                (record["priority"], record["exchange"])
                for record in result["records"]
            }

            if result["status"] != "success" or not expected_records:
                comparison_status = "not_checked"
            elif expected_records == found_records:
                comparison_status = "ok"
            else:
                comparison_status = "mismatch"

            with transaction.atomic():
                check = MXCheck.objects.create(
                    domain=domain,
                    status=result["status"],
                    error_message=result["error"],
                    comparison_status=comparison_status,
                )

                records = [
                    Record(
                        domain=domain,
                        mx_check=check,
                        mx_entry=mx["exchange"],
                        priority=mx["priority"],
                    )
                    for mx in result["records"]
                ]

                if records:
                    Record.objects.bulk_create(records)

            message = (
                f"[{index}/{total}] {domain.domain_name}: "
                f"DNS={result['status']}, "
                f"comparison={comparison_status}, "
                f"{len(result['records'])} MX records"
            )

            if comparison_status == "mismatch":
                missing = expected_records - found_records
                unexpected = found_records - expected_records

                if missing:
                    message += f", missing={sorted(missing)}"
                if unexpected:
                    message += f", unexpected={sorted(unexpected)}"

                self.stdout.write(self.style.WARNING(message))
            elif comparison_status == "ok":
                self.stdout.write(self.style.SUCCESS(message))
            else:
                self.stdout.write(message)

        self.stdout.write(
            self.style.SUCCESS("MX checks completed.")
        )

    def lookup_mx(self, domain_name):
        resolver = dns.resolver.Resolver()
        resolver.timeout = 3
        resolver.lifetime = 5

        try:
            answers = resolver.resolve(
                domain_name,
                "MX",
                raise_on_no_answer=False,
            )

            if answers.rrset is None:
                return {
                    "status": "no_mx",
                    "records": [],
                    "error": "",
                }

            records = [
                {
                    "priority": answer.preference,
                    "exchange": str(answer.exchange).rstrip(".").lower(),
                }
                for answer in answers
            ]

            return {
                "status": "success",
                "records": records,
                "error": "",
            }

        except dns.resolver.NXDOMAIN:
            return {
                "status": "nxdomain",
                "records": [],
                "error": "Domain does not exist (NXDOMAIN).",
            }

        except dns.resolver.NoAnswer:
            return {
                "status": "no_mx",
                "records": [],
                "error": "DNS response contains no MX answer.",
            }

        except dns.exception.DNSException as exc:
            return {
                "status": "error",
                "records": [],
                "error": str(exc),
            }
