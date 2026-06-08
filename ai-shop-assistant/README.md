# AI 店长助手

抖音来客电商数据自动诊断系统。

```
抖音来客 API
     ↓  (ingestion/)
PostgreSQL
     ↓  (agent/)
分析 Agent  ←── 结构化 Prompt
     ↓  (llm/)
Qwen (通义千问)
     ↓  (reports/)
诊断报告 (.md)
```

## 快速开始

### 1. 安装依赖

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env，填写 DASHSCOPE_API_KEY 等必要参数
```

### 3. 运行（模拟模式，无需真实 API）

```bash
DOUYIN_MOCK=1 DASHSCOPE_API_KEY=sk-xxx python main.py
```

报告将输出到 `output/<SHOP_ID>/` 目录，同时在终端打印。

### 4. 完整流程（真实数据）

```bash
# 确保 .env 中所有变量已填写，数据库已启动
python main.py
```

## 目录结构

```
ai-shop-assistant/
├── main.py              # 入口，orchestrates 完整管道
├── config.py            # 环境变量加载与校验
├── db/
│   ├── schema.sql       # PostgreSQL 表定义
│   ├── models.py        # 数据模型 (dataclasses)
│   └── connection.py    # asyncpg 连接池
├── ingestion/
│   ├── douyin_client.py # 抖音来客 Open API 客户端
│   ├── sync.py          # 数据同步（API → PostgreSQL）
│   └── mock_data.py     # 本地开发模拟数据
├── agent/
│   ├── analyzer.py      # 分析 Agent（加载快照、调用 LLM、保存）
│   └── prompts.py       # 诊断 Prompt 构建
├── llm/
│   └── qwen_client.py   # Qwen / DashScope 客户端
├── reports/
│   └── generator.py     # 报告文件写入与终端打印
└── tests/               # 单元测试（无需网络/数据库）
```

## 数据库 Schema

| 表名 | 说明 |
|------|------|
| `shop_traffic_daily` | 每日流量汇总（访客、进店、转化、GMV） |
| `product_stats` | 商品每日销售数据 |
| `livestream_sessions` | 直播场次数据 |
| `fan_stats_daily` | 粉丝增减日报 |
| `diagnostic_reports` | 历史诊断报告存档 |

初始化：

```bash
# 自动初始化（程序启动时自动执行）
python main.py

# 或手动执行
psql $DATABASE_URL -f db/schema.sql
```

## Qwen 模型选择

| 模型 | 适用场景 | 价格 |
|------|---------|------|
| `qwen-max` | 最高质量诊断（推荐） | 较高 |
| `qwen-plus` | 性价比平衡 | 中等 |
| `qwen-turbo` | 低成本快速输出 | 低 |

通过环境变量 `QWEN_MODEL` 切换。

## 测试

```bash
pytest tests/ -v
```

测试不依赖数据库或外部 API，可在本地直接运行。

## 环境变量参考

| 变量 | 必填 | 说明 |
|------|------|------|
| `DATABASE_URL` | 非 MOCK 模式 | PostgreSQL 连接串 |
| `DOUYIN_APP_KEY` | 非 MOCK 模式 | 抖音开放平台 App Key |
| `DOUYIN_APP_SECRET` | 非 MOCK 模式 | 抖音开放平台 App Secret |
| `DOUYIN_ACCESS_TOKEN` | 非 MOCK 模式 | 店铺授权 Token |
| `DASHSCOPE_API_KEY` | 必填 | 阿里云灵积 API Key |
| `QWEN_MODEL` | 否 | 默认 `qwen-max` |
| `SHOP_ID` | 否 | 默认 `SHOP_DEMO_001` |
| `REPORT_DAYS` | 否 | 分析天数，默认 `7` |
| `DOUYIN_MOCK` | 否 | 设为 `1` 启用模拟数据 |
| `OUTPUT_DIR` | 否 | 报告输出目录，默认 `output` |
