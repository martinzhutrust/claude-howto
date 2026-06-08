"""分析 Agent：从 PostgreSQL 加载快照，调用 Qwen 生成诊断。"""
from __future__ import annotations

import logging
from datetime import date
from decimal import Decimal

from db.connection import acquire
from db.models import FanDay, ProductStat, ShopSnapshot, TrafficDay
from agent.prompts import build_analysis_prompt
from llm.qwen_client import QwenClient

logger = logging.getLogger(__name__)


async def load_snapshot(
    shop_id: str,
    start_date: date,
    end_date: date,
) -> ShopSnapshot:
    """从数据库加载指定周期的快照，并附上上一等长周期的对比基准。"""
    from datetime import timedelta

    period_days = (end_date - start_date).days + 1
    prev_end = start_date - timedelta(days=1)
    prev_start = prev_end - timedelta(days=period_days - 1)

    async with acquire() as conn:
        # 当期流量
        traffic_rows = await conn.fetch(
            """
            SELECT report_date, visitor_count, entry_count,
                   conversation_count, order_count, gmv, conversion_rate
            FROM shop_traffic_daily
            WHERE shop_id = $1 AND report_date BETWEEN $2 AND $3
            ORDER BY report_date
            """,
            shop_id, start_date, end_date,
        )

        # 当期商品
        product_rows = await conn.fetch(
            """
            SELECT product_id, product_name, category, report_date,
                   views, clicks, cart_adds, order_count, revenue
            FROM product_stats
            WHERE shop_id = $1 AND report_date BETWEEN $2 AND $3
            ORDER BY report_date, revenue DESC
            """,
            shop_id, start_date, end_date,
        )

        # 当期粉丝
        fan_rows = await conn.fetch(
            """
            SELECT report_date, new_fans, lost_fans, total_fans
            FROM fan_stats_daily
            WHERE shop_id = $1 AND report_date BETWEEN $2 AND $3
            ORDER BY report_date
            """,
            shop_id, start_date, end_date,
        )

        # 上期汇总（对比基准）
        prev_agg = await conn.fetchrow(
            """
            SELECT COALESCE(SUM(gmv), 0)         AS prev_gmv,
                   COALESCE(SUM(order_count), 0) AS prev_order_count,
                   COALESCE(SUM(visitor_count), 0) AS prev_visitor_count
            FROM shop_traffic_daily
            WHERE shop_id = $1 AND report_date BETWEEN $2 AND $3
            """,
            shop_id, prev_start, prev_end,
        )

    traffic = [
        TrafficDay(
            shop_id=shop_id,
            report_date=r["report_date"],
            visitor_count=r["visitor_count"],
            entry_count=r["entry_count"],
            conversation_count=r["conversation_count"],
            order_count=r["order_count"],
            gmv=r["gmv"],
            conversion_rate=r["conversion_rate"],
        )
        for r in traffic_rows
    ]
    products = [
        ProductStat(
            shop_id=shop_id,
            product_id=r["product_id"],
            product_name=r["product_name"],
            category=r["category"] or "",
            report_date=r["report_date"],
            views=r["views"],
            clicks=r["clicks"],
            cart_adds=r["cart_adds"],
            order_count=r["order_count"],
            revenue=r["revenue"],
        )
        for r in product_rows
    ]
    fans = [
        FanDay(
            shop_id=shop_id,
            report_date=r["report_date"],
            new_fans=r["new_fans"],
            lost_fans=r["lost_fans"],
            total_fans=r["total_fans"],
        )
        for r in fan_rows
    ]

    return ShopSnapshot(
        shop_id=shop_id,
        period_start=start_date,
        period_end=end_date,
        traffic=traffic,
        products=products,
        fans=fans,
        prev_gmv=prev_agg["prev_gmv"] if prev_agg else Decimal("0"),
        prev_order_count=prev_agg["prev_order_count"] if prev_agg else 0,
        prev_visitor_count=prev_agg["prev_visitor_count"] if prev_agg else 0,
    )


async def run_analysis(
    snapshot: ShopSnapshot,
    qwen: QwenClient,
) -> str:
    """将快照送入 Qwen，返回诊断报告 Markdown 文本。"""
    prompt = build_analysis_prompt(snapshot)
    logger.info(
        "sending analysis prompt to Qwen (shop=%s, %s→%s)",
        snapshot.shop_id,
        snapshot.period_start,
        snapshot.period_end,
    )
    report_md = await qwen.chat(prompt)
    return report_md


async def save_report(snapshot: ShopSnapshot, report_md: str) -> int:
    """将生成的报告写入 diagnostic_reports 表，返回新行 ID。"""
    async with acquire() as conn:
        row_id = await conn.fetchval(
            """
            INSERT INTO diagnostic_reports
                (shop_id, period_start, period_end, report_md)
            VALUES ($1, $2, $3, $4)
            RETURNING id
            """,
            snapshot.shop_id,
            snapshot.period_start,
            snapshot.period_end,
            report_md,
        )
    logger.info("saved report id=%d for shop=%s", row_id, snapshot.shop_id)
    return row_id
