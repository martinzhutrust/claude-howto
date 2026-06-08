"""测试模拟数据生成器和 Prompt 构建。"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from datetime import date
from decimal import Decimal

from ingestion.mock_data import generate_snapshot
from agent.prompts import build_analysis_prompt


def test_generate_snapshot_basic():
    snap = generate_snapshot(shop_id="TEST001", period_days=7)
    assert snap.shop_id == "TEST001"
    assert len(snap.traffic) == 7
    assert len(snap.fans) == 7
    assert len(snap.products) == 7 * 6  # 6 products × 7 days
    assert snap.period_end >= snap.period_start


def test_snapshot_gmv_positive():
    snap = generate_snapshot(period_days=3)
    total_gmv = sum(t.gmv for t in snap.traffic)
    assert total_gmv > Decimal("0")


def test_product_conversion_rate():
    snap = generate_snapshot(period_days=1)
    for p in snap.products:
        assert 0.0 <= p.conversion_rate <= 1.0
        assert 0.0 <= p.click_rate <= 1.0


def test_fan_net_calculation():
    snap = generate_snapshot(period_days=5)
    for f in snap.fans:
        assert f.net_fans == f.new_fans - f.lost_fans


def test_build_analysis_prompt_contains_shop_id():
    snap = generate_snapshot(shop_id="MY_SHOP", period_days=7)
    prompt = build_analysis_prompt(snap)
    assert "MY_SHOP" in prompt
    assert "GMV" in prompt or "成交金额" in prompt
    assert "转化率" in prompt


def test_build_analysis_prompt_prev_comparison():
    snap = generate_snapshot(period_days=7)
    # inject known previous values
    snap = snap.__class__(
        **{**snap.__dict__, "prev_gmv": Decimal("10000"), "prev_order_count": 50}
    )
    prompt = build_analysis_prompt(snap)
    # pct change should appear in prompt
    assert "%" in prompt
