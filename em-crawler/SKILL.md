---
name: em-crawler
description: 东方财富数据抓取 CLI（接口层，只取数不存储）。当需要抓取/查询东方财富数据时使用——行情（价格/K线/分时/盘口/涨跌停池/板块/港美股/期货/期权/外汇/黄金）、资金（主力净流入/龙虎榜/两融/沪深港通/大宗/质押/股东户数）、财务（三表/预告快报/分红/解禁/评级）、公司资料 F10、股东高管、资讯（公告/研报/快讯）、基金、宏观、股吧、工具、数据中心事件。命令 `em-crawler <指标> <代码> [--参数]`，共 506 个指标、11 个分组，全量清单见 references/metrics.md。原名 em，已重命名为 em-crawler。
version: 3.0.0
---

# em-crawler —— 东方财富数据抓取 CLI（接口层）

按「数据意图」取数：查一个指标，只返回一个干净、口径明确的值。**只负责取数，不负责存储。**

- CLI 源码：`/mnt/data01/projects/clihub/em-crawler/`（纯 Python，包名 `em_crawler`）
- 命令：`em-crawler`
- 全量指标参考：[references/metrics.md](references/metrics.md)（506 个指标 × 参数 × 口径 × 数据源链，自动生成）

> 命名沿革：原名 `em`，2026-10 重命名为 `em-crawler`（命令、包名、目录同步变更，旧命令 `em` 已移除）。

---

## 1. 命令

```bash
em-crawler list                              # 列出全部指标（JSON）
em-crawler list --group quote                # 按分组列出（分组键见 §5，用英文键，非中文组名）
em-crawler <指标> <参数值> [--参数/口径 ...]   # 查询单一指标
em-crawler batch <代码> 指标1,指标2,...        # 批量合并查询（同接口一次请求）
em-crawler help                              # 帮助
```

### 位置参数绑定规则

- 多数指标的位置参数是 `code`（证券代码），如 `em-crawler close 000001`。
- 当指标**唯一必填参数不是 `code`** 时，位置参数绑定到该必填参数，例如：
  - `em-crawler lhb 2026-09-30`（龙虎榜，必填 `trade_date`）
  - `em-crawler board_quote BK0475`（板块，必填 `board_code`）
- 其余参数一律用 `--key value` 传入；开关式参数写成 `--key` 即为 `true`。

---

## 2. 输出格式

三种 `kind`：

| kind | value 形态 | 示例指标 |
| :-: | :- | :- |
| `scalar` | 单值（数字/字符串） | close、pct_change、pe、net_profit |
| `series` | 对象数组（时间序列） | cpi、fund_nav、margin_history |
| `table` | 对象数组（清单/明细，字段即东财原始字段） | zt_pool、lhb、kline_daily、stock_list |

成功：

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

失败（**不会返回非零退出码**，一律 JSON）：

```json
{"ok": false, "error": "指标 pct_change 当前不可用（quote.snapshot:RuntimeError; quote.kline:空值）"}
```

- `calibration`：只回显「本指标可变的口径」；无口径的指标为 `{}`。
- `as_of`：结果里推断出的时间字段（`date`/`trade_date`/`report_date`/`nav_date`/`time`）；推断不到则回退 `--trade_date`。
- `provider`：实际命中的 endpoint；`fallback=true` 表示主源失败、由兜底源命中。
- `table`/`series` 的数组元素保留东财原始字段名（大小写混杂，如 `TRADE_DATE`/`DEAL_AMOUNT_RATIO`）。

---

## 3. 参数（38 个）

参数在指标定义中声明（`required: true` 为必填）。常用参数：

