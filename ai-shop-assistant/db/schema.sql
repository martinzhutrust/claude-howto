-- 抖音来客数据库 Schema
-- 店铺流量日报
CREATE TABLE IF NOT EXISTS shop_traffic_daily (
    id          BIGSERIAL PRIMARY KEY,
    shop_id     VARCHAR(64)    NOT NULL,
    report_date DATE           NOT NULL,
    visitor_count       INTEGER        NOT NULL DEFAULT 0,  -- 访客数
    entry_count         INTEGER        NOT NULL DEFAULT 0,  -- 进店次数
    conversation_count  INTEGER        NOT NULL DEFAULT 0,  -- 咨询人数
    order_count         INTEGER        NOT NULL DEFAULT 0,  -- 成交订单数
    gmv                 NUMERIC(14,2)  NOT NULL DEFAULT 0,  -- 成交金额
    conversion_rate     NUMERIC(6,4)   NOT NULL DEFAULT 0,  -- 转化率
    created_at  TIMESTAMPTZ    NOT NULL DEFAULT NOW(),
    UNIQUE (shop_id, report_date)
);

-- 商品销售数据
CREATE TABLE IF NOT EXISTS product_stats (
    id              BIGSERIAL PRIMARY KEY,
    shop_id         VARCHAR(64)    NOT NULL,
    product_id      VARCHAR(128)   NOT NULL,
    product_name    VARCHAR(512)   NOT NULL,
    category        VARCHAR(128),
    report_date     DATE           NOT NULL,
    views           INTEGER        NOT NULL DEFAULT 0,
    clicks          INTEGER        NOT NULL DEFAULT 0,
    cart_adds       INTEGER        NOT NULL DEFAULT 0,
    order_count     INTEGER        NOT NULL DEFAULT 0,
    revenue         NUMERIC(14,2)  NOT NULL DEFAULT 0,
    created_at      TIMESTAMPTZ    NOT NULL DEFAULT NOW(),
    UNIQUE (shop_id, product_id, report_date)
);

-- 直播场次数据
CREATE TABLE IF NOT EXISTS livestream_sessions (
    id              BIGSERIAL PRIMARY KEY,
    shop_id         VARCHAR(64)    NOT NULL,
    session_id      VARCHAR(128)   NOT NULL UNIQUE,
    start_time      TIMESTAMPTZ    NOT NULL,
    end_time        TIMESTAMPTZ,
    total_viewers   INTEGER        NOT NULL DEFAULT 0,
    peak_viewers    INTEGER        NOT NULL DEFAULT 0,
    new_fans        INTEGER        NOT NULL DEFAULT 0,
    order_count     INTEGER        NOT NULL DEFAULT 0,
    revenue         NUMERIC(14,2)  NOT NULL DEFAULT 0,
    created_at      TIMESTAMPTZ    NOT NULL DEFAULT NOW()
);

-- 粉丝增减数据
CREATE TABLE IF NOT EXISTS fan_stats_daily (
    id          BIGSERIAL PRIMARY KEY,
    shop_id     VARCHAR(64)    NOT NULL,
    report_date DATE           NOT NULL,
    new_fans    INTEGER        NOT NULL DEFAULT 0,
    lost_fans   INTEGER        NOT NULL DEFAULT 0,
    net_fans    INTEGER        GENERATED ALWAYS AS (new_fans - lost_fans) STORED,
    total_fans  BIGINT         NOT NULL DEFAULT 0,
    created_at  TIMESTAMPTZ    NOT NULL DEFAULT NOW(),
    UNIQUE (shop_id, report_date)
);

-- 诊断报告存档
CREATE TABLE IF NOT EXISTS diagnostic_reports (
    id          BIGSERIAL PRIMARY KEY,
    shop_id     VARCHAR(64)    NOT NULL,
    period_start DATE          NOT NULL,
    period_end   DATE          NOT NULL,
    report_md   TEXT           NOT NULL,
    created_at  TIMESTAMPTZ    NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_traffic_shop_date  ON shop_traffic_daily (shop_id, report_date DESC);
CREATE INDEX IF NOT EXISTS idx_product_shop_date  ON product_stats       (shop_id, report_date DESC);
CREATE INDEX IF NOT EXISTS idx_livestream_shop     ON livestream_sessions (shop_id, start_time DESC);
CREATE INDEX IF NOT EXISTS idx_fans_shop_date      ON fan_stats_daily     (shop_id, report_date DESC);
