"""从环境变量加载运行时配置。"""
from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Config:
    # 数据库
    database_url: str
    # 抖音 API（MOCK 模式下可为空字符串）
    douyin_app_key: str
    douyin_app_secret: str
    douyin_access_token: str
    # Qwen
    dashscope_api_key: str
    qwen_model: str
    # 运行参数
    shop_id: str
    report_days: int
    mock_mode: bool
    output_dir: str


def load() -> Config:
    mock = os.environ.get("DOUYIN_MOCK", "0") == "1"
    return Config(
        database_url=os.environ.get("DATABASE_URL", ""),
        douyin_app_key=os.environ.get("DOUYIN_APP_KEY", ""),
        douyin_app_secret=os.environ.get("DOUYIN_APP_SECRET", ""),
        douyin_access_token=os.environ.get("DOUYIN_ACCESS_TOKEN", ""),
        dashscope_api_key=os.environ.get("DASHSCOPE_API_KEY", ""),
        qwen_model=os.environ.get("QWEN_MODEL", "qwen-max"),
        shop_id=os.environ.get("SHOP_ID", "SHOP_DEMO_001"),
        report_days=int(os.environ.get("REPORT_DAYS", "7")),
        mock_mode=mock,
        output_dir=os.environ.get("OUTPUT_DIR", "output"),
    )


def validate(cfg: Config) -> None:
    if not cfg.mock_mode:
        missing = [
            name
            for name, val in [
                ("DATABASE_URL", cfg.database_url),
                ("DOUYIN_APP_KEY", cfg.douyin_app_key),
                ("DOUYIN_APP_SECRET", cfg.douyin_app_secret),
                ("DOUYIN_ACCESS_TOKEN", cfg.douyin_access_token),
                ("DASHSCOPE_API_KEY", cfg.dashscope_api_key),
            ]
            if not val
        ]
        if missing:
            raise EnvironmentError(f"缺少必要环境变量: {', '.join(missing)}")
    else:
        if not cfg.dashscope_api_key:
            raise EnvironmentError("MOCK 模式也需要 DASHSCOPE_API_KEY 调用 Qwen")
