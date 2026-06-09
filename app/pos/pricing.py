from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP

from django.db.models import Q
from django.utils import timezone

from catalog.models import SupplierProductCost

from .models import Promotion


MONEY = Decimal("0.01")


@dataclass(frozen=True)
class CostSnapshot:
    reference_unit_cost: Decimal
    actual_unit_cost: Decimal
    landed_unit_cost: Decimal | None
    cost_basis: Decimal


@dataclass(frozen=True)
class PromotionPrice:
    promotion: Promotion | None
    original_unit_price: Decimal
    final_unit_price: Decimal
    discount_per_unit: Decimal

    @property
    def promotion_name(self):
        return self.promotion.name if self.promotion else ""


def money(value):
    return Decimal(value or "0.00").quantize(MONEY, rounding=ROUND_HALF_UP)


def get_reference_unit_cost(product, supplier):
    reference = (
        SupplierProductCost.objects.filter(product=product, supplier=supplier, is_active=True)
        .order_by("-updated_at", "-id")
        .first()
    )
    if reference is not None:
        return money(reference.reference_unit_cost)
    return money(product.default_cost_price)


def get_cost_snapshot(stock_batch):
    reference_unit_cost = get_reference_unit_cost(stock_batch.product, stock_batch.supplier)
    actual_unit_cost = money(stock_batch.actual_unit_cost)
    landed_unit_cost = money(stock_batch.landed_unit_cost) if stock_batch.landed_unit_cost is not None else None
    cost_basis = landed_unit_cost if landed_unit_cost is not None else actual_unit_cost
    if cost_basis <= 0 and reference_unit_cost > 0:
        cost_basis = reference_unit_cost
    return CostSnapshot(
        reference_unit_cost=reference_unit_cost,
        actual_unit_cost=actual_unit_cost,
        landed_unit_cost=landed_unit_cost,
        cost_basis=money(cost_basis),
    )


def promotion_applies_to_product(promotion, product):
    if promotion.product_id and promotion.product_id == product.id:
        return True
    return bool(promotion.category_id and product.category_id and promotion.category_id == product.category_id)


def active_promotions_for_product(product, today=None):
    today = today or timezone.localdate()
    scope = Q(product=product)
    if product.category_id:
        scope |= Q(category_id=product.category_id)
    return (
        Promotion.objects.select_related("product", "category")
        .filter(
            is_active=True,
            start_date__lte=today,
            end_date__gte=today,
        )
        .filter(scope)
        .order_by("name", "id")
    )


def calculate_promotion_price(promotion, original_unit_price):
    original_unit_price = money(original_unit_price)
    if promotion.discount_type == Promotion.DiscountType.PERCENTAGE:
        discount_per_unit = money(original_unit_price * promotion.value / Decimal("100.00"))
        final_unit_price = original_unit_price - discount_per_unit
    elif promotion.discount_type == Promotion.DiscountType.FIXED_AMOUNT:
        discount_per_unit = min(money(promotion.value), original_unit_price)
        final_unit_price = original_unit_price - discount_per_unit
    else:
        final_unit_price = min(original_unit_price, money(promotion.value))
        discount_per_unit = original_unit_price - final_unit_price
    return PromotionPrice(
        promotion=promotion,
        original_unit_price=original_unit_price,
        final_unit_price=money(max(final_unit_price, Decimal("0.00"))),
        discount_per_unit=money(max(discount_per_unit, Decimal("0.00"))),
    )


def choose_best_promotion(stock_batch):
    original_unit_price = money(stock_batch.selling_price)
    candidates = [
        calculate_promotion_price(promotion, original_unit_price)
        for promotion in active_promotions_for_product(stock_batch.product)
        if promotion_applies_to_product(promotion, stock_batch.product)
    ]
    if not candidates:
        return PromotionPrice(
            promotion=None,
            original_unit_price=original_unit_price,
            final_unit_price=original_unit_price,
            discount_per_unit=Decimal("0.00"),
        )
    return sorted(
        candidates,
        key=lambda candidate: (
            candidate.final_unit_price,
            0 if candidate.promotion.product_id else 1,
            candidate.promotion.name,
            candidate.promotion.id,
        ),
    )[0]


def allocate_discount(total_discount, line_totals):
    total_discount = money(total_discount)
    if total_discount <= 0:
        return [Decimal("0.00") for _line_total in line_totals]
    pre_discount_total = sum(line_totals, Decimal("0.00"))
    if pre_discount_total <= 0:
        return [Decimal("0.00") for _line_total in line_totals]

    allocations = []
    remaining = total_discount
    for index, line_total in enumerate(line_totals):
        if index == len(line_totals) - 1:
            allocation = min(remaining, line_total)
        else:
            allocation = money(total_discount * line_total / pre_discount_total)
            allocation = min(allocation, line_total, remaining)
        allocations.append(allocation)
        remaining -= allocation
    return allocations
