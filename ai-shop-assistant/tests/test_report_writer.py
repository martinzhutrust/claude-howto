"""测试报告文件写入。"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import tempfile
from pathlib import Path

from ingestion.mock_data import generate_snapshot
from reports.generator import write_report_file


def test_write_report_creates_file():
    snap = generate_snapshot(period_days=3)
    with tempfile.TemporaryDirectory() as tmp:
        path = write_report_file(snap, "# 测试报告\n内容", output_dir=tmp)
        assert path.exists()
        content = path.read_text(encoding="utf-8")
        assert snap.shop_id in content
        assert "测试报告" in content


def test_report_filename_contains_dates():
    snap = generate_snapshot(period_days=3)
    with tempfile.TemporaryDirectory() as tmp:
        path = write_report_file(snap, "report", output_dir=tmp)
        assert str(snap.period_start) in path.name
        assert str(snap.period_end) in path.name