| 参数 | 含义 | 备注 |
| :- | :- | :- |
| `code` | 证券代码 | 193 个指标使用，其中 189 个必填；自动推断市场（6/9/5→沪，4/8/92→北，其余→深） |
| `trade_date` | 交易日 `YYYY-MM-DD` | 19 个指标使用 |
| `date_from` | 起始日期 | 7 个指标使用，5 个必填 |
| `end_date` | 结束日期 | 3 个指标 |
| `board_code` | 板块代码（`BK0475`） | 6 个指标，全部必填 |
| `secucode` | 带市场后缀代码（`600519.SH`） | 3 个指标，全部必填 |
| `secid` | 东财 secid（`1.600519`） | 2 个指标，全部必填 |
| `lmt` | K线条数上限 | 7 个指标 |
| `klt` | K线周期：101 日 / 102 周 / 103 月 / 5,15,30,60 分钟 | 1 个指标直传，多数内部固定 |
| `page_size` / `page` / `page_num` | 分页大小 / 页码 | 336 / 150 / 1 个指标 |
| `dept_code` | 营业部代码 | 2 个指标，必填 |
| `participant_code` | 参与方代码（期货/期权） | 2 个指标，必填 |
| `art_code` | 文章代码（研报） | 2 个指标，必填 |
| `info_code` | 公告代码 | 2 个指标，必填 |
| `post_id` | 股吧帖子 ID | 2 个指标，必填 |
| `indicator_id` | 宏观指标 id | 2 个指标 |
| `person_name` | 人名（基金经理等） | 1 个指标 |
| `underlying` | 期权标的 | 1 个指标，必填 |
| `weights` / `period_returns` | 组合权重 / 各期收益（回测计算器） | 各 1 个指标，必填 |
| `monthly_amount` / `months` / `annual_rate` | 月投金额 / 月数 / 年化（定投计算器） | 各 1 个指标 |
| `market` / `index` / `kind` / `stat` / `product` / `security_code` / `economy` / `ps` / `ndays` / `date` / `trade_market_code` | 各指标专用参数 | 详见 [references/metrics.md](references/metrics.md) |

> 完整对应关系（哪个指标用哪些参数、哪些必填）以 [references/metrics.md](references/metrics.md) 为准。

---

## 4. 口径（calibration）

口径是「会改变数值语义」的维度。用 `--key value` 传入，未传则用默认值并在结果 `calibration` 中回显。
**同一个口径键在不同指标上的取值集可能不同**，务必按指标查 [references/metrics.md](references/metrics.md)。

| 口径键 | 出现指标数 | 取值（并集） | 默认 | 说明 |
| :- | :-: | :- | :- | :- |
| `adjust` | 7 | `none` / `qfq` / `hfq` | `none` | 复权：不复权 / 前复权 / 后复权（历史 K 线、收盘价等有意义） |
| `scope` | 8 | TTM 组：`ttm`/`dynamic`/`static`；股东组：`free`/`all` | `ttm` / `free` | 市盈率口径；或十大股东「自由流通/全部」 |
| `market` | 8 | `all`/`sha`/`sza`/`kcb`/`cyb`/`bja`/`zxb`/`hb`/`sb`/`hs_a`/`sh_a`/`sz_a`/`bj_a`/`etf`/`kzz`/`sh`/`sz`/`bj`/`shibor`/`chibor`/`libor`/`hibor` | `all` | 市场范围（各指标取值集不同） |
| `mutual` | 7 | `north`/`south`/`sh`/`sz`/`hk_sh`/`hk_sz` | `north`/`south`/`sh` | 沪深港通方向/通道 |
| `cycle` | 7 | `1m`/`3m`/`6m`/`1y`；`1m`/`1q`/`1y` | `3m`/`1m` | 统计周期 |
| `stat` | 5 | `today`/`3d`/`5d`/`10d` | `today` | 统计区间 |
| `board` | 3 | `hy`/`gn`/`dy` | `hy` | 板块类型：行业/概念/地域 |
| `interval` | 4 | `3日`/`5日`/`10日`；`today`/`3d`/`5d`/`10d`；`today`/`d5`/`d20`/`hist` | `3日`/`today` | 区间 |
| `window` | 1 | `today`/`3d`/`5d`/`10d`/`30d` | `today` | 时间窗 |
| `period` | 2 | `1m`/`1q`/`6m`/`1y`/`2y` | `1m` | 期限 |
| `index` | 2 | 指数范围（各指标不同，如 `hs2`/`sh`/`sz`/`cyb`/`shb`/`szb`/`kcb`） | — | 指数范围 |
| `sec_type` | 1 | `a`/`b`/`fund`/`bond` | `a` | 证券类型 |
| `org_type` | 2 | `sec`/`bank`；`fund`/`qfii`/`ssf`/`broker`/`insurance`/`trust` | `sec`/`fund` | 机构类型 |
| `listing_state` | 2 | `free`/`all` | `free` | 上市状态 |
| `holder_kind` | 1 | `all`/`person`/`fund`/`qfii`/`ssf`/`broker`/`trust` | `all` | 股东类型 |
| `change` | 1 | `in`/`out`/`new` | `in` | 变动方向 |

