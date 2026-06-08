from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal


@dataclass
class TrafficDay:
    shop_id: str
    report_date: date
    visitor_count: int = 0
    entry_count: int = 0
    conversation_count: int = 0
    order_count: int = 0
    gmv: Decimal = field(default_factory=lambda: Decimal("0"))
    conversion_rate: Decimal = field(default_factory=lambda: Decimal("0"))


@dataclass
class ProductStat:
    shop_id: str
    product_id: str
    product_name: str
    report_date: date
    category: str = ""
    views: int = 0
    clicks: int = 0
    cart_adds: int = 0
    order_count: int = 0
    revenue: Decimal = field(default_factory=lambda: Decimal("0"))

    @property
    def click_rate(self) -> float:
        return self.clicks / self.views if self.views else 0.0

    @property
    def conversion_rate(self) -> float:
        return self.order_count / self.clicks if self.clicks else 0.0


@dataclass
class LivestreamSession:
    shop_id: str
    session_id: str
    start_time: datetime
    end_time: datetime | None = None
    total_viewers: int = 0
    peak_viewers: int = 0
    new_fans: int = 0
    order_count: int = 0
    revenue: Decimal = field(default_factory=lambda: Decimal("0"))

    @property
    def duration_minutes(self) -> float | None:
        if self.end_time is None:
            return None
        return (self.end_time - self.start_time).total_seconds() / 60


@dataclass
class FanDay:
    shop_id: str
    report_date: date
    new_fans: int = 0
    lost_fans: int = 0
    total_fans: int = 0

    @property
    def net_fans(self) -> int:
        return self.new_fans - self.lost_fans


@dataclass
class ShopSnapshot:
    """Aggregated data window passed to the analysis agent."""
    shop_id: str
    period_start: date
    period_end: date
    traffic: list[TrafficDay] = field(default_factory=list)
    products: list[ProductStat] = field(default_factory=list)
    livestreams: list[LivestreamSession] = field(default_factory=list)
    fans: list[FanDay] = field(default_factory=list)

    # previous-period totals for comparison (optional)
    prev_gmv: Decimal = field(default_factory=lambda: Decimal("0"))
    prev_order_count: int = 0
    prev_visitor_count: int = 0
