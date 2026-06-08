"""诊断报告的 Prompt 模板。"""
from __future__ import annotations

from decimal import Decimal

from db.models import ShopSnapshot


def build_analysis_prompt(snapshot: ShopSnapshot) -> str:
    s = snapshot

    # 汇总当期数据
    total_visitors = sum(t.visitor_count for t in s.traffic)
    total_entries = sum(t.entry_count for t in s.traffic)
    total_orders = sum(t.order_count for t in s.traffic)
    total_gmv = sum((t.gmv for t in s.traffic), Decimal("0"))
    avg_conversion = (
        sum(float(t.conversion_rate) for t in s.traffic) / len(s.traffic)
        if s.traffic else 0
    )

    # 粉丝
    net_fans = sum(f.net_fans for f in s.fans)
    end_fans = s.fans[-1].total_fans if s.fans else 0

    # 商品 TOP3（按收入）
    from collections import defaultdict
    product_revenue: dict[str, Decimal] = defaultdict(Decimal)
    product_orders: dict[str, int] = defaultdict(int)
    product_names: dict[str, str] = {}
    for p in s.products:
        product_revenue[p.product_id] += p.revenue
        product_orders[p.product_id] += p.order_count
        product_names[p.product_id] = p.product_name
    top3 = sorted(product_revenue, key=lambda k: product_revenue[k], reverse=True)[:3]
    top3_lines = "\n".join(
        f"  {i+1}. {product_names[pid]}：收入 ¥{product_revenue[pid]:.0f}，"
        f"订单 {product_orders[pid]} 件"
        for i, pid in enumerate(top3)
    )

    # 环比变化
    def pct(curr: float, prev: float) -> str:
        if prev == 0:
            return "N/A"
        diff = (curr - prev) / prev * 100
        sign = "+" if diff >= 0 else ""
        return f"{sign}{diff:.1f}%"

    gmv_chg = pct(float(total_gmv), float(s.prev_gmv))
    order_chg = pct(total_orders, s.prev_order_count)
    visitor_chg = pct(total_visitors, s.prev_visitor_count)

    return f"""你是一名资深抖音电商运营诊断专家。请根据以下店铺数据，生成一份专业的经营诊断报告。

## 店铺基本信息
- 店铺 ID：{s.shop_id}
- 分析周期：{s.period_start} 至 {s.period_end}（共 {len(s.traffic)} 天）

## 核心数据汇总（当期）
| 指标 | 数值 | 环比变化 |
|------|------|---------|
| 访客数 | {total_visitors:,} | {visitor_chg} |
| 进店次数 | {total_entries:,} | — |
| 成交订单 | {total_orders:,} | {order_chg} |
| 成交金额(GMV) | ¥{total_gmv:,.0f} | {gmv_chg} |
| 平均转化率 | {avg_conversion:.2%} | — |
| 粉丝净增 | {net_fans:+,} | — |
| 当前粉丝总量 | {end_fans:,} | — |

## 商品 TOP3（按收入排名）
{top3_lines}

## 要求
请按以下结构输出报告（Markdown 格式）：

1. **经营概况**（3-5 句话，点明核心亮点与问题）
2. **流量诊断**（访客质量、转化漏斗分析，识别关键断层）
3. **商品诊断**（爆款集中度、长尾商品机会）
4. **粉丝运营**（粉丝增长健康度评估）
5. **优先行动建议**（列出 3-5 条可立即执行的具体措施，附预期效果）
6. **风险预警**（如有异常指标，给出警示）

要求：语言专业简洁，直接给出判断，避免模糊表述；行动建议须具体到操作层面。
"""
