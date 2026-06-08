"""用于本地开发和测试的模拟数据生成器。"""
from __future__ import annotations

import random
from datetime import date, timedelta
from decimal import Decimal

from db.models import FanDay, LivestreamSession, ProductStat, ShopSnapshot, TrafficDay

_PRODUCTS = [
    ("P001", "爆款连衣裙-白色", "女装"),
    ("P002", "爆款连衣裙-黑色", "女装"),
    ("P003", "修身牛仔裤", "女装"),
    ("P004", "休闲卫衣套装", "休闲"),
    ("P005", "真皮手提包", "包袋"),
    ("P006", "复古墨镜", "配件"),
]

_rng = random.Random(42)


def _rand_traffic(shop_id: str, d: date, trend: float = 1.0) -> TrafficDay:
    visitors = int(_rng.randint(800, 2000) * trend)
    entries = int(visitors * _rng.uniform(0.3, 0.55))
    convos = int(entries * _rng.uniform(0.15, 0.30))
    orders = int(convos * _rng.uniform(0.20, 0.40))
    gmv = Decimal(str(round(orders * _rng.uniform(120, 350), 2)))
    conv_rate = Decimal(str(round(orders / visitors if visitors else 0, 4)))
    return TrafficDay(
        shop_id=shop_id,
        report_date=d,
        visitor_count=visitors,
        entry_count=entries,
        conversation_count=convos,
        order_count=orders,
        gmv=gmv,
        conversion_rate=conv_rate,
    )


def _rand_products(shop_id: str, d: date, trend: float = 1.0) -> list[ProductStat]:
    stats = []
    for pid, pname, cat in _PRODUCTS:
        views = int(_rng.randint(100, 600) * trend)
        clicks = int(views * _rng.uniform(0.1, 0.35))
        cart = int(clicks * _rng.uniform(0.2, 0.5))
        orders = int(cart * _rng.uniform(0.15, 0.4))
        revenue = Decimal(str(round(orders * _rng.uniform(80, 400), 2)))
        stats.append(
            ProductStat(
                shop_id=shop_id,
                product_id=pid,
                product_name=pname,
                category=cat,
                report_date=d,
                views=views,
                clicks=clicks,
                cart_adds=cart,
                order_count=orders,
                revenue=revenue,
            )
        )
    return stats


def _rand_fans(shop_id: str, d: date, total: int) -> FanDay:
    new_f = _rng.randint(20, 120)
    lost_f = _rng.randint(5, 30)
    return FanDay(
        shop_id=shop_id,
        report_date=d,
        new_fans=new_f,
        lost_fans=lost_f,
        total_fans=total + new_f - lost_f,
    )


def generate_snapshot(
    shop_id: str = "SHOP_DEMO_001",
    period_days: int = 7,
    end_date: date | None = None,
) -> ShopSnapshot:
    """生成指定周期的模拟快照（包含上周对比基准）。"""
    if end_date is None:
        end_date = date.today() - timedelta(days=1)
    start_date = end_date - timedelta(days=period_days - 1)
    prev_start = start_date - timedelta(days=period_days)
    prev_end = start_date - timedelta(days=1)

    # current period
    traffic, products, fans = [], [], []
    fan_total = _rng.randint(40_000, 80_000)
    for i in range(period_days):
        d = start_date + timedelta(days=i)
        trend = 1.0 + 0.05 * i  # slight upward trend
        traffic.append(_rand_traffic(shop_id, d, trend))
        products.extend(_rand_products(shop_id, d, trend))
        fan_day = _rand_fans(shop_id, d, fan_total)
        fan_total = fan_day.total_fans
        fans.append(fan_day)

    # previous period totals for comparison
    prev_traffic = [_rand_traffic(shop_id, prev_start + timedelta(days=i)) for i in range(period_days)]
    prev_gmv = sum((t.gmv for t in prev_traffic), Decimal("0"))
    prev_orders = sum(t.order_count for t in prev_traffic)
    prev_visitors = sum(t.visitor_count for t in prev_traffic)

    return ShopSnapshot(
        shop_id=shop_id,
        period_start=start_date,
        period_end=end_date,
        traffic=traffic,
        products=products,
        fans=fans,
        prev_gmv=prev_gmv,
        prev_order_count=prev_orders,
        prev_visitor_count=prev_visitors,
    )
