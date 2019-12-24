import uuid

from django.db import models


class Invoice(models.Model):
    class Meta:
        ordering = ["-date_created"]

    STATUS = (
        ("pending", "Pending"),
        ("successful", "Successful"),
        ("failed", "Failed"),
    )

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    destination = models.CharField(
        max_length=255,
    )

    amount = models.BigIntegerField()

    label = models.TextField()

    date_created = models.DateTimeField(
        auto_now_add=True,
    )

    status = models.CharField(
        choices=STATUS,
        max_length=32,
    )

    error_reason = models.TextField()

    @property
    def date_broadcast(self):
        if self.tx:
            return self.tx.date_broadcast

    @property
    def tx(self):
        return self.transaction_set.last()


class Transaction(models.Model):
    class Meta:
        ordering = ["-date_broadcast"]

    invoice = models.ForeignKey(
        to=Invoice,
        on_delete=models.PROTECT,
    )

    source = models.CharField(
        max_length=255,
        blank=True,
    )

    destination = models.CharField(
        max_length=255,
    )

    amount = models.BigIntegerField()

    payload = models.TextField()

    date_broadcast = models.DateTimeField(
        blank=True, null=True,
    )

    signed_tx = models.TextField()

    tx_hash = models.CharField(
        max_length=255,
    )