---

## 5. 指标目录（506 个，11 组）

| 分组键 | 组名 | 指标数 | 内容（示例） |
| :-: | :-: | :-: | :- |
| `quote` | 行情 | 196 | price/close/open/high/low/pct_change/volume/amount/turnover_rate/pe/pb/市值/量比/kline/分时/盘口/行业板块/概念板块/全球指数/债券/北交所/涨跌停池/港美股/期货/期权/外汇/黄金/沪深港通标的 |
| `capital` | 资金 | 86 | 主力·超大单·大单·中单·小单净流入、龙虎榜（含营业部维度）、融资·融券（多口径）、沪深港通（十大成交/机构/板块）、大宗交易（多口径）、质押、股东户数、账户统计 |
| `finance` | 财务 | 20 | eps/bps/营收/净利润/roe/毛利率/每股经营现金流/同比、三表、业绩预告·快报、预约披露、分红、解禁、调研、评级 |
| `f10` | 公司资料 | 115 | 概况、十大股东、流通股东、股本结构、主要指标、杜邦分析、概念、机构持股、重大事项、高管、股权激励、融资、分红融资、行业对比、关联公司、估值、港股/美股 F10 |
| `company` | 股东与高管 | 12 | 高管持股变动、限售解禁、十大股东/流通股东分析、股东户数、主力持仓 |
| `news` | 资讯 | 10 | 公告列表/正文、研报列表/正文、快讯、财经新闻、新股申购 |
| `fund` | 基金 | 11 | 代码表、净值、持仓、经理、排行、ETF/LOF、定期报告 PDF |
| `macro` | 宏观 | 25 | CPI/PPI/PMI/GDP/M2/LPR/财政/社融/外汇储备/用电量、海外宏观、行业指标库 |
| `guba` | 股吧 | 4 | 帖子列表/正文/评论、人气榜 |
| `tool` | 工具 | 7 | 个股诊断、互动易、主力监控、指数估值、定投计算、组合回测、财报图解 |
| `event` | 数据中心事件 | 20 | 千股千评、港通持股、配股、回购、高管增减持、商誉、IPO 日历、股东大会、期货龙虎榜、关联交易、重大合同、委托理财、市场估值、股东持股、一致行动人、转融通、公司投资、并购重组、IPO 审核、停复牌 |

按 `kind` 分布：`table` 416、`series` 46、`scalar` 44。

---

## 6. 网络与反爬（重要）

| 域名 | 用途 | 直连 |
| :- | :- | :- |
| `push2.eastmoney.com` | 实时快照、盘口、排行榜 | ✗ TLS 指纹反爬，连接会被重置 → **需走 IP 隧道代理** |
| `push2his.eastmoney.com` | 历史 K 线（日/周/月/分钟）、分时 | ✓ 可直连 |
| `push2ex.eastmoney.com` | 涨停池等 | ✓ 可直连 |
| `datacenter-web.eastmoney.com` | 财务/资金/宏观/事件/龙虎榜 | ✓ 可直连 |
| 其他（基金/股吧/资讯/F10） | — | 多数可直连，股吧人气榜需 `pycryptodome` 解密 |

需要走代理时（配合 `ip-tunnel` skill 取隧道配置）：

```bash
EM_PROXY="http://<隧道地址>:<端口>" em-crawler price 000001
```

环境变量：

| 变量 | 说明 |
| :- | :- |
| `EM_HTTP_TIMEOUT` | 单请求超时秒数，默认 30；走隧道建议 40+ |
| `EM_PROXY` / `HTTP_PROXY` / `HTTPS_PROXY` | 代理 |
| `EM_VERIFY_TLS` | 置 `0` 关闭 TLS 校验 |

---

## 7. 已知问题（S0 实盘核验，2026-10-07）

