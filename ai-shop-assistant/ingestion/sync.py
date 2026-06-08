"""将抖音来客数据同步写入 PostgreSQL。"""
from __future__ import annotations

import logging
from datetime import date

from db.connection import acquire
from db.models import FanDay, LivestreamSession, ProductStat, TrafficDay
from ingestion.douyin_client import DouyinClient

logger = logging.getLogger(__name__)


async def upsert_traffic(rows: list[TrafficDay]) -> int:
    if not rows:
        return 0
    async with acquire() as conn:
        result = await conn.executemany(
            """
            INSERT INTO shop_traffic_daily
                (shop_id, report_date, visitor_count, entry_count,
                 conversation_count, order_count, gmv, conversion_rate)
            VALUES ($1,$2,$3,$4,$5,$6,$7,$8)
            ON CONFLICT (shop_id, report_date) DO UPDATE SET
                visitor_count      = EXCLUDED.visitor_count,
                entry_count        = EXCLUDED.entry_count,
                conversation_count = EXCLUDED.conversation_count,
                order_count        = EXCLUDED.order_count,
                gmv                = EXCLUDED.gmv,
                conversion_rate    = EXCLUDED.conversion_rate
            """,
            [
                (r.shop_id, r.report_date, r.visitor_count, r.entry_count,
                 r.conversation_count, r.order_count, r.gmv, r.conversion_rate)
                for r in rows
            ],
        )
    count = len(rows)
    logger.info("upserted %d traffic rows", count)
    return count


async def upsert_products(rows: list[ProductStat]) -> int:
    if not rows:
        return 0
    async with acquire() as conn:
        await conn.executemany(
            """
            INSERT INTO product_stats
                (shop_id, product_id, product_name, category, report_date,
                 views, clicks, cart_adds, order_count, revenue)
            VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10)
            ON CONFLICT (shop_id, product_id, report_date) DO UPDATE SET
                product_name = EXCLUDED.product_name,
                category     = EXCLUDED.category,
                views        = EXCLUDED.views,
                clicks       = EXCLUDED.clicks,
                cart_adds    = EXCLUDED.cart_adds,
                order_count  = EXCLUDED.order_count,
                revenue      = EXCLUDED.revenue
            """,
            [
                (r.shop_id, r.product_id, r.product_name, r.category, r.report_date,
                 r.views, r.clicks, r.cart_adds, r.order_count, r.revenue)
                for r in rows
            ],
        )
    count = len(rows)
    logger.info("upserted %d product rows", count)
    return count


async def upsert_fans(rows: list[FanDay]) -> int:
    if not rows:
        return 0
    async with acquire() as conn:
        await conn.executemany(
            """
            INSERT INTO fan_stats_daily
                (shop_id, report_date, new_fans, lost_fans, total_fans)
            VALUES ($1,$2,$3,$4,$5)
            ON CONFLICT (shop_id, report_date) DO UPDATE SET
                new_fans   = EXCLUDED.new_fans,
                lost_fans  = EXCLUDED.lost_fans,
                total_fans = EXCLUDED.total_fans
            """,
            [(r.shop_id, r.report_date, r.new_fans, r.lost_fans, r.total_fans) for r in rows],
        )
    count = len(rows)
    logger.info("upserted %d fan rows", count)
    return count


async def full_sync(
    client: DouyinClient,
    shop_id: str,
    start_date: date,
    end_date: date,
) -> dict[str, int]:
    """从抖音 API 拉取所有数据并写入数据库。"""
    raw_traffic = await client.get_traffic_daily(shop_id, start_date, end_date)
    raw_products = await client.get_product_stats(shop_id, start_date, end_date)
    raw_fans = await client.get_fan_stats(shop_id, start_date, end_date)

    traffic_rows = [
        TrafficDay(
            shop_id=shop_id,
            report_date=date.fromisoformat(r["date"]),
            visitor_count=r.get("visitor_count", 0),
            entry_count=r.get("entry_count", 0),
            conversation_count=r.get("conversation_count", 0),
            order_count=r.get("order_count", 0),
            gmv=r.get("gmv", 0),
            conversion_rate=r.get("conversion_rate", 0),
        )
        for r in raw_traffic
    ]
    product_rows = [
        ProductStat(
            shop_id=shop_id,
            product_id=r["product_id"],
            product_name=r.get("product_name", ""),
            category=r.get("category", ""),
            report_date=date.fromisoformat(r["date"]),
            views=r.get("views", 0),
            clicks=r.get("clicks", 0),
            cart_adds=r.get("cart_adds", 0),
            order_count=r.get("order_count", 0),
            revenue=r.get("revenue", 0),
        )
        for r in raw_products
    ]
    fan_rows = [
        FanDay(
            shop_id=shop_id,
            report_date=date.fromisoformat(r["date"]),
            new_fans=r.get("new_fans", 0),
            lost_fans=r.get("lost_fans", 0),
            total_fans=r.get("total_fans", 0),
        )
        for r in raw_fans
    ]

    return {
        "traffic": await upsert_traffic(traffic_rows),
        "products": await upsert_products(product_rows),
        "fans": await upsert_fans(fan_rows),
    }
