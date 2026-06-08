"""将 Qwen 输出的 Markdown 渲染成最终诊断报告文件。"""
from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path

from db.models import ShopSnapshot


def write_report_file(
    snapshot: ShopSnapshot,
    report_md: str,
    output_dir: str = "output",
) -> Path:
    """将报告写入 output/<shop_id>/<date>_diagnostic.md，返回文件路径。"""
    out = Path(output_dir) / snapshot.shop_id
    out.mkdir(parents=True, exist_ok=True)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{ts}_{snapshot.period_start}_{snapshot.period_end}_diagnostic.md"
    filepath = out / filename

    header = f"""# 抖音店铺经营诊断报告

**店铺 ID**：{snapshot.shop_id}
**分析周期**：{snapshot.period_start} 至 {snapshot.period_end}
**生成时间**：{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

---

"""
    filepath.write_text(header + report_md, encoding="utf-8")
    return filepath


def print_report(report_md: str, snapshot: ShopSnapshot) -> None:
    """终端打印报告（带分隔线）。"""
    sep = "=" * 60
    print(f"\n{sep}")
    print(f"  诊断报告 | 店铺 {snapshot.shop_id}")
    print(f"  周期：{snapshot.period_start} → {snapshot.period_end}")
    print(f"{sep}\n")
    print(report_md)
    print(f"\n{sep}\n")
