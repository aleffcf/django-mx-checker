
from django.db import models


class Domain(models.Model):
    domain_name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.domain_name


class ExpectedMX(models.Model):
    domain = models.ForeignKey(
        Domain,
        on_delete=models.CASCADE,
        related_name="expected_mx_records",
    )
    exchange = models.CharField(max_length=255)
    priority = models.PositiveIntegerField()

    class Meta:
        ordering = ["priority", "exchange"]
        constraints = [
            models.UniqueConstraint(
                fields=["domain", "exchange", "priority"],
                name="unique_expected_mx_per_domain",
            )
        ]

    def __str__(self):
        return f"{self.domain.domain_name} - {self.priority} {self.exchange}"


class MXCheck(models.Model):
    STATUS_CHOICES = [
        ("success", "Success"),
        ("no_mx", "No MX records"),
        ("nxdomain", "Domain does not exist"),
        ("error", "DNS query error"),
    ]

    COMPARISON_STATUS_CHOICES = [
        ("ok", "Configuration matches"),
        ("mismatch", "MX configuration differs"),
        ("not_checked", "Not checked"),
    ]

    comparison_status = models.CharField(
        max_length=20,
        choices=COMPARISON_STATUS_CHOICES,
        default="not_checked",
    )

    domain = models.ForeignKey(
        Domain,
        on_delete=models.CASCADE,
        related_name="checks",
    )
    checked_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    error_message = models.TextField(blank=True)

    class Meta:
        ordering = ["-checked_at"]
        indexes = [
            models.Index(fields=["domain", "-checked_at"]),
        ]

    def __str__(self):
        return f"{self.domain.domain_name} - {self.checked_at}"


class Record(models.Model):
    domain = models.ForeignKey(
        Domain,
        on_delete=models.CASCADE,
        related_name="records",
    )
    mx_check = models.ForeignKey(
        MXCheck,
        on_delete=models.CASCADE,
        related_name="records",
    )
    mx_entry = models.CharField(max_length=255)
    priority = models.PositiveIntegerField(default=0)

    def __str__(self):
        return (
            f"{self.domain.domain_name} - "
            f"{self.priority} {self.mx_entry}"
        )
