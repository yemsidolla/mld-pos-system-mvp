from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from inventory.models import StockBatch
from inventory.services import mark_batch_expired


class Command(BaseCommand):
    help = "Mark expired active stock batches as expired using the normal inventory movement and audit workflow."

    def add_arguments(self, parser):
        parser.add_argument("--username", required=True, help="Existing user recorded as the maintenance actor.")
        parser.add_argument("--dry-run", action="store_true", help="Show the number of affected batches without changing stock.")

    def handle(self, *args, **options):
        user = get_user_model().objects.filter(username=options["username"], is_active=True).first()
        if user is None:
            raise CommandError("Active maintenance user does not exist.")

        today = timezone.localdate()
        batches = (
            StockBatch.objects.select_related("product")
            .filter(
                status=StockBatch.Status.ACTIVE,
                quantity_available__gt=0,
                expiry_date__lt=today,
            )
            .order_by("expiry_date", "batch_no")
        )
        count = batches.count()

        if options["dry_run"]:
            self.stdout.write(f"{count} expired active batch(es) would be marked expired.")
            return

        reason = f"Expired batch maintenance run on {today.isoformat()}."
        for batch in batches:
            mark_batch_expired(stock_batch=batch, reason=reason, marked_by=user)

        self.stdout.write(self.style.SUCCESS(f"Marked {count} expired batch(es)."))