1. **`quote.snapshot` 全部失败**：`push2.eastmoney.com` TLS 指纹反爬，未配代理时报
   `RuntimeError: request failed after 3 retries ... Connection closed abruptly`。
   影响所有以 snapshot 为主源的指标（`price`/`pe`/`pb`/市值/量比/`main_net_inflow` 等）。
   **→ 需配置 IP 隧道代理后重试。**
2. **`amount`/`volume`/`pct_change`/`turnover_rate` 连兜底也失败**：
   这些指标在 `metrics.yaml` 中未声明 `trade_date` 参数，但 provider 参数里写了 `end: trade_date`；
   引擎 `_resolve_args` 对「不在上下文中的字符串」按字面量传入，于是把字符串 `"trade_date"` 当作
   `end` 传给 K 线接口 → 返回空 → 报 `quote.kline:空值`。
   对比 `close`/`open`/`high`/`low` 已声明 `trade_date: {required: false}`，因此正常。
   **→ 属既有缺陷（非本次重命名引入），修复方式是给这些指标补 `trade_date` 可选参数或改引擎语义；S0 先记录不修。**
3. **`batch` 会被单个指标拖垮**：`engine.batch` 中任一指标主源失败触发 `_fallback_query` 抛出时，
   整批返回 `{"ok": false, "error": ...}`（实测 `batch 000001 close,high,low,pct_change,turnover_rate` 整体失败）。
   **→ 批量查询前先用单个指标验证可用性。**
4. **两个指标上游已下线（保留定义，调用会明确报错）**：
   - `shzr`（社会融资规模）、`electricity`（全社会用电量）—— 上游 `macro.domestic` 已不再提供，
     东财页面返回占位页、`cjsj` 菜单已移除、穷举 `RPT_ECONOMY_*` 均报"报表配置不存在"。
   - 二者在 `metrics.yaml` 中标记 `status: offline`，调用时报
     `指标 shzr 上游已下线（东财不再提供该指标），定义保留仅供查阅`（而非含糊的"空值"）。
   - **落表脚本应跳过这两个指标**；`references/metrics.md` 中其名称带 ⚠️上游已下线 标记。

---

## 8. 架构与扩展

```
em-crawler (CLI 意图面)
 ├─ cli.py        命令行入口（list / 单指标 / batch / help）
 ├─ engine/       查询引擎：分组规划(同接口合并) + 兜底链 + 字段提取裁剪
 ├─ catalog/      指标目录 metrics.yaml（意图 → 参数 → 口径 → 多源 provider 链 → 一致性断言）
 └─ providers/    72 个底层 endpoint（quote/datacenter/fflow/news/fund/f10/guba/pool/macro/tools/cross/event/extended）
```

- 多源兜底：`providers` 为有序链，按 priority 升序尝试，命中即停；主源异常/空值时降级并置 `fallback=true`。
- 扩展方式：`providers/` 加一个 endpoint 函数 + `metrics.yaml` 登记一个指标，无需改引擎与 CLI。
- 重新生成指标参考：`python3 /mnt/data01/projects/clihub/em-crawler/tools/gen_metrics_reference.py <输出路径>`。

---

## 9. 典型用法

```bash
em-crawler close 000001                                       # 收盘价
em-crawler close 000001 --trade_date 2025-06-30 --adjust qfq   # 历史前复权收盘价
em-crawler kline_daily 000001                                  # 日 K 全序列
em-crawler zt_pool                                             # 涨停池
em-crawler lhb 2026-09-30                                      # 龙虎榜（按日）
em-crawler cpi                                                 # CPI 序列
em-crawler fund_nav 161725                                     # 基金净值
em-crawler guba_rank                                           # 股吧人气榜
em-crawler batch 000001 close,high,low,volume                  # 批量（先用单指标确认可用）
```

---

## 10. 边界

- **只取数，不存储**。落盘、调度、历史回溯由外部脚本负责（见 `todo_list/1007/数据存储架构实现/`）。
- 无状态：不写本地文件、不建缓存；相同请求重复调用结果一致（除实时字段）。
- 失败即 JSON 错误，不抛栈、不中断批处理脚本（脚本需自行判断 `ok` 字段）。
