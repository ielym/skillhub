---
name: em
description: 东方财富数据意图查询 CLI。当用户需要按数据意图查询东方财富数据时使用（如查某股票的收盘价/涨跌幅/成交量/换手率/市盈率/净利润/股东户数，或查涨停池/龙虎榜/宏观指标/基金净值等）。通过 `em <指标> <代码> [--口径]` 调用，按数据意图返回干净、口径明确的单一指标；同一数据多接口互为兜底。此 CLI 已取代旧的按模块抓取的 em-crawler。
version: 2.0.0
---

# em —— 使用导向的东方财富数据 CLI

按「数据意图」查询东方财富数据，而非按「东财模块」抓取。查一个指标，只返回一个干净、口径明确的值。

- CLI 源码：`/mnt/data01/projects/clihub/em/`（纯 Python，自包含，指向 `src/em` 包）
- 命令：`em`（`bin/em` 为入口脚本）

## 核心理念

| 概念 | 说明 |
| :-: | :-: |
| **指标 metric** | 一个数据意图（「收盘价」「涨跌幅」「净利润」「质押比例」…），全局唯一 ID |
| **口径 calibration** | 同一指标上「会改变数值语义」的维度：复权(前/后/不复权)、市盈率(静态/动态/TTM)、报告期等 |
| **多源兜底** | 同一指标可能来自多个东财接口，按优先级尝试，主源失败自动降级 |
| **结果纯净** | 查「涨跌幅」只返回涨跌幅，不带换手率/市值等无关字段 |

## 安装

```bash
cd /mnt/data01/projects/clihub/em
export PATH="$PATH:$PWD/bin"     # 或 ln -s "$PWD/bin/em" /usr/local/bin/em
```

依赖：`httpx`、`curl_cffi`（push2 行情 TLS 指纹必需）、`pyyaml`、`pycryptodome`（股吧人气榜解密）。

## 用法

```bash
em list                      # 列出全部指标
em list --group 行情          # 按分组列出
em <指标> <代码> [--口径...]   # 查单一指标
em batch <代码> 指标1,指标2    # 批量合并查询（同接口一次请求）
```

### 示例

```bash
em close 000001                                  # 收盘价
em close 000001 --trade_date 2025-06-30 --adjust qfq   # 历史前复权收盘价
em pct_change 000001                             # 涨跌幅
em pe 000001 --scope ttm|dynamic|static          # 市盈率（口径）
em turnover_rate 000001                          # 换手率
em net_profit 000001                             # 净利润
em eps 000001                                    # 每股收益
em holder_num 000001                             # 股东户数
em margin_balance 000001                         # 融资余额
em cpi                                           # CPI 序列
em guba_rank                                     # 股吧人气榜
em zt_pool                                       # 涨停池
em lhb --trade_date 2026-09-30                   # 龙虎榜
em fund_nav 161725                               # 基金净值
em batch 000001 close,high,low,pct_change,volume,turnover_rate,pe,pb
```

### 输出格式

```json
{
  "ok": true,
  "metric": "close",
  "calibration": {"adjust": "none"},
  "value": 11.57,
  "unit": "元",
  "as_of": "2026-09-30",
  "provider": "quote.kline",
  "fallback": false
}
```

- `value`：标量指标为单值；`series`/`table` 指标为数组。
- `calibration`：仅回显「本指标可变口径」；`fallback=true` 表示主源失败、兜底源命中。

## 指标目录（487 个，11 组）

| 组 | 内容（示例） |
| :-: | :-: |
| 行情 quote | price/close/open/high/low/pct_change/volume/amount/turnover_rate/pe/pb/市值/量比/kline/分时/盘口/行业板块/概念板块/全球指数/债券/北交所/涨停·跌停·炸板·昨日涨停池/港股/美股/英股/期货/期权/外汇/黄金/沪深港通标的 |
| 资金 capital | 主力·超大单·大单·中单·小单净流入、龙虎榜（含营业部维度）、融资·融券（多口径）、沪深港通（十大成交/机构/板块）、大宗交易（多口径）、质押、股东户数、账户统计 |
| 财务 finance | eps/bps/营收/净利润/roe/毛利率/每股经营现金流/同比、三表、业绩预告·快报、预约披露、分红、解禁、调研、评级 |
| 公司资料 f10 | 概况、十大股东、流通股东、股东户数变动、股本结构、主要指标、杜邦分析、概念、机构持股、重大事项、高管、股权激励、融资、分红融资、行业对比、关联公司、估值、港股/美股 F10 |
| 股东与高管 company | 高管持股变动、限售解禁、十大股东/流通股东分析、股东户数、主力持仓 |
| 资讯 news | 公告列表/正文、研报列表/正文、快讯、财经新闻、新股申购 |
| 基金 fund | 代码表、净值、持仓、经理、排行、ETF/LOF、定期报告 PDF |
| 宏观 macro | CPI/PPI/PMI/GDP/M2/LPR/财政/社融/外汇储备/用电量、海外宏观、行业指标库 |
| 股吧 guba | 帖子列表/正文/评论、人气榜 |
| 工具 tool | 个股诊断、互动易、主力监控、指数估值、定投计算、组合回测、财报图解 |
| 事件 event | 千股千评、港通持股、配股、回购、高管增减持、商誉、IPO 日历、股东大会、期货龙虎榜、关联交易、重大合同、委托理财、市场估值、股东持股、一致行动人、转融通、公司投资、并购重组、IPO 审核、停复牌 |

完整清单：`em list`。

## 口径（calibration）

- 行情复权：`--adjust none|qfq|hfq`（历史 K 线/收盘价）
- 市盈率：`--scope ttm|dynamic|static`（默认 TTM）
- 报告期：`--report_date YYYY-MM-DD`（财务类）
- 未显式给口径用默认值，结果 `calibration` 回显。

## 多源兜底与校验

- 每个指标在 `src/em/catalog/metrics.yaml` 声明有序 `providers` 链（主源 + 兜底源）。
- 引擎按优先级尝试主源，命中即停；主源异常/空值时降级兜底源并标记 `fallback=true`。
- 对「同口径多接口」数据（如换手率 = 快照 f168 vs K线）在 `equivalence` 字段登记交叉校验；口径不一致则拆分为两个指标。

## 环境变量

| 变量 | 说明 |
| :-: | :-: |
| `EM_HTTP_TIMEOUT` | 单请求超时秒数，默认 30；走隧道建议 40+ |
| `EM_PROXY` / `HTTP_PROXY` / `HTTPS_PROXY` | 代理（push2 行情域名需 IP 隧道） |
| `EM_VERIFY_TLS` | 置 0 关闭 TLS 校验 |

> `push2*.eastmoney.com`（快照/K线/榜单/资金流）有 TLS 指纹反爬，直连可能连接被断，需经 IP 隧道；`datacenter-web`（财务/资金/宏观/事件）、`push2ex`（涨停池）等直连即可。

## 架构

```
em (CLI 意图面)
 └─ engine/     查询引擎：分组规划(同接口合并) + 兜底链 + 字段裁剪
     ├─ catalog/   指标目录 metrics.yaml（意图→口径→多源→一致性断言）
     └─ providers/ 东财接口封装 quote/datacenter/fflow/news/fund/f10/guba/pool/macro/tools/cross/event
```

新增数据源渠道：`providers/` 加一个 endpoint 函数 + `metrics.yaml` 登记一个指标，即可被 `em` 查询，无需改引擎与 CLI。

> CLI 只负责查询返回，不承担存储功能。