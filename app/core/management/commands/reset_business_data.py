import os

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from audit.models import AuditLog
from audit.services import create_audit_log
from batch_upload.models import BatchUploadJob
from catalog.models import Brand, Category, Product, ProductTag, Supplier, SupplierProductCost
from inventory.models import InventoryMovement, StockBatch
from pos.models import Promotion, Sale

ENV_FLAG = "ALLOW_DATA_RESET"
SCOPES = ("sales", "movements", "batches", "demo", "catalog", "all")

# Data that is NEVER deleted by this command, for clarity in the help text and
# the operator-facing summary.
PRESERVED = "users, roles, store settings, label templates, and audit logs"


def build_plan(scope):
    """Return an ordered list of (label, queryset) to delete for a scope.

    Order respects on_delete=PROTECT foreign keys: transactional records are
    removed before the master data they reference.
    """
    sales = ("Sales (and sale items)", Sale.objects.all())
    sale_movements = (
        "Sale/return movements",
        InventoryMovement.objects.filter(
            movement_type__in=[
                InventoryMovement.MovementType.SALE,
                InventoryMovement.MovementType.RETURN,
            ]
        ),
    )
    all_movements = ("Inventory movements", InventoryMovement.objects.all())
    batches = ("Stock batches", StockBatch.objects.all())
    promotions = ("Promotions", Promotion.objects.all())
    costs = ("Supplier product costs", SupplierProductCost.objects.all())
    products = ("Products", Product.objects.all())
    tags = ("Product tags", ProductTag.objects.all())
    categories = ("Categories", Category.objects.all())
    brands = ("Brands", Brand.objects.all())
    suppliers = ("Suppliers", Supplier.objects.all())
    uploads = ("Batch upload jobs", BatchUploadJob.objects.all())

    operational = [sales, all_movements, batches]
    catalog = operational + [promotions, costs, products, tags, categories, brands, suppliers, uploads]

    plans = {
        "sales": [sales, sale_movements],
        "movements": [all_movements],
        "batches": operational,
        "demo": operational,
        "catalog": catalog,
        "all": catalog,
    }
    return plans[scope]


class Command(BaseCommand):
    help = (
        "Safely clear business data (Owner-only operation). Defaults to a dry run. "
        f"Always preserves {PRESERVED}."
    )

    def add_arguments(self, parser):
        parser.add_argument("--scope", required=True, choices=SCOPES)
        parser.add_argument("--dry-run", action="store_true", help="Show counts and delete nothing.")
        parser.add_argument("--confirm", action="store_true", help="Actually delete (otherwise dry run).")
        parser.add_argument("--phrase", default="", help='Must equal "RESET <scope>" to execute.')
        parser.add_argument(
            "--backup-confirmed",
            action="store_true",
            help="Acknowledge a fresh backup exists. Required to execute.",
        )

    def handle(self, *args, **options):
        scope = options["scope"]
        plan = build_plan(scope)
        counts = [(label, qs.count()) for label, qs in plan]
        total = sum(count for _label, count in counts)

        self.stdout.write(f"Reset scope: {scope}")
        for label, count in counts:
            self.stdout.write(f"  {label}: {count}")
        self.stdout.write(f"  Total records: {total}")
        self.stdout.write(f"Always preserved: {PRESERVED}")

        dry_run = options["dry_run"] or not options["confirm"]
        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN — nothing was deleted. Re-run with --confirm to execute."))
            return

        # --- Execution guards ---
        if os.environ.get(ENV_FLAG) != "1":
            raise CommandError(
                f"Refusing to delete: set {ENV_FLAG}=1 in the environment to allow data reset."
            )
        expected_phrase = f"RESET {scope}"
        if options["phrase"] != expected_phrase:
            raise CommandError(f'Confirmation phrase mismatch. Pass --phrase "{expected_phrase}".')
        if not options["backup_confirmed"]:
            raise CommandError("Refusing to delete without --backup-confirmed. Take a backup first.")

        create_audit_log(
            action=AuditLog.Action.DATA_RESET,
            module="core",
            object_type="reset",
            object_display=f"scope={scope}",
            new_value={"phase": "before", "scope": scope, "planned_total": total},
        )

        deleted_total = 0
        with transaction.atomic():
            for _label, qs in build_plan(scope):
                removed, _detail = qs.delete()
                deleted_total += removed
            create_audit_log(
                action=AuditLog.Action.DATA_RESET,
                module="core",
                object_type="reset",
                object_display=f"scope={scope}",
                new_value={"phase": "after", "scope": scope, "deleted_total": deleted_total},
            )

        self.stdout.write(self.style.SUCCESS(f"Data reset complete. Deleted {deleted_total} records."))
