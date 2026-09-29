---
name: em-crawler
description: 东方财富全量采集 CLI 的使用指引。当用户需要查询股票行情、资金流向、财务报表、F10 公司资料、公告研报、基金数据、宏观指标、股吧帖子或个股诊断评分时使用。通过 em-crawler 命令行调用，输出 JSON 信封格式数据。
version: 1.0.0
---

# em-crawler（东方财富全量采集）

本 skill 描述如何使用 `em-crawler` CLI 采集东方财富公开数据。CLI 源码在 `D:\projects\clihub\em-crawler\`，底层爬虫在 `D:\projects\todo_list\0926\股票爬虫代码架构实现_东方财富\`。

## 前置条件

1. **Python**：爬虫依赖 Python 3.12 + `httpx / pandas / pyarrow / duckdb / pydantic`。
2. **Node.js**：CLI 是 Node.js 薄封装，需要 Node ≥ 18。
3. **环境变量**（首次使用配置一次）：
   ```
   EM_CRAWLER_PYTHON = D:\projects\todo_list\0926\股票爬虫代码架构实现_东方财富\runtime\python312\python.exe
   EM_CRAWLER_ROOT   = D:\projects\todo_list\0926\股票爬虫代码架构实现_东方财富
   ```

## 安装 CLI

```bash
cd D:\projects\clihub\em-crawler
npm install -g .
```

安装后得到 `em-crawler` 命令（Windows 下若 `node` 不在 PATH，用完整路径 `C:\Program Files\nodejs\node.exe` 调用）。

## 输出格式

所有命令在 stdout 输出 **JSON**：成功时为 Envelope 对象（或其数组），失败时错误信息写到 stderr 且 exit code 非 0。

Envelope 结构：
```json
{
  "source": "em",
  "entity_type": "quote_snapshot",
  "source_id": "...",
  "captured_at": "2026-09-29T10:18:29+08:00",
  "schema_version": "1.0",
  "payload": { ... }
}
```

## 命令速查

> 完整列表：`em-crawler list`

### 行情（em_market）

| 命令 | 说明 | 关键参数 |
| :-: | :-: | :-: |
| `em-crawler quote <code>` | 个股实时快照 | `--market SZ\|SH` |
| `em-crawler bar <code>` | K线 | `--market SZ --klt 101 --fqt 0 --lmt 5` |
| `em-crawler tick <code>` | 逐笔/分时 | `--market SZ --ndays 1` |
| `em-crawler orderbook <code>` | 五档盘口 | `--market SZ` |
| `em-crawler clist` | 板块/证券列表 | `--fs m:0+t:6 --page_size 50` |

`klt`：101=日K, 102=周K, 103=月K, 1=1分, 5=5分。`fqt`：0=不复权, 1=前复权, 2=后复权。

### 跨市场（em_cross）

| 命令 | 说明 |
| :-: | :-: |
| `em-crawler cross-snapshot <secid>` | 港股/美股等快照（secid 如 116.00700） |
| `em-crawler cross-bars <secid>` | 跨市场K线 |
| `em-crawler global-index` | 全球指数 |
| `em-crawler bond-list` | 可转债列表 |
| `em-crawler bj` | 北交所列表 |

### 资金（em_money）

| 命令 | 说明 |
| :-: | :-: |
| `em-crawler moneyflow <secid>` | 个股资金流向 |
| `em-crawler lhb` | 龙虎榜 `--date YYYY-MM-DD` |
| `em-crawler hsgt` | 沪深港通资金 |
| `em-crawler hsgt-quota` | 北向资金额度 |
| `em-crawler margin-sum` | 两融余额汇总 |
| `em-crawler block-trade <code>` | 大宗交易 |
| `em-crawler pledge <code>` | 股权质押 |
| `em-crawler holder-num <code>` | 股东户数 |

### 财务（em_finance）

| 命令 | 说明 |
| :-: | :-: |
| `em-crawler finance <code>` | 财务指标（默认） |
| `em-crawler balance <code>` | 资产负债表 |
| `em-crawler income <code>` | 利润表 |
| `em-crawler cashflow <code>` | 现金流量表 |
| `em-crawler forecast <code>` | 业绩预告 |
| `em-crawler express <code>` | 业绩快报 |
| `em-crawler dividend <code>` | 分红送配 |
| `em-crawler unlock <code>` | 限售解禁 |
| `em-crawler survey <code>` | 机构调研 |
| `em-crawler rating <code>` | 评级/盈利预测 |

### F10 公司资料（em_f10）

前缀 `f10-`，后跟模块名：`profile` / `shareholders` / `capital` / `analysis` / `concept` / `holding` / `event` / `history-name` / `executives` / `equity-incentive` / `financing` / `dividend-financing` / `industry-compare` / `related` / `valuation` / `foreign`。

```bash
em-crawler f10-profile 000001
em-crawler f10-shareholders 000001
em-crawler f10-concept 000001
```

### 资讯（em_news）

| 命令 | 说明 |
| :-: | :-: |
| `em-crawler announcements` | 公告列表 `--ann_type A` |
| `em-crawler announcement-content <art_code>` | 公告正文 |
| `em-crawler reports <code>` | 研报列表 |
| `em-crawler report-content <info_code>` | 研报正文 |
| `em-crawler flash-news` | 快讯 |
| `em-crawler news` | 财经新闻 |
| `em-crawler new-stock` | 新股 |
| `em-crawler report-pdf <info_code>` | 研报PDF |
| `em-crawler ipo-prospectus <code>` | IPO招股书 |

### 基金（em_fund）

| 命令 | 说明 |
| :-: | :-: |
| `em-crawler fund-codes` | 基金代码表 |
| `em-crawler fund-nav <code>` | 基金净值 |
| `em-crawler fund-holding <code>` | 基金持仓 `--topline 10` |
| `em-crawler fund-manager <code>` | 基金经理 |
| `em-crawler fund-rank` | 基金排行 |
| `em-crawler etf-lof` | ETF/LOF |
| `em-crawler fund-report-pdf <fund_code>` | 基金定期报告PDF |

### 宏观（em_macro）

| 命令 | 说明 |
| :-: | :-: |
| `em-crawler macro` | 国内宏观指标 |
| `em-crawler macro-overseas` | 海外宏观 |
| `em-crawler industry-index` | 行业板块 |
| `em-crawler concept-board` | 概念板块 |

国内指标 `--indicator` 可选值：`CPI` / `PPI` / `PMI` / `GDP` / `M2` / `LPR` / `FISCAL` / `HOUSE_PRICE` / `SHZR`(社融) / `FOREX_RESERVE`(外汇储备) / `ELECTRICITY`(用电量)。

海外经济体 `--economy`：`USANEW` / `EURONEW` / `CA` / `HK` 等。

### 股吧（em_guba）

| 命令 | 说明 |
| :-: | :-: |
| `em-crawler guba-posts <code>` | 帖子列表 `--page 1 --limit 20` |
| `em-crawler guba-post <code> --post_id <id>` | 帖子正文 |
| `em-crawler guba-comments <code> --post_id <id>` | 评论 |
| `em-crawler guba-rank` | 热度排行 |

### 工具（em_tools）

| 命令 | 说明 |
| :-: | :-: |
| `em-crawler diagnosis <code>` | 个股诊断评分（0-100） |
| `em-crawler fund-calc <fund_code>` | 基金定投计算器 `--monthly_amount 1000 --months 12 --annual_rate 0.08` |
| `em-crawler backtest` | 组合回测 `--weights '{"000001":0.5}' --period_returns '{"000001":0.1}'` |
| `em-crawler screener` | 选股器 |
| `em-crawler index-valuation` | 指数估值 |
| `em-crawler main-monitor` | 主力监控 |

## 使用示例

```bash
# 查平安银行快照
em-crawler quote 000001 --market SZ

# 查 CPI 最近 5 期
em-crawler macro --indicator CPI --page_size 5

# 查个股诊断评分
em-crawler diagnosis 000001

# 查北向资金
em-crawler hsgt --page_size 10

# 查基金净值
em-crawler fund-nav 161725 --page_size 5
```

## 注意事项

- **反爬限流**：`push2.eastmoney.com`（行情）偶发被限，返回连接关闭；datacenter 域名（财务/资金/F10/宏观）较稳定。限流时重试即可。
- **LPR 接口**：高频请求后可能返回空数据（东财服务端限流），代码内含 JSONP + 重试机制。
- **代码参数**：深市用 `SZ`，沪市用 `SH`；资金流等接口的 `secid` 格式为 `市场.代码`（如 `0.000001`）。
- **输出大小**：部分列表数据较大，CLI 已设置 50MB 缓冲区。
