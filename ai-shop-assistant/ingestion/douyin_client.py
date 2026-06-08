"""抖音来客 Open API 客户端。

实际调用需要在抖音开放平台申请 access_token。
开发/测试时设置环境变量 DOUYIN_MOCK=1 以使用内置模拟数据。
"""
from __future__ import annotations

import hashlib
import hmac
import os
import time
from datetime import date
from typing import Any

import httpx

_BASE_URL = "https://open.douyin.com"


class DouyinClient:
    def __init__(
        self,
        app_key: str,
        app_secret: str,
        access_token: str,
        timeout: float = 15.0,
    ) -> None:
        self.app_key = app_key
        self.app_secret = app_secret
        self.access_token = access_token
        self._http = httpx.AsyncClient(
            base_url=_BASE_URL,
            timeout=timeout,
            headers={
                "Content-Type": "application/json",
                "access-token": access_token,
            },
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _sign(self, params: dict[str, Any]) -> str:
        sorted_str = "".join(f"{k}{v}" for k, v in sorted(params.items()))
        payload = self.app_secret + sorted_str + self.app_secret
        return hmac.new(
            self.app_secret.encode(), payload.encode(), hashlib.md5
        ).hexdigest().upper()

    def _base_params(self) -> dict[str, Any]:
        return {
            "app_key": self.app_key,
            "timestamp": str(int(time.time())),
        }

    async def _get(self, path: str, params: dict[str, Any]) -> dict[str, Any]:
        all_params = {**self._base_params(), **params}
        all_params["sign"] = self._sign(all_params)
        resp = await self._http.get(path, params=all_params)
        resp.raise_for_status()
        data = resp.json()
        if data.get("err_no", 0) != 0:
            raise RuntimeError(f"Douyin API error {data['err_no']}: {data.get('err_tips')}")
        return data

    # ------------------------------------------------------------------
    # Public API methods (抖音来客数据接口)
    # ------------------------------------------------------------------

    async def get_traffic_daily(
        self, shop_id: str, start_date: date, end_date: date
    ) -> list[dict[str, Any]]:
        """店铺每日流量数据。"""
        data = await self._get(
            "/shop/v1/traffic/daily",
            {
                "shop_id": shop_id,
                "start_date": start_date.strftime("%Y%m%d"),
                "end_date": end_date.strftime("%Y%m%d"),
            },
        )
        return data.get("data", {}).get("list", [])

    async def get_product_stats(
        self, shop_id: str, start_date: date, end_date: date
    ) -> list[dict[str, Any]]:
        """商品销售数据。"""
        data = await self._get(
            "/shop/v1/product/stats",
            {
                "shop_id": shop_id,
                "start_date": start_date.strftime("%Y%m%d"),
                "end_date": end_date.strftime("%Y%m%d"),
            },
        )
        return data.get("data", {}).get("list", [])

    async def get_livestream_sessions(
        self, shop_id: str, start_date: date, end_date: date
    ) -> list[dict[str, Any]]:
        """直播场次数据。"""
        data = await self._get(
            "/shop/v1/live/sessions",
            {
                "shop_id": shop_id,
                "start_date": start_date.strftime("%Y%m%d"),
                "end_date": end_date.strftime("%Y%m%d"),
            },
        )
        return data.get("data", {}).get("list", [])

    async def get_fan_stats(
        self, shop_id: str, start_date: date, end_date: date
    ) -> list[dict[str, Any]]:
        """粉丝增减数据。"""
        data = await self._get(
            "/shop/v1/fans/daily",
            {
                "shop_id": shop_id,
                "start_date": start_date.strftime("%Y%m%d"),
                "end_date": end_date.strftime("%Y%m%d"),
            },
        )
        return data.get("data", {}).get("list", [])

    async def aclose(self) -> None:
        await self._http.aclose()


def build_client() -> DouyinClient:
    """从环境变量构建客户端实例。"""
    return DouyinClient(
        app_key=os.environ["DOUYIN_APP_KEY"],
        app_secret=os.environ["DOUYIN_APP_SECRET"],
        access_token=os.environ["DOUYIN_ACCESS_TOKEN"],
    )
