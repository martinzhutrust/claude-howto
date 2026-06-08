#!/usr/bin/env python3
"""AI 店长助手 — 主入口。

运行方式：
  # 完整流程（真实 API）
  python main.py

  # 模拟数据模式（跳过抖音拉取，直接生成报告）
  DOUYIN_MOCK=1 python main.py

  # 指定分析周期
  DOUYIN_MOCK=1 REPORT_DAYS=14 python main.py
"""
from __future__ import annotations

import asyncio
import logging
import sys
from datetime import date, timedelta

import config
from db import close_pool, init_schema
from ingestion import build_client, full_sync, generate_snapshot
from agent import load_snapshot, run_analysis, save_report
from llm import build_qwen_client
from reports import print_report, write_report_file

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


async def run_mock_pipeline(cfg: config.Config) -> None:
    """使用内置模拟数据运行完整管道（无需数据库或抖音 API）。"""
    logger.info("=== MOCK 模式启动 ===")
    end_date = date.today() - timedelta(days=1)
    snapshot = generate_snapshot(
        shop_id=cfg.shop_id,
        period_days=cfg.report_days,
        end_date=end_date,
    )
    logger.info(
        "模拟快照已生成：%s → %s，%d 天",
        snapshot.period_start,
        snapshot.period_end,
        cfg.report_days,
    )

    qwen = build_qwen_client()
    try:
        report_md = await run_analysis(snapshot, qwen)
    finally:
        await qwen.aclose()

    filepath = write_report_file(snapshot, report_md, cfg.output_dir)
    print_report(report_md, snapshot)
    logger.info("报告已保存至 %s", filepath)


async def run_full_pipeline(cfg: config.Config) -> None:
    """完整流程：拉取抖音数据 → 写 PG → 分析 → 生成报告。"""
    logger.info("=== 完整流程启动（shop=%s）===", cfg.shop_id)

    # 1. 初始化数据库
    await init_schema()
    logger.info("数据库 Schema 就绪")

    # 2. 从抖音 API 拉取数据
    end_date = date.today() - timedelta(days=1)
    start_date = end_date - timedelta(days=cfg.report_days - 1)

    douyin = build_client()
    try:
        sync_result = await full_sync(douyin, cfg.shop_id, start_date, end_date)
        logger.info("数据同步完成：%s", sync_result)
    finally:
        await douyin.aclose()

    # 3. 从数据库加载快照
    snapshot = await load_snapshot(cfg.shop_id, start_date, end_date)
    logger.info("快照加载完成，流量记录 %d 条", len(snapshot.traffic))

    # 4. 调用 Qwen 生成分析
    qwen = build_qwen_client()
    try:
        report_md = await run_analysis(snapshot, qwen)
    finally:
        await qwen.aclose()

    # 5. 保存报告
    await save_report(snapshot, report_md)
    filepath = write_report_file(snapshot, report_md, cfg.output_dir)
    print_report(report_md, snapshot)
    logger.info("报告已保存至 %s", filepath)

    await close_pool()


async def main() -> None:
    cfg = config.load()
    try:
        config.validate(cfg)
    except EnvironmentError as exc:
        logger.error("%s", exc)
        sys.exit(1)

    if cfg.mock_mode:
        await run_mock_pipeline(cfg)
    else:
        await run_full_pipeline(cfg)


if __name__ == "__main__":
    asyncio.run(main())
