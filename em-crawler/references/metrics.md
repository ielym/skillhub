# em-crawler 指标全量参考（506 个）

> 本文件由 `clihub/em-crawler/tools/gen_metrics_reference.py` 从 `src/em_crawler/catalog/metrics.yaml` 自动生成，请勿手工编辑。

## 阅读说明

| 列 | 含义 |
| :- | :- |
| 指标 | 调用时的指标 id：`em-crawler <指标> <参数值>` |
| kind | `scalar` 单值 / `series` 序列 / `table` 清单 |
| 参数 | 该指标接受的参数；带 `*` 为必填。除 `code` 外的唯一必填参数可用位置参数传入 |
| 口径 | 可传 `--<key> <value>`，括号内为默认值 |
| 数据源链 | 按优先级升序，命中即停；`⤵` 标记兜底源，命中时结果 `fallback=true` |

## 分组索引

| 分组键 | 组名 | 指标数 |
| :- | :- | :-: |
| `quote` | 行情 | 196 |
| `capital` | 资金 | 86 |
| `finance` | 财务 | 20 |
| `f10` | 公司资料 | 115 |
| `company` | 股东与高管 | 12 |
| `news` | 资讯 | 10 |
| `fund` | 基金 | 11 |
| `macro` | 宏观 | 25 |
| `guba` | 股吧 | 4 |
| `tool` | 工具 | 7 |
| `event` | 数据中心事件 | 20 |
| — | **合计** | **506** |

## 行情 `quote`（196 个）

| 指标 | 名称 | kind | 单位 | 参数 | 口径 | 数据源链 |
| :- | :- | :-: | :-: | :- | :- | :- |
| `ab_comparison`<br>`AB股比价/AB比价/ab_comparison` | AB股比价 | table | - | page_size, page | - | quote.listed(name=ab_comparison,page_size=page_size,page=page)[all] |
| `ab_comparison_sh`<br>`AB股比价(沪)/ab_comparison_sh` | AB股比价(沪) | table | - | page_size, page | - | quote.listed(name=ab_comparison_sh,page_size=page_size,page=page)[all] |
| `ab_comparison_sz`<br>`AB股比价(深)/ab_comparison_sz` | AB股比价(深) | table | - | page_size, page | - | quote.listed(name=ab_comparison_sz,page_size=page_size,page=page)[all] |
| `ah_comparison`<br>`AH股比价/AH比价/A+H/ah_comparison` | AH股比价 | table | - | page_size, page | - | quote.listed(name=ah_comparison,page_size=page_size,page=page)[all] |
| `amount`<br>`成交额/turnover_amount` | 成交额 | scalar | 元 | code* | - | quote.snapshot(code=code).amount → quote.kline(code=code,klt=101,fqt=0,lmt=80,end=trade_date).amount⤵ |
| `amplitude`<br>`振幅` | 振幅 | scalar | % | code* | - | quote.snapshot(code=code).amplitude |
| `bj_stock`<br>`北交所/北证` | 北交所股票列表 | table | - | page_size | - | cross.bj(page_size=page_size)[all] |
| `bond_bj_enterprise`<br>`北企债/bond_bj_enterprise` | 北企债 | table | - | page_size, page | - | quote.listed(name=bond_bj_enterprise,page_size=page_size,page=page)[all] |
| `bond_index_list`<br>`债券指数/bond_index_list` | 债券指数 | table | - | page_size, page | - | quote.listed(name=bond_index_list,page_size=page_size,page=page)[all] |
| `bond_list`<br>`债券/bond` | 债券列表 | table | - | page_size | - | cross.bond(page_size=page_size)[all] |
| `bond_sh_convertible`<br>`沪转债/bond_sh_convertible` | 沪转债 | table | - | page_size, page | - | quote.listed(name=bond_sh_convertible,page_size=page_size,page=page)[all] |
| `bond_sh_enterprise`<br>`沪企债/bond_sh_enterprise` | 沪企债 | table | - | page_size, page | - | quote.listed(name=bond_sh_enterprise,page_size=page_size,page=page)[all] |
| `bond_sh_treasury`<br>`沪国债/bond_sh_treasury` | 沪国债 | table | - | page_size, page | - | quote.listed(name=bond_sh_treasury,page_size=page_size,page=page)[all] |
| `bond_spot_list_bj`<br>`北京债券现券/京债券现券/bond_spot_list_bj` | 北京债券现券 | table | - | page_size, page | - | quote.listed(name=bond_spot_list_bj,page_size=page_size,page=page)[all] |
| `bond_spot_list_sh`<br>`上海债券现券/沪债券现券/bond_spot_list_sh` | 上海债券现券 | table | - | page_size, page | - | quote.listed(name=bond_spot_list_sh,page_size=page_size,page=page)[all] |
| `bond_spot_list_sz`<br>`深圳债券现券/深债券现券/bond_spot_list_sz` | 深圳债券现券 | table | - | page_size, page | - | quote.listed(name=bond_spot_list_sz,page_size=page_size,page=page)[all] |
| `bond_sz_convertible`<br>`深转债/bond_sz_convertible` | 深转债 | table | - | page_size, page | - | quote.listed(name=bond_sz_convertible,page_size=page_size,page=page)[all] |
| `bond_sz_enterprise`<br>`深企债/bond_sz_enterprise` | 深企债 | table | - | page_size, page | - | quote.listed(name=bond_sz_enterprise,page_size=page_size,page=page)[all] |
| `bond_sz_treasury`<br>`深国债/bond_sz_treasury` | 深国债 | table | - | page_size, page | - | quote.listed(name=bond_sz_treasury,page_size=page_size,page=page)[all] |
| `ch_gdr_list`<br>`瑞士GDR/GDR/瑞士GDR列表/ch_gdr_list` | 瑞士GDR | table | - | page_size, page | - | quote.listed(name=ch_gdr_list,page_size=page_size,page=page)[all] |
| `change`<br>`涨跌/change_amt` | 涨跌额 | scalar | 元 | code* | - | quote.snapshot(code=code).change → quote.kline(code=code,klt=101,fqt=0,lmt=80,end=trade_date).change⤵ |
| `close`<br>`收盘/close_price/收` | 收盘价 | scalar | 元 | code*, trade_date | adjust=none|qfq|hfq（默认 none） | quote.kline(code=code,klt=101,fqt=fqt,lmt=80,end=trade_date).close → quote.snapshot(code=code).price⤵ |
| `concept_board`<br>`概念板块/概念` | 概念板块行情 | table | - | page_size | - | quote.clist(fs=m:90+t:3,page_size=page_size)[all] |
| `convertible_bond_comparison`<br>`可转债比价表/可转债比价/可转债全表/convertible_bond_comparison` | 可转债比价表 | table | - | page_size, page | - | quote.listed(name=convertible_bond_comparison,page_size=page_size,page=page)[all] |
| `cx_pool`<br>`次新股/次新股池/cx_pool` | 次新股池 | table | - | trade_date, page_size | - | pool.get(kind=cx,trade_date=trade_date,page_size=page_size)[all] |
| `delisted_stock_list`<br>`两网及退市/退市股票/两网退市/delisted_stock_list` | 两网及退市 | table | - | page_size, page | - | quote.listed(name=delisted_stock_list,page_size=page_size,page=page)[all] |
| `dt_pool`<br>`跌停池/跌停板` | 跌停池 | table | - | trade_date, page_size | - | pool.get(kind=dt,trade_date=trade_date,page_size=page_size)[all] |
| `etf_list`<br>`ETF基金行情/ETF列表/全部ETF/etf_list` | ETF基金行情 | table | - | page_size, page | - | quote.listed(name=etf_list,page_size=page_size,page=page)[all] |
| `float_mv`<br>`流通市值/float_cap` | 流通市值 | scalar | 元 | code* | - | quote.snapshot(code=code).float_mv |
| `forex_bank_abc`<br>`农业银行外汇牌价/农行外汇牌价/forex_bank_abc` | 农业银行外汇牌价 | table | - | page_size, page | - | quote.listed(name=forex_bank_abc,page_size=page_size,page=page)[all] |
| `forex_bank_bcm`<br>`交通银行外汇牌价/交行外汇牌价/forex_bank_bcm` | 交通银行外汇牌价 | table | - | page_size, page | - | quote.listed(name=forex_bank_bcm,page_size=page_size,page=page)[all] |
| `forex_bank_boc`<br>`中国银行外汇牌价/中行外汇牌价/forex_bank_boc` | 中国银行外汇牌价 | table | - | page_size, page | - | quote.listed(name=forex_bank_boc,page_size=page_size,page=page)[all] |
| `forex_bank_ccb`<br>`建设银行外汇牌价/建行外汇牌价/forex_bank_ccb` | 建设银行外汇牌价 | table | - | page_size, page | - | quote.listed(name=forex_bank_ccb,page_size=page_size,page=page)[all] |
| `forex_bank_cmb`<br>`招商银行外汇牌价/招行外汇牌价/forex_bank_cmb` | 招商银行外汇牌价 | table | - | page_size, page | - | quote.listed(name=forex_bank_cmb,page_size=page_size,page=page)[all] |
| `forex_bank_icbc`<br>`工商银行外汇牌价/工行外汇牌价/forex_bank_icbc` | 工商银行外汇牌价 | table | - | page_size, page | - | quote.listed(name=forex_bank_icbc,page_size=page_size,page=page)[all] |
| `forex_basic`<br>`基本汇率/forex_basic` | 基本汇率 | table | - | page_size, page | - | quote.listed(name=forex_basic,page_size=page_size,page=page)[all] |
| `forex_cnh`<br>`离岸人民币/forex_cnh` | 离岸人民币 | table | - | page_size, page | - | quote.listed(name=forex_cnh,page_size=page_size,page=page)[all] |
| `forex_cny`<br>`人民币品种/forex_cny` | 人民币品种 | table | - | page_size, page | - | quote.listed(name=forex_cny,page_size=page_size,page=page)[all] |
| `forex_cnyc`<br>`人民币中间价/forex_cnyc` | 人民币中间价 | table | - | page_size, page | - | quote.listed(name=forex_cnyc,page_size=page_size,page=page)[all] |
| `forex_cross`<br>`交叉汇率/forex_cross` | 交叉汇率 | table | - | page_size, page | - | quote.listed(name=forex_cross,page_size=page_size,page=page)[all] |
| `forex_list`<br>`所有汇率/forex_list` | 所有汇率 | table | - | page_size, page | - | quote.listed(name=forex_list,page_size=page_size,page=page)[all] |
| `futures_avg_price`<br>`期货持仓均价/持仓均价/futures_avg_price` | 期货持仓均价 | table | - | page_size | - | dc.get(report=RPT_FUTU_AVGPPAL,sort_columns=TRADE_DATE,sort_types=-1,page_size=page_size)[all] |
| `futures_cffex`<br>`中金所期货/中金所/futures_cffex` | 中金所期货 | table | - | page_size, page | - | quote.listed(name=futures_cffex,page_size=page_size,page=page)[all] |
| `futures_contract`<br>`期货合约/期货品种/合约列表/futures_contract` | 期货品种合约 | table | - | market*, product, page_size, page | - | quote.futures_contracts(market=market,product=product,page_size=page_size,page=page)[all] |
| `futures_czce`<br>`郑商所期货/郑商所/futures_czce` | 郑商所期货 | table | - | page_size, page | - | quote.listed(name=futures_czce,page_size=page_size,page=page)[all] |
| `futures_dce`<br>`大商所期货/大商所/futures_dce` | 大商所期货 | table | - | page_size, page | - | quote.listed(name=futures_dce,page_size=page_size,page=page)[all] |
| `futures_gfex`<br>`广期所期货/广期所/futures_gfex` | 广期所期货 | table | - | page_size, page | - | quote.listed(name=futures_gfex,page_size=page_size,page=page)[all] |
| `futures_ine`<br>`上期能源期货/上期能源/futures_ine` | 上期能源期货 | table | - | page_size, page | - | quote.listed(name=futures_ine,page_size=page_size,page=page)[all] |
| `futures_main_contract`<br>`期货主力合约/主力合约/期货合约列表/futures_main_contract` | 期货主力合约列表 | table | - | page_size, page | - | dc.get(report=RPT_FUTU_POSITIONCODE,sort_columns=SECURITY_CODE,sort_types=1,page_size=page_size,page=page)[all] |
| `futures_org`<br>`期货机构/期货公司列表/futures_org` | 期货机构列表 | table | - | page_size | - | dc.get(report=RPT_FUTU_FUTUREORGLIST,page_size=page_size)[all] |
| `futures_position_rank`<br>`期货成交持仓/期货持仓排名/期货成交排名/futures_position_rank` | 期货成交持仓排名 | table | - | security_code, trade_market_code, page_size | - | ext.futures_position_rank(security_code=security_code,trade_market_code=trade_market_code,page_size=page_size)[all] |
| `futures_shfe`<br>`上期所期货/上期所/futures_shfe` | 上期所期货 | table | - | page_size, page | - | quote.listed(name=futures_shfe,page_size=page_size,page=page)[all] |
| `futures_stock_data`<br>`期货库存/库存数据/交易所库存/futures_stock_data` | 期货库存数据 | table | - | page_size | - | dc.get(report=RPT_FUTU_STOCKDATA,sort_columns=TRADE_DATE,sort_types=-1,page_size=page_size)[all] |
| `global_index`<br>`全球指数/国际指数` | 全球指数 | table | - | page_size | - | cross.global_index(page_size=page_size)[all] |
| `gold_global_futures`<br>`国际贵金属期货/外盘贵金属/CME贵金属/gold_global_futures` | 国际贵金属期货 | table | - | page_size, page | - | quote.listed(name=gold_global_futures,page_size=page_size,page=page)[all] |
| `gold_global_spot`<br>`国际贵金属现货/gold_global_spot` | 国际贵金属现货 | table | - | page_size, page | - | quote.listed(name=gold_global_spot,page_size=page_size,page=page)[all] |
| `gold_sh_futures`<br>`上海黄金期货/gold_sh_futures` | 上海黄金期货 | table | - | page_size, page | - | quote.listed(name=gold_sh_futures,page_size=page_size,page=page)[all] |
| `gold_sh_spot`<br>`上海黄金现货/沪金现货/gold_sh_spot` | 上海黄金现货 | table | - | page_size, page | - | quote.listed(name=gold_sh_spot,page_size=page_size,page=page)[all] |
| `high`<br>`最高/high_price` | 最高价 | scalar | 元 | code*, trade_date | adjust=none|qfq|hfq（默认 none） | quote.snapshot(code=code).high → quote.kline(code=code,klt=101,fqt=fqt,lmt=80,end=trade_date).high⤵ |
| `hk_adr_list`<br>`港股ADR/hk_adr_list` | 港股ADR | table | - | page_size, page | - | quote.listed(name=hk_adr_list,page_size=page_size,page=page)[all] |
| `hk_blue_chip_list`<br>`港股蓝筹股/hk_blue_chip_list` | 港股蓝筹股 | table | - | page_size, page | - | quote.listed(name=hk_blue_chip_list,page_size=page_size,page=page)[all] |
| `hk_cbbc_list`<br>`港股牛熊证/牛熊证/hk_cbbc_list` | 港股牛熊证 | table | - | page_size, page | - | quote.listed(name=hk_cbbc_list,page_size=page_size,page=page)[all] |
| `hk_gem`<br>`港股创业板/hk_gem` | 港股创业板 | table | - | page_size, page | - | quote.listed(name=hk_gem,page_size=page_size,page=page)[all] |
| `hk_hsgt_etf_all`<br>`港股通ETF(沪深合计)/hk_hsgt_etf_all` | 港股通ETF(沪深合计) | table | - | page_size, page | - | quote.listed(name=hk_hsgt_etf_all,page_size=page_size,page=page)[all] |
| `hk_hsgt_etf_sh`<br>`港股通(沪)ETF/hk_hsgt_etf_sh` | 港股通(沪)ETF | table | - | page_size, page | - | quote.listed(name=hk_hsgt_etf_sh,page_size=page_size,page=page)[all] |
| `hk_hsgt_etf_sz`<br>`港股通(深)ETF/hk_hsgt_etf_sz` | 港股通(深)ETF | table | - | page_size, page | - | quote.listed(name=hk_hsgt_etf_sz,page_size=page_size,page=page)[all] |
| `hk_hsgt_list_all`<br>`港股通标的(沪深合计)/hk_hsgt_list_all` | 港股通标的(沪深合计) | table | - | page_size, page | - | quote.listed(name=hk_hsgt_list_all,page_size=page_size,page=page)[all] |
| `hk_hsgt_list_sh`<br>`港股通(沪)标的/港股通沪标的/hk_hsgt_list_sh` | 港股通(沪)标的 | table | - | page_size, page | - | quote.listed(name=hk_hsgt_list_sh,page_size=page_size,page=page)[all] |
| `hk_hsgt_list_sz`<br>`港股通(深)标的/港股通深标的/hk_hsgt_list_sz` | 港股通(深)标的 | table | - | page_size, page | - | quote.listed(name=hk_hsgt_list_sz,page_size=page_size,page=page)[all] |
| `hk_hsics_large`<br>`恒生综合大型股/hk_hsics_large` | 恒生综合大型股 | table | - | page_size, page | - | quote.listed(name=hk_hsics_large,page_size=page_size,page=page)[all] |
| `hk_hsics_mid`<br>`恒生综合中型股/hk_hsics_mid` | 恒生综合中型股 | table | - | page_size, page | - | quote.listed(name=hk_hsics_mid,page_size=page_size,page=page)[all] |
| `hk_index_list`<br>`香港指数/hk_index_list` | 香港指数 | table | - | page_size, page | - | quote.listed(name=hk_index_list,page_size=page_size,page=page)[all] |
| `hk_known_list`<br>`知名港股/知名港股列表/hk_known_list` | 知名港股 | table | - | page_size, page | - | quote.listed(name=hk_known_list,page_size=page_size,page=page)[all] |
| `hk_main_board`<br>`港股主板/hk_main_board` | 港股主板 | table | - | page_size, page | - | quote.listed(name=hk_main_board,page_size=page_size,page=page)[all] |
| `hk_red_chip_components`<br>`红筹成分股/hk_red_chip_components` | 红筹成分股 | table | - | page_size, page | - | quote.listed(name=hk_red_chip_components,page_size=page_size,page=page)[all] |
| `hk_red_chip_list`<br>`港股红筹股/hk_red_chip_list` | 港股红筹股 | table | - | page_size, page | - | quote.listed(name=hk_red_chip_list,page_size=page_size,page=page)[all] |
| `hk_rmb_stock_list`<br>`人民币交易港股/hk_rmb_stock_list` | 人民币交易港股 | table | - | page_size, page | - | quote.listed(name=hk_rmb_stock_list,page_size=page_size,page=page)[all] |
| `hk_soe_components`<br>`国企成分股/hk_soe_components` | 国企成分股 | table | - | page_size, page | - | quote.listed(name=hk_soe_components,page_size=page_size,page=page)[all] |
| `hk_soe_list`<br>`港股国企股/hk_soe_list` | 港股国企股 | table | - | page_size, page | - | quote.listed(name=hk_soe_list,page_size=page_size,page=page)[all] |
| `hk_stock_list`<br>`全部港股/港股列表/hk_stock_list` | 全部港股 | table | - | page_size, page | - | quote.listed(name=hk_stock_list,page_size=page_size,page=page)[all] |
| `hk_warrant_list`<br>`港股窝轮/窝轮/认股证/hk_warrant_list` | 港股窝轮 | table | - | page_size, page | - | quote.listed(name=hk_warrant_list,page_size=page_size,page=page)[all] |
| `hsgt_etf_sh`<br>`沪股通ETF/沪股通ETF列表/hsgt_etf_sh` | 沪股通ETF | table | - | page_size, page | - | quote.listed(name=hsgt_etf_sh,page_size=page_size,page=page)[all] |
| `hsgt_etf_sz`<br>`深股通ETF/hsgt_etf_sz` | 深股通ETF | table | - | page_size, page | - | quote.listed(name=hsgt_etf_sz,page_size=page_size,page=page)[all] |
| `hsgt_realtime_flow`<br>`沪深港通实时资金流/北向资金实时/沪深港通额度/沪股通资金/深股通资金/hsgt_realtime_flow` | 沪深港通实时资金流 | table | - | - | - | quote.kamt[all] |
| `hsgt_realtime_flow_history`<br>`沪深港通资金流历史/北向资金历史/沪深港通历史/hsgt_realtime_flow_history` | 沪深港通资金流历史 | series | - | lmt | - | quote.kamt_kline(lmt=lmt)[all] |
| `hsgt_stock_list_sh`<br>`沪股通标的/hsgt_stock_list_sh` | 沪股通标的 | table | - | page_size, page | - | quote.listed(name=hsgt_stock_list_sh,page_size=page_size,page=page)[all] |
| `hsgt_stock_list_sz`<br>`深股通标的/hsgt_stock_list_sz` | 深股通标的 | table | - | page_size, page | - | quote.listed(name=hsgt_stock_list_sz,page_size=page_size,page=page)[all] |
| `index_components`<br>`指数成分股/成分股/指数成分/index_components` | 指数成分股 | table | - | page_size, page | - | quote.listed(name=index_components,page_size=page_size,page=page)[all] |
| `index_list_sh`<br>`上证系列指数/上证指数列表/index_list_sh` | 上证系列指数 | table | - | page_size, page | - | quote.listed(name=index_list_sh,page_size=page_size,page=page)[all] |
| `index_list_sz`<br>`深证系列指数/深证指数列表/index_list_sz` | 深证系列指数 | table | - | page_size, page | - | quote.listed(name=index_list_sz,page_size=page_size,page=page)[all] |
| `index_snapshot`<br>`市场总貌/大盘指数快照/上证指数快照/深证成指快照/创业板指快照/沪深300快照/index_snapshot` | 市场总貌指数快照 | table | - | index | - | quote.index_snapshot(index=index)[all] |
| `index_zzzs`<br>`中证系列指数/中证指数/index_zzzs` | 中证系列指数 | table | - | page_size, page | - | quote.listed(name=index_zzzs,page_size=page_size,page=page)[all] |
| `industry_board_1`<br>`行业板块(一级)/东财一级行业/industry_board_1` | 行业板块(一级) | table | - | page_size, page | - | quote.listed(name=industry_board_1,page_size=page_size,page=page)[all] |
| `industry_board_2`<br>`行业板块(二级)/东财二级行业/industry_board_2` | 行业板块(二级) | table | - | page_size, page | - | quote.listed(name=industry_board_2,page_size=page_size,page=page)[all] |
| `industry_board_3`<br>`行业板块(三级)/东财三级行业/industry_board_3` | 行业板块(三级) | table | - | page_size, page | - | quote.listed(name=industry_board_3,page_size=page_size,page=page)[all] |
| `industry_index`<br>`行业板块/行业指数` | 行业板块行情 | table | - | page_size | - | quote.clist(fs=m:90+t:2,page_size=page_size)[all] |
| `kline_daily`<br>`日K/kline/K线` | 日K线 | series | - | code*, trade_date | adjust=none|qfq|hfq（默认 none） | quote.kline(code=code,klt=101,fqt=fqt,lmt=120,end=trade_date)[all] |
| `kline_min15`<br>`15分钟K线/十五分钟K线/kline_min15` | 15分钟K线 | series | - | code*, lmt | - | quote.kline(code=code,klt=15,lmt=lmt)[all] |
| `kline_min30`<br>`30分钟K线/三十分钟K线/kline_min30` | 30分钟K线 | series | - | code*, lmt | - | quote.kline(code=code,klt=30,lmt=lmt)[all] |
| `kline_min5`<br>`5分钟K线/五分钟K线/kline_min5` | 5分钟K线 | series | - | code*, lmt | - | quote.kline(code=code,klt=5,lmt=lmt)[all] |
| `kline_min60`<br>`60分钟K线/六十分钟K线/kline_min60` | 60分钟K线 | series | - | code*, lmt | - | quote.kline(code=code,klt=60,lmt=lmt)[all] |
| `kline_monthly`<br>`月K/kline_m` | 月K线 | series | - | code* | adjust=none|qfq|hfq（默认 none） | quote.kline(code=code,klt=103,fqt=fqt,lmt=120)[all] |
| `kline_weekly`<br>`周K/kline_w` | 周K线 | series | - | code* | adjust=none|qfq|hfq（默认 none） | quote.kline(code=code,klt=102,fqt=fqt,lmt=120)[all] |
| `large_net_inflow`<br>`大单净额` | 大单净流入 | scalar | 元 | code* | - | quote.snapshot(code=code).large_net_inflow |
| `limit_down`<br>`跌停价` | 跌停价 | scalar | 元 | code* | - | quote.snapshot(code=code).limit_down |
| `limit_up`<br>`涨停价/涨停` | 涨停价 | scalar | 元 | code* | - | quote.snapshot(code=code).limit_up |
| `lof_list`<br>`LOF基金行情/LOF列表/lof_list` | LOF基金行情 | table | - | page_size, page | - | quote.listed(name=lof_list,page_size=page_size,page=page)[all] |
| `low`<br>`最低/low_price` | 最低价 | scalar | 元 | code*, trade_date | adjust=none|qfq|hfq（默认 none） | quote.snapshot(code=code).low → quote.kline(code=code,klt=101,fqt=fqt,lmt=80,end=trade_date).low⤵ |
| `main_net_inflow`<br>`主力净额/main_net` | 主力净流入 | scalar | 元 | code* | - | quote.snapshot(code=code).main_net_inflow |
| `market_breadth`<br>`涨跌家数/市场涨跌家数/market_breadth` | 市场涨跌家数 | table | - | index | - | quote.market_breadth(index=index) |
| `market_breadth_all`<br>`主要指数涨跌家数/market_breadth_all` | 市场涨跌家数(主要指数) | table | - | - | - | quote.market_breadth(index=all)[all] |
| `market_down_count`<br>`下跌家数/跌家数/market_down_count` | 市场下跌家数 | scalar | - | index | - | quote.market_breadth(index=index).down_count |
| `market_flat_count`<br>`平盘家数/平家数/market_flat_count` | 市场平盘家数 | scalar | - | index | - | quote.market_breadth(index=index).flat_count |
| `market_up_count`<br>`上涨家数/涨家数/market_up_count` | 市场上涨家数 | scalar | - | index | - | quote.market_breadth(index=index).up_count |
| `mid_net_inflow`<br>`中单净额` | 中单净流入 | scalar | 元 | code* | - | quote.snapshot(code=code).mid_net_inflow |
| `neeq_basic`<br>`新三板基础层/neeq_basic` | 新三板基础层 | table | - | page_size, page | - | quote.listed(name=neeq_basic,page_size=page_size,page=page)[all] |
| `neeq_bidding`<br>`新三板集合竞价/neeq_bidding` | 新三板集合竞价 | table | - | page_size, page | - | quote.listed(name=neeq_bidding,page_size=page_size,page=page)[all] |
| `neeq_innovate`<br>`新三板创新层/neeq_innovate` | 新三板创新层 | table | - | page_size, page | - | quote.listed(name=neeq_innovate,page_size=page_size,page=page)[all] |
| `neeq_marketmaking`<br>`新三板做市/neeq_marketmaking` | 新三板做市 | table | - | page_size, page | - | quote.listed(name=neeq_marketmaking,page_size=page_size,page=page)[all] |
| `neeq_stock_list`<br>`新三板/股转系统/三板/neeq_stock_list` | 新三板 | table | - | page_size, page | - | quote.listed(name=neeq_stock_list,page_size=page_size,page=page)[all] |
| `new_stock_list`<br>`新股/新股列表/次新股/new_stock_list` | 新股 | table | - | page_size, page | - | quote.listed(name=new_stock_list,page_size=page_size,page=page)[all] |
| `open`<br>`开盘/open_price` | 开盘价 | scalar | 元 | code*, trade_date | adjust=none|qfq|hfq（默认 none） | quote.snapshot(code=code).open → quote.kline(code=code,klt=101,fqt=fqt,lmt=80,end=trade_date).open⤵ |
| `option_call_sse`<br>`上交所认购期权/option_call_sse` | 上交所认购期权 | table | - | page_size, page | - | quote.listed(name=option_call_sse,page_size=page_size,page=page)[all] |
| `option_call_szse`<br>`深交所认购期权/option_call_szse` | 深交所认购期权 | table | - | page_size, page | - | quote.listed(name=option_call_szse,page_size=page_size,page=page)[all] |
| `option_cffex_all`<br>`中金所股指期权/中金所期权/股指期权/option_cffex_all` | 中金所股指期权 | table | - | page_size, page | - | quote.listed(name=option_cffex_all,page_size=page_size,page=page)[all] |
| `option_cffex_hs300`<br>`沪深300股指期权/option_cffex_hs300` | 沪深300股指期权 | table | - | page_size, page | - | quote.listed(name=option_cffex_hs300,page_size=page_size,page=page)[all] |
| `option_cffex_zz1000`<br>`中证1000股指期权/option_cffex_zz1000` | 中证1000股指期权 | table | - | page_size, page | - | quote.listed(name=option_cffex_zz1000,page_size=page_size,page=page)[all] |
| `option_commodity`<br>`商品期权/期权合约/商品期权列表/option_commodity` | 商品期权合约 | table | - | market*, product, page_size, page | - | quote.option_contracts(market=market,product=product,page_size=page_size,page=page)[all] |
| `option_lhb`<br>`期权龙虎榜/期权持仓排名/期权成交排名/option_lhb` | 期权龙虎榜 | table | - | security_code, page_size | - | ext.option_lhb(security_code=security_code,page_size=page_size)[all] |
| `option_list_all`<br>`全部商品期权/option_list_all` | 全部商品期权 | table | - | page_size, page | - | quote.listed(name=option_list_all,page_size=page_size,page=page)[all] |
| `option_list_sse`<br>`上交所期权/上交所期权列表/50ETF期权/option_list_sse` | 上交所期权 | table | - | page_size, page | - | quote.listed(name=option_list_sse,page_size=page_size,page=page)[all] |
| `option_list_szse`<br>`深交所期权/深交所期权列表/沪深300ETF期权/option_list_szse` | 深交所期权 | table | - | page_size, page | - | quote.listed(name=option_list_szse,page_size=page_size,page=page)[all] |
| `option_put_sse`<br>`上交所认沽期权/option_put_sse` | 上交所认沽期权 | table | - | page_size, page | - | quote.listed(name=option_put_sse,page_size=page_size,page=page)[all] |
| `option_put_szse`<br>`深交所认沽期权/option_put_szse` | 深交所认沽期权 | table | - | page_size, page | - | quote.listed(name=option_put_szse,page_size=page_size,page=page)[all] |
| `option_tquote`<br>`T型报价/期权T型报价/期权报价/option_tquote` | 期权T型报价 | table | - | underlying*, kind, page_size, page | - | quote.option_tquote(underlying=underlying,kind=kind,page_size=page_size,page=page)[all] |
| `orderbook`<br>`盘口/五档/order_book` | 五档盘口 | table | - | code* | - | quote.orderbook(code=code) |
| `pb`<br>`市净率/PB/市净` | 市净率 | scalar | 倍 | code* | - | quote.snapshot(code=code).pb |
| `pct_change`<br>`涨跌幅/percent_change/涨幅` | 涨跌幅 | scalar | % | code* | - | quote.snapshot(code=code).pct_change → quote.kline(code=code,klt=101,fqt=0,lmt=80,end=trade_date).pct_change⤵ |
| `pe`<br>`市盈率/PE/市盈` | 市盈率 | scalar | 倍 | code* | scope=ttm|dynamic|static（默认 ttm） | quote.snapshot(code=code).{scope_field} |
| `pkyd`<br>`盘口异动/异动明细/实时异动/个股异动/pkyd` | 盘口异动明细 | table | - | kind, page_size, page | - | quote.pkyd(kind=kind,page_size=page_size,page=page)[all] |
| `pre_close`<br>`昨收/prev_close/previous_close` | 昨收价 | scalar | 元 | code* | - | quote.snapshot(code=code).pre_close |
| `precious_metal`<br>`贵金属/黄金库存/黄金持仓/CFTC/COMEX/ETF黄金/钯金/铂金/白银/precious_metal` | 贵金属数据中心（CFTC持仓/COMEX库存/ETF黄金） | series | - | page_size | - | dc.get(report=RPT_FUTUOPT_GOLDSIL,sort_columns=REPORT_DATE,sort_types=-1,page_size=page_size)[all] |
| `price`<br>`现价/latest/last_price/当前价` | 最新价 | scalar | 元 | code* | - | quote.snapshot(code=code).price |
| `qs_pool`<br>`强势股/强势股池/qs_pool` | 强势股池 | table | - | trade_date, page_size | - | pool.get(kind=qs,trade_date=trade_date,page_size=page_size)[all] |
| `region_board`<br>`地域板块/地域板块列表/地区板块/region_board` | 地域板块 | table | - | page_size, page | - | quote.listed(name=region_board,page_size=page_size,page=page)[all] |
| `reits_list`<br>`REITs行情/REITs列表/基础设施基金/reits_list` | REITs行情 | table | - | page_size, page | - | quote.listed(name=reits_list,page_size=page_size,page=page)[all] |
| `reits_list_sh`<br>`沪市REITs/reits_list_sh` | 沪市REITs | table | - | page_size, page | - | quote.listed(name=reits_list_sh,page_size=page_size,page=page)[all] |
| `reits_list_sz`<br>`深市REITs/reits_list_sz` | 深市REITs | table | - | page_size, page | - | quote.listed(name=reits_list_sz,page_size=page_size,page=page)[all] |
| `repo_sh`<br>`上证质押式回购/沪回购/国债逆回购沪/repo_sh` | 上证质押式回购 | table | - | page_size, page | - | quote.listed(name=repo_sh,page_size=page_size,page=page)[all] |
| `repo_sz`<br>`深证质押式回购/深回购/国债逆回购深/repo_sz` | 深证质押式回购 | table | - | page_size, page | - | quote.listed(name=repo_sz,page_size=page_size,page=page)[all] |
| `secid_kline`<br>`跨市场K线/港股K线/美股K线/外汇K线/国际指数K线/secid_kline/hk_kline/us_kline/forex_kline` | 跨市场K线 | series | - | secid*, klt, lmt | - | quote.kline_secid(secid=secid,klt=klt,lmt=lmt)[all] |
| `secid_quote`<br>`跨市场快照/港股快照/美股快照/外汇快照/国际指数快照/港股行情/美股行情/secid_quote/hk_quote/us_quote/forex_quote/global_index_quote` | 跨市场快照 | table | - | secid* | - | quote.snapshot_secid(secid=secid)[all] |
| `small_net_inflow`<br>`小单净额/散户净额` | 小单净流入 | scalar | 元 | code* | - | quote.snapshot(code=code).small_net_inflow |
| `st_stock_list`<br>`风险警示板/ST股/风险警示/st_stock_list` | 风险警示板 | table | - | page_size, page | - | quote.listed(name=st_stock_list,page_size=page_size,page=page)[all] |
| `st_stock_list_bj`<br>`风险警示板(北)/st_stock_list_bj` | 风险警示板(北) | table | - | page_size, page | - | quote.listed(name=st_stock_list_bj,page_size=page_size,page=page)[all] |
| `st_stock_list_gem`<br>`风险警示板(创业)/st_stock_list_gem` | 风险警示板(创业) | table | - | page_size, page | - | quote.listed(name=st_stock_list_gem,page_size=page_size,page=page)[all] |
| `st_stock_list_kcb`<br>`风险警示板(科创)/st_stock_list_kcb` | 风险警示板(科创) | table | - | page_size, page | - | quote.listed(name=st_stock_list_kcb,page_size=page_size,page=page)[all] |
| `st_stock_list_sh`<br>`风险警示板(沪)/st_stock_list_sh` | 风险警示板(沪) | table | - | page_size, page | - | quote.listed(name=st_stock_list_sh,page_size=page_size,page=page)[all] |
| `st_stock_list_sz`<br>`风险警示板(深)/st_stock_list_sz` | 风险警示板(深) | table | - | page_size, page | - | quote.listed(name=st_stock_list_sz,page_size=page_size,page=page)[all] |
| `stock_list`<br>`沪深京A股/A股列表/沪深京A股列表/stock_list` | 沪深京A股 | table | - | page_size, page | - | quote.listed(name=stock_list,page_size=page_size,page=page)[all] |
| `stock_list_b`<br>`B股/B股列表/stock_list_b` | B股 | table | - | page_size, page | - | quote.listed(name=stock_list_b,page_size=page_size,page=page)[all] |
| `stock_list_bj`<br>`北交所股票/stock_list_bj` | 北交所股票 | table | - | page_size, page | - | quote.listed(name=stock_list_bj,page_size=page_size,page=page)[all] |
| `stock_list_gem`<br>`创业板/创业板列表/stock_list_gem` | 创业板 | table | - | page_size, page | - | quote.listed(name=stock_list_gem,page_size=page_size,page=page)[all] |
| `stock_list_gem_hzz`<br>`创业板(核准制)/stock_list_gem_hzz` | 创业板(核准制) | table | - | page_size, page | - | quote.listed(name=stock_list_gem_hzz,page_size=page_size,page=page)[all] |
| `stock_list_gem_zcz`<br>`创业板(注册制)/stock_list_gem_zcz` | 创业板(注册制) | table | - | page_size, page | - | quote.listed(name=stock_list_gem_zcz,page_size=page_size,page=page)[all] |
| `stock_list_kcb`<br>`科创板/科创板列表/stock_list_kcb` | 科创板 | table | - | page_size, page | - | quote.listed(name=stock_list_kcb,page_size=page_size,page=page)[all] |
| `stock_list_sh`<br>`上证A股/stock_list_sh` | 上证A股 | table | - | page_size, page | - | quote.listed(name=stock_list_sh,page_size=page_size,page=page)[all] |
| `stock_list_sh_hzz`<br>`上证A股(核准制)/stock_list_sh_hzz` | 上证A股(核准制) | table | - | page_size, page | - | quote.listed(name=stock_list_sh_hzz,page_size=page_size,page=page)[all] |
| `stock_list_sh_zcz`<br>`上证A股(注册制)/stock_list_sh_zcz` | 上证A股(注册制) | table | - | page_size, page | - | quote.listed(name=stock_list_sh_zcz,page_size=page_size,page=page)[all] |
| `stock_list_sz`<br>`深证A股/stock_list_sz` | 深证A股 | table | - | page_size, page | - | quote.listed(name=stock_list_sz,page_size=page_size,page=page)[all] |
| `stock_list_sz_hzz`<br>`深证A股(核准制)/stock_list_sz_hzz` | 深证A股(核准制) | table | - | page_size, page | - | quote.listed(name=stock_list_sz_hzz,page_size=page_size,page=page)[all] |
| `stock_list_sz_zcz`<br>`深证A股(注册制)/stock_list_sz_zcz` | 深证A股(注册制) | table | - | page_size, page | - | quote.listed(name=stock_list_sz_zcz,page_size=page_size,page=page)[all] |
| `super_net_inflow`<br>`超大单净额` | 超大单净流入 | scalar | 元 | code* | - | quote.snapshot(code=code).super_net_inflow |
| `tick`<br>`分时/trend/逐笔` | 分时成交 | series | - | code* | - | quote.trends(code=code,ndays=1)[all] |
| `total_mv`<br>`总市值/market_cap/市值` | 总市值 | scalar | 元 | code* | - | quote.snapshot(code=code).total_mv |
| `trend_multi`<br>`多日分时/五日分时/分时多日/trend_multi` | 多日分时 | series | - | code*, ndays | - | quote.trends(code=code,ndays=ndays)[all] |
| `turnover_rate`<br>`换手率/换手/turnover` | 换手率 | scalar | % | code* | - | quote.snapshot(code=code).turnover_rate → quote.kline(code=code,klt=101,fqt=0,lmt=80,end=trade_date).turnover_rate⤵ |
| `uk_list`<br>`英股/英股列表/英国股票/uk_list` | 英股 | table | - | page_size, page | - | quote.listed(name=uk_list,page_size=page_size,page=page)[all] |
| `us_automotive_energy`<br>`知名美股·汽车能源/us_automotive_energy` | 知名美股·汽车能源 | table | - | page_size, page | - | quote.listed(name=us_automotive_energy,page_size=page_size,page=page)[all] |
| `us_china_list`<br>`中国概念股/us_china_list` | 中国概念股 | table | - | page_size, page | - | quote.listed(name=us_china_list,page_size=page_size,page=page)[all] |
| `us_china_net_list`<br>`互联网中国概念股/us_china_net_list` | 互联网中国概念股 | table | - | page_size, page | - | quote.listed(name=us_china_net_list,page_size=page_size,page=page)[all] |
| `us_financial`<br>`知名美股·金融/us_financial` | 知名美股·金融 | table | - | page_size, page | - | quote.listed(name=us_financial,page_size=page_size,page=page)[all] |
| `us_index_list`<br>`美股指数/us_index_list` | 美股指数 | table | - | page_size, page | - | quote.listed(name=us_index_list,page_size=page_size,page=page)[all] |
| `us_known_list`<br>`知名美股/us_known_list` | 知名美股 | table | - | page_size, page | - | quote.listed(name=us_known_list,page_size=page_size,page=page)[all] |
| `us_manufacture_retail`<br>`知名美股·制造零售/us_manufacture_retail` | 知名美股·制造零售 | table | - | page_size, page | - | quote.listed(name=us_manufacture_retail,page_size=page_size,page=page)[all] |
| `us_media`<br>`知名美股·媒体/us_media` | 知名美股·媒体 | table | - | page_size, page | - | quote.listed(name=us_media,page_size=page_size,page=page)[all] |
| `us_medicine_food`<br>`知名美股·医药食品/us_medicine_food` | 知名美股·医药食品 | table | - | page_size, page | - | quote.listed(name=us_medicine_food,page_size=page_size,page=page)[all] |
| `us_otc_list`<br>`粉单市场/OTC/粉单/us_otc_list` | 粉单市场 | table | - | page_size, page | - | quote.listed(name=us_otc_list,page_size=page_size,page=page)[all] |
| `us_stock_list`<br>`全部美股/美股列表/us_stock_list` | 全部美股 | table | - | page_size, page | - | quote.listed(name=us_stock_list,page_size=page_size,page=page)[all] |
| `us_technology`<br>`知名美股·科技/us_technology` | 知名美股·科技 | table | - | page_size, page | - | quote.listed(name=us_technology,page_size=page_size,page=page)[all] |
| `volume`<br>`成交量/vol` | 成交量 | scalar | 手 | code* | - | quote.snapshot(code=code).volume → quote.kline(code=code,klt=101,fqt=0,lmt=80,end=trade_date).volume⤵ |
| `volume_ratio`<br>`量比` | 量比 | scalar | - | code* | - | quote.snapshot(code=code).volume_ratio |
| `yzt_pool`<br>`昨日涨停/yzt` | 昨日涨停池 | table | - | trade_date, page_size | - | pool.get(kind=yzt,trade_date=trade_date,page_size=page_size)[all] |
| `zb_pool`<br>`炸板池/炸板` | 炸板池 | table | - | trade_date, page_size | - | pool.get(kind=zb,trade_date=trade_date,page_size=page_size)[all] |
| `zt_pool`<br>`涨停池/涨停板` | 涨停池 | table | - | trade_date, page_size | - | pool.get(kind=zt,trade_date=trade_date,page_size=page_size)[all] |
| `zt_sentiment`<br>`涨跌分布/涨跌家数分布/市场情绪/赚钱效应/zt_sentiment` | 涨跌分布 | table | - | trade_date | - | pool.fenbu(trade_date=trade_date)[all] |

## 资金 `capital`（86 个）

| 指标 | 名称 | kind | 单位 | 参数 | 口径 | 数据源链 |
| :- | :- | :-: | :-: | :- | :- | :- |
| `account_stat`<br>`开户数/账户统计` | 股票账户统计 | table | - | page_size | - | dc.get(report=RPT_CSDC_STATISTICS,sort_columns=TRADE_DATE,page_size=page_size)[all] |
| `block_trade`<br>`大宗/block_trade` | 大宗交易 | table | - | code, page_size | - | dc.get(report=RPT_DATA_BLOCKTRADE,filter=(SECURITY_CODE="{code}"),sort_columns=TRADE_DATE,page_size=page_size)[all] |
| `block_trade_active_dept`<br>`大宗交易活跃营业部/活跃营业部统计/block_trade_active_dept` | 大宗交易活跃营业部统计 | table | - | page_size, page | window=today|3d|5d|10d|30d（默认 today） | dc.get(report=RPT_BLOCKTRADE_OPERATEDEPTSTATISTICS,filter=(N_DATE={window_field}),sort_columns=BUYER_NUM,sort_types=-1,page_size=page_size,page=page)[all] |
| `block_trade_active_stock`<br>`大宗交易活跃A股/活跃A股统计/block_trade_active_stock` | 大宗交易活跃A股统计 | table | - | page_size, page | cycle=1m|3m|6m|1y（默认 3m） | dc.get(report=RPT_BLOCKTRADE_ACSTA,filter=(DATE_TYPE_CODE="{cycle_field}"),sort_columns=DEAL_NUM,sort_types=-1,page_size=page_size,page=page)[all] |
| `block_trade_daily_stat`<br>`大宗交易每日统计/大宗每日统计/block_trade_daily_stat` | 大宗交易每日统计 | table | - | date_from*, page_size, page | - | dc.get(report=RPT_BLOCKTRADE_STAINCLUDE,filter=(TRADE_DATE>='{date_from}'),sort_columns=TURNOVERRATE,sort_types=-1,page_size=page_size,page=page)[all] |
| `block_trade_dept_detail`<br>`营业部大宗交易明细/大宗营业部明细/block_trade_dept_detail` | 营业部大宗交易明细 | table | - | dept_code*, page_size, page | - | dc.get(report=RPT_DATA_BLOCKTRADE,filter=(BUYER_CODE="{dept_code}"),sort_columns=TRADE_DATE,sort_types=-1,page_size=page_size,page=page)[all] |
| `block_trade_dept_query`<br>`大宗交易营业部查询/大宗营业部查询/block_trade_dept_query` | 大宗交易营业部查询 | table | - | pinyin, page_size | - | dc.get(report=RPT_BLOCKTRADE_OPERATEDEPT_NAME,columns=ORG_CODE,ORG_NAME_ABBR,ORGNAME_PINYIN,ORG_RN,OPERATEDEPT_SPLICING,filter=(ORGNAME_PINYIN="{pinyin}"),sort_columns=ORGNAME_PINYIN,sort_types=1,page_size=page_size)[all] → dc.get(report=RPT_BLOCKTRADE_OPERATEDEPT_NAME,columns=ORG_CODE,ORG_NAME_ABBR,ORGNAME_PINYIN,ORG_RN,OPERATEDEPT_SPLICING,sort_columns=ORGNAME_PINYIN,sort_types=1,page_size=page_size)[all]⤵ |
| `block_trade_dept_rank`<br>`大宗交易营业部排行/大宗营业部排行/block_trade_dept_rank` | 大宗交易营业部排行 | table | - | page_size, page | cycle=1m|3m|6m|1y（默认 3m） | dc.get(report=RPT_BLOCKTRADE_OPERATEDEPT_RANK,filter=(N_DATE={cycle_field}),sort_columns=D5_BUYER_NUM,sort_types=-1,page_size=page_size,page=page)[all] |
| `block_trade_detail`<br>`大宗交易每日明细/大宗交易明细/block_trade_detail` | 大宗交易每日明细 | table | - | date_from*, page_size, page | sec_type=a|b|fund|bond（默认 a） | dc.get(report=RPT_DATA_BLOCKTRADE,filter=(SECURITY_TYPE_WEB="{sec_type_field}")(TRADE_DATE>='{date_from}'),sort_columns=SECURITY_CODE,sort_types=1,page_size=page_size,page=page)[all] |
| `block_trade_stat`<br>`大宗交易市场统计/大宗市场统计/block_trade_stat` | 大宗交易市场统计 | table | - | page_size, page | - | dc.get(report=PRT_BLOCKTRADE_MARKET_STA,sort_columns=TRADE_DATE,sort_types=-1,page_size=page_size,page=page)[all] |
| `board_stock_moneyflow`<br>`板块内个股资金流/板块个股资金流/board_stock_moneyflow` | 板块内个股资金流 | table | - | board_code*, stat, page_size | stat=today|3d|5d|10d（默认 today） | flow.board_stock(board_code=board_code,stat=stat,page_size=page_size)[all] |
| `concept_moneyflow_rank`<br>`概念资金流/概念资金流排行/concept_moneyflow_rank` | 概念资金流排行 | table | - | stat, page_size | stat=today|3d|5d|10d（默认 today） | flow.board_rank(board=concept,stat=stat,page_size=page_size)[all] |
| `holder_num`<br>`股东户数/股东人数` | 股东户数 | scalar | 户 | code* | - | dc.get(report=RPT_HOLDERNUMLATEST,filter=(SECURITY_CODE="{code}"),page_size=1).HOLDER_NUM[first] |
| `hsgt_board_hold_history`<br>`板块港通持股/hsgt_board_hold_history` | 板块沪深港通持股历史 | table | - | board_code*, page_size | - | dc.get(report=RPT_MUTUAL_BOARD_HOLDRANK_NEW,filter=(BOARD_CODE="{board_code}"),sort_columns=HOLD_DATE,page_size=page_size)[all] |
| `hsgt_board_member_hold`<br>`板块成分股港通持股/hsgt_board_member_hold` | 板块成分股沪深港通持股 | table | - | board_code*, page_size | - | dc.get(report=RPT_NORTH_BOARD_HOLDDETAIL_NEW,filter=(BOARD_CODE="{board_code}"),page_size=page_size)[all] |
| `hsgt_board_rank`<br>`北向增持板块/板块季度排行/hsgt_board_rank` | 北向增持板块排行 | table | - | page_size | board=hy|gn|dy（默认 hy） | dc.get(report=RPT_MUTUAL_BOARD_HOLDRANK_NEW,filter=(BOARD_TYPE="{board_field}"),sort_columns=HOLD_MARKET_CAP,page_size=page_size)[all] |
| `hsgt_channel_history`<br>`沪深港通历史/港通历史数据/hsgt_channel_history` | 沪深港通历史数据 | table | - | page_size | mutual=north|sh|sz|south|hk_sh|hk_sz（默认 north） | dc.get(report=RPT_MUTUAL_DEAL_HISTORY,filter=(MUTUAL_TYPE="{mutual_field}"),sort_columns=TRADE_DATE,page_size=page_size)[all] |
| `hsgt_deal_num`<br>`港通成交笔数/hsgt_deal_num` | 沪深港通成交笔数 | table | - | page_size | - | dc.get(report=RPT_MUTUAL_DEALAMT,sort_columns=TRADE_DATE,page_size=page_size)[all] |
| `hsgt_deal_num_month`<br>`港通月度成交/hsgt_deal_num_month` | 沪深港通月度成交 | table | - | page_size | - | dc.get(report=RPT_MUTUAL_DEALAMT_MONTHS,sort_columns=TRADE_DATE,page_size=page_size)[all] |
| `hsgt_hold_dates`<br>`港通持股日期/北向机构持股日期/hsgt_hold_dates` | 沪深港通持股日期窗口 | table | - | page_size | mutual=south|north（默认 south） | dc.get(report=RPT_MUTUAL_TRADEDATE,filter=(MUTUAL_TYPE="{mutual_field}"),sort_columns=HOLD_DATE,page_size=page_size)[all] → dc.get(report=RPT_NORTH_ORG_HOLDRANKDATE,sort_columns=TRADE_DATE,page_size=page_size)[all]⤵ |
| `hsgt_net`<br>`北向资金/港通净额/沪深港通/hsgt_net` | 沪深港通当日成交净买额 | scalar | 万元 | page_size | mutual=south|north（默认 south） | dc.get(report=RPT_MUTUAL_DEAL_HISTORY,filter=(MUTUAL_TYPE="{mutual_field}"),sort_columns=TRADE_DATE,page_size=1).NET_DEAL_AMT[first] |
| `hsgt_net_inflow_history`<br>`北向净流入/南向净流入/hsgt_net_inflow_history` | 沪深港通净流入序列 | table | 万元 | page_size | mutual=south|north（默认 south）；interval=today|d5|d20|hist（默认 today） | dc.get(report=RPT_MUTUAL_NETINFLOW_DETAILS,filter=(DIRECTION_TYPE="{mutual_field}")(TIME_TYPE="{interval_field}"),sort_columns=TRADE_DATE,page_size=page_size)[all] |
| `hsgt_net_inflow_stat`<br>`北向净流入统计/南向净流入统计/hsgt_net_inflow_stat` | 沪深港通净流入统计 | table | 万元 | page_size | - | dc.get(report=RPT_MUTUAL_NETINFLOW_STATISTICS,page_size=page_size)[all] |
| `hsgt_north_accum_netbuy`<br>`北向累计净买入/hsgt_north_accum_netbuy` | 北向累计净买入 | series | - | page_size | - | dc.get(report=RPT_NORTH_ACCUM_NETBUY,filter=(DATE_TYPE_CODE="001"),sort_columns=TRADE_DATE,page_size=page_size)[all] |
| `hsgt_north_stock_hold_rank`<br>`北向个股排行/北向持股排行/hsgt_north_stock_hold_rank` | 北向个股持股排行 | table | - | page_size | mutual=sh|sz（默认 sh） | dc.get(report=RPT_MUTUAL_HOLDRANK_NEW,filter=(MUTUAL_TYPE="{mutual_field}"),sort_columns=HOLD_MARKET_CAP,page_size=page_size)[all] |
| `hsgt_org_hold_detail`<br>`机构持股明细/机构港通持股明细/hsgt_org_hold_detail` | 沪深港通机构持股明细 | table | - | participant_code*, page_size | - | dc.get(report=RPT_NORTH_ORG_HOLDDETAIL_NEW,filter=(PARTICIPANT_CODE="{participant_code}"),page_size=page_size)[all] |
| `hsgt_org_hold_stat`<br>`机构持股统计/机构港通持股统计/hsgt_org_hold_stat` | 沪深港通机构持股统计 | table | - | participant_code*, date_from, page_size | - | dc.get(report=PRT_MUTUAL_ORG_STA,filter=(PARTICIPANT_CODE="{participant_code}")(HOLD_DATE>='{date_from}'),sort_columns=HOLD_DATE,page_size=page_size)[all] → dc.get(report=PRT_MUTUAL_ORG_STA,filter=(PARTICIPANT_CODE="{participant_code}"),sort_columns=HOLD_DATE,page_size=page_size)[all]⤵ |
| `hsgt_org_rank`<br>`机构季度排行/北向机构排行/hsgt_org_rank` | 沪深港通机构季度排行 | table | - | page_size | mutual=sh|sz（默认 sh） | dc.get(report=RPT_NORTH_ORG_HOLDRANK_NEW,filter=(MUTUAL_TYPE="{mutual_field}"),sort_columns=HOLD_MARKET_CAP,page_size=page_size)[all] |
| `hsgt_quota`<br>`北向额度/港通额度` | 沪深港通额度 | table | - | page_size | - | dc.get(report=RPT_MUTUAL_QUOTA,sort_columns=TRADE_DATE,page_size=page_size)[all] |
| `hsgt_south_accum_netbuy`<br>`南向累计净买入/hsgt_south_accum_netbuy` | 南向累计净买入 | series | - | page_size | - | dc.get(report=RPT_SOUTH_ACCUM_NETBUY,filter=(DATE_TYPE_CODE="001"),sort_columns=TRADE_DATE,page_size=page_size)[all] |
| `hsgt_south_stock_hold_rank`<br>`南向个股排行/南向持股排行/hsgt_south_stock_hold_rank` | 南向个股持股排行 | table | - | page_size | mutual=south|hk_sh|hk_sz（默认 south） | dc.get(report=RPT_MUTUAL_STOCK_HOLDRANKS,filter={mutual_field},sort_columns=ADD_MARKET_CAP,page_size=page_size)[all] |
| `hsgt_stock_deal`<br>`个股港通成交/个股成交榜详情/hsgt_stock_deal` | 个股沪深港通成交榜 | table | - | code*, page_size | - | dc.get(report=RPT_MUTUAL_TOP10DEAL,filter=(SECURITY_CODE="{code}"),sort_columns=TRADE_DATE,page_size=page_size)[all] → dc.get(report=RPT_HK_DEAL_RANK,filter=(SECURITY_CODE="{code}"),sort_columns=TRADE_DATE,page_size=page_size)[all]⤵ |
| `hsgt_top10`<br>`十大成交股/十大活跃成交股/hsgt_top10` | 沪深港通十大成交股 | table | - | trade_date, page_size | mutual=sh|sz|hk_sh|hk_sz（默认 sh） | dc.get(report=RPT_MUTUAL_TOP10DEAL,filter=(MUTUAL_TYPE="{mutual_field}")(TRADE_DATE='{trade_date}'),sort_columns=RANK,sort_types=1,page_size=page_size)[all] → dc.get(report=RPT_MUTUAL_TOP10DEAL,filter=(MUTUAL_TYPE="{mutual_field}"),sort_columns=TRADE_DATE,RANK,sort_types=-1,1,page_size=page_size)[all]⤵ |
| `industry_moneyflow_rank`<br>`行业资金流/行业资金流排行/industry_moneyflow_rank` | 行业资金流排行 | table | - | stat, page_size | stat=today|3d|5d|10d（默认 today） | flow.board_rank(board=industry,stat=stat,page_size=page_size)[all] |
| `lhb`<br>`龙虎榜/龙虎` | 龙虎榜 | table | - | trade_date, page_size | - | dc.get(report=RPT_DAILYBILLBOARD_DETAILSNEW,sort_columns=TRADE_DATE,page_size=page_size)[all] |
| `lhb_active_dept`<br>`每日活跃营业部/活跃营业部/lhb_active_dept` | 每日活跃营业部 | table | - | date_from*, page_size, page | - | dc.get(report=RPT_OPERATEDEPT_ACTIVE,filter=(ONLIST_DATE>='{date_from}'),sort_columns=TOTAL_NETAMT,sort_types=-1,page_size=page_size,page=page)[all] |
| `lhb_date_windows`<br>`龙虎榜日期窗口/龙虎榜区间日期/lhb_date_windows` | 龙虎榜区间日期 | table | - | - | - | dc.get(report=RPT_ORGANIZATION_DATE,sort_columns=NEWDATE,sort_types=-1)[all] |
| `lhb_dept_detail`<br>`营业部上榜明细/营业部明细/lhb_dept_detail` | 营业部上榜明细 | table | - | dept_code*, page_size, page | - | dc.get(report=RPT_OPERATEDEPT_TRADE_DETAILSNEW,filter=(OPERATEDEPT_CODE="{dept_code}"),sort_columns=TRADE_DATE,sort_types=-1,page_size=page_size,page=page)[all] |
| `lhb_dept_query`<br>`营业部查询/证券公司查询/lhb_dept_query` | 证券公司营业部查询 | table | - | pinyin, page_size | - | dc.get(report=RPT_OPERATEDEPT_NAME,filter=(ORGNAME_PINYIN="{pinyin}"),sort_columns=ORGNAME_PINYIN,sort_types=1,page_size=page_size)[all] → dc.get(report=RPT_OPERATEDEPT_NAME,sort_columns=ORGNAME_PINYIN,sort_types=1,page_size=page_size)[all]⤵ |
| `lhb_dept_return_rank`<br>`营业部回报排行/营业部回报/lhb_dept_return_rank` | 营业部回报排行 | table | - | page_size, page | cycle=1m|3m|6m|1y（默认 3m） | dc.get(report=RPT_RATEDEPT_RETURNT_RANKING,filter=(STATISTICSCYCLE="{cycle_field}"),sort_columns=TOTAL_BUYER_SALESTIMES_1DAY,sort_types=-1,page_size=page_size,page=page)[all] |
| `lhb_dept_stat`<br>`证券营业部上榜统计/营业部上榜统计/lhb_dept_stat` | 证券营业部上榜统计 | table | - | page_size, page | cycle=1m|3m|6m|1y（默认 3m） | dc.get(report=RPT_OPERATEDEPT_LIST_STATISTICS,filter=(STATISTICSCYCLE="{cycle_field}"),sort_columns=AMOUNT,sort_types=-1,page_size=page_size,page=page)[all] |
| `lhb_org_daily`<br>`机构买卖每日统计/机构买卖情况/lhb_org_daily` | 机构买卖每日统计 | table | - | date_from*, page_size, page | market=all|sha|kcb|sza|cyb|bja|kzz（默认 all） | dc.get(report=RPT_ORGANIZATION_TRADE_DETAILSNEW,filter=(TRADE_DATE>='{date_from}'){market_field},sort_columns=NET_BUY_AMT,sort_types=-1,page_size=page_size,page=page)[all] |
| `lhb_org_seat`<br>`机构席位追踪/机构席位买卖追踪/lhb_org_seat` | 机构席位追踪 | table | - | page_size, page | cycle=1m|3m|6m|1y（默认 3m） | dc.get(report=RPT_ORGANIZATION_SEATNEW,filter=(STATISTICSCYCLE="{cycle_field}"),sort_columns=ONLIST_TIMES,sort_types=-1,page_size=page_size,page=page)[all] |
| `lhb_stock_day`<br>`个股单日龙虎榜/单日龙虎榜明细/lhb_stock_day` | 个股单日龙虎榜明细 | table | - | code*, trade_date*, page_size | - | dc.get(report=RPT_DAILYBILLBOARD_DETAILSNEW,filter=(SECURITY_CODE="{code}")(TRADE_DATE<='{trade_date}')(TRADE_DATE>='{trade_date}'),sort_columns=TRADE_DATE,sort_types=-1,page_size=page_size)[all] |
| `lhb_stock_history`<br>`个股龙虎榜历史/龙虎榜历史/lhb_stock_history` | 个股龙虎榜历史 | table | - | code*, page_size | - | dc.get(report=RPT_BILLBOARD_DAILYDETAILS,filter=(SECURITY_CODE="{code}"),sort_columns=TRADE_DATE,sort_types=-1,page_size=page_size)[all] |
| `lhb_stock_stat`<br>`个股上榜统计/龙虎榜统计/lhb_stock_stat` | 个股龙虎榜统计 | table | - | page_size, page | cycle=1m|3m|6m|1y（默认 3m） | dc.get(report=RPT_BILLBOARD_TRADEALLNEW,filter=(STATISTICS_CYCLE="{cycle_field}"),sort_columns=BILLBOARD_TIMES,sort_types=-1,page_size=page_size,page=page)[all] |
| `lhb_trade_detail`<br>`龙虎榜交易明细/龙虎榜明细/lhb_trade_detail` | 龙虎榜交易明细 | table | - | trade_date*, page_size, page | market=all|sha|kcb|sza|cyb|bja|kzz（默认 all） | dc.get(report=RPT_DAILYBILLBOARD_DETAILSNEW,filter=(TRADE_DATE<='{trade_date}')(TRADE_DATE>='{trade_date}'){market_field},sort_columns=TRADE_DATE,sort_types=-1,page_size=page_size,page=page)[all] |
| `lift_market_day`<br>`解禁日/每日解禁/lift_market_day` | 解禁市场一览（日） | series | - | page_size | market=all|sha|sza|kcb|cyb|bja（默认 all） | dc.get(report=RPT_LIFTDAY_STA,filter=(INDEX_CODE="{market_field}"),sort_columns=FREE_DATE,sort_types=1,page_size=page_size)[all] |
| `lift_market_month`<br>`解禁月/每月解禁/lift_market_month` | 解禁市场一览（月） | series | - | page_size | market=all|sha|sza|kcb|cyb|bja（默认 all） | dc.get(report=RPT_CUSTOM_LIFT_STA_MONTH,filter=(INDEX_CODE="{market_field}"),sort_columns=LIFT_MON,sort_types=1,page_size=page_size)[all] |
| `lift_market_week`<br>`解禁周/每周解禁/lift_market_week` | 解禁市场一览（周） | series | - | page_size | market=all|sha|sza|kcb|cyb|bja（默认 all） | dc.get(report=RPT_CUSTOM_LIFT_STA_WEEK,filter=(INDEX_CODE="{market_field}"),sort_columns=START_DATE,sort_types=1,page_size=page_size)[all] |
| `lift_stage`<br>`解禁明细/解禁个股/lift_stage` | 限售解禁明细 | table | - | date_from*, page_size | - | dc.get(report=RPT_LIFT_STAGE,columns=SECURITY_CODE,SECURITY_NAME_ABBR,FREE_DATE,CURRENT_FREE_SHARES,ABLE_FREE_SHARES,LIFT_MARKET_CAP,FREE_RATIO,NEW,B20_ADJCHRATE,A20_ADJCHRATE,FREE_SHARES_TYPE,TOTAL_RATIO,NON_FREE_SHARES,BATCH_HOLDER_NUM,filter=(FREE_DATE>='{date_from}'),sort_columns=FREE_DATE,CURRENT_FREE_SHARES,sort_types=1,-1,page_size=page_size)[all] |
| `lift_total_stat`<br>`解禁统计/解禁规模/lift_total_stat` | 限售解禁统计 | table | - | page_size | cycle=1m|1q|1y（默认 1m） | dc.get(report=RPT_LIFT_STA,filter=(STA="{cycle_field}"),page_size=page_size)[all] |
| `margin_account_stat`<br>`两融账户统计/两融账户信息日度/margin_account_stat` | 两融账户信息（日度） | table | - | page_size | - | dc.get(report=RPTA_WEB_MARGIN_DAILYTRADE,sort_columns=STATISTICS_DATE,page_size=page_size)[all] |
| `margin_account_stat_month`<br>`两融账户月度/两融账户信息月度/margin_account_stat_month` | 两融账户信息（月度） | table | - | page_size | - | dc.get(report=RPTA_WEB_MARGIN_MONTHTRADE,sort_columns=STATISTICS_DATE,page_size=page_size)[all] |
| `margin_balance`<br>`融资余额/融资` | 融资余额 | scalar | 元 | code* | - | dc.get(report=RPTA_WEB_RZRQ_GGMX,filter=(SCODE="{code}"),sort_columns=DATE,page_size=5).RZYE[first] |
| `margin_board_detail`<br>`板块两融明细/板块融资融券明细/margin_board_detail` | 板块融资融券明细 | table | - | board_code*, page_size | - | dc.board(report=RPTA_WEB_BKJYMX,filter=(BOARD_CODE="{board_code}"),sort_columns=TRADE_DATE,page_size=page_size)[all] |
| `margin_board_member`<br>`板块个股两融/margin_board_member` | 板块成分股两融（今日） | table | - | board_code*, page_size | - | dc.board(report=RPTA_WEB_GGJYMX,filter=(BOARD_CODE="{board_code}"),sort_columns=FIN_NETBUY_AMT,page_size=page_size)[all] |
| `margin_board_member_range`<br>`板块个股两融区间/margin_board_member_range` | 板块成分股两融（区间） | table | - | board_code*, page_size | interval=3日|5日|10日（默认 3日） | dc.board(report=RPTA_WEB_GGQJJYMX,filter=(BOARD_CODE="{board_code}")(INTERVAL_TYPE="{interval}"),sort_columns=FIN_NETBUY_AMT,page_size=page_size)[all] |
| `margin_board_rank`<br>`板块两融排行/板块融资融券排行/margin_board_rank` | 板块融资融券排行 | table | - | page_size | board=hy|gn|dy（默认 hy） | dc.get(report=RPTA_WEB_BKJYMXN,filter=(BOARD_TYPE_CODE="{board_field}"),sort_columns=FIN_NETBUY_AMT,page_size=page_size)[all] |
| `margin_board_rank_range`<br>`板块两融区间排行/板块融资融券区间排行/margin_board_rank_range` | 板块融资融券排行（区间） | table | - | page_size | board=hy|gn|dy（默认 hy）；interval=3日|5日|10日（默认 3日） | dc.get(report=RPTA_WEB_BKQJYMXN,filter=(BOARD_TYPE_CODE="{board_field}")(INTERVAL_TYPE="{interval}"),sort_columns=FIN_NETBUY_AMT,page_size=page_size)[all] |
| `margin_detail`<br>`两融交易明细/融资融券明细/margin_detail` | 融资融券交易明细 | table | - | trade_date, page_size | market=all|hs_a|sh_a|kcb|sz_a|cyb|bj_a|etf（默认 all）；interval=today|3d|5d|10d（默认 today） | dc.get(report=RPTA_WEB_RZRQ_GGMX,filter=(DATE='{trade_date}'){market_field},sort_columns=RZJME{interval_field},page_size=page_size)[all] → dc.get(report=RPTA_WEB_RZRQ_GGMX,filter={market_field},sort_columns=DATE,RZJME{interval_field},sort_types=-1,-1,page_size=page_size)[all]⤵ |
| `margin_history`<br>`两融历史数据/融资融券历史/margin_history` | 融资融券历史数据 | table | - | page_size | - | dc.get(report=RPTA_RZRQ_LSDB,sort_columns=DIM_DATE,page_size=page_size)[all] |
| `margin_market_total`<br>`两融交易总量/市场交易总量/margin_market_total` | 融资融券交易总量 | table | - | page_size | market=all|sh|sz|bj（默认 all） | dc.get(report=RPTA_RZRQ_LSHJ,filter={market_field},sort_columns=DIM_DATE,page_size=page_size)[all] → dc.get(report=RPTA_WEB_RZRQ_LSSH,filter={market_field},sort_columns=DIM_DATE,page_size=page_size)[all]⤵ |
| `margin_stock_history`<br>`个股两融历史/融资融券个股历史/margin_stock_history` | 个股融资融券历史 | series | - | code*, page_size | - | dc.get(report=RPTA_WEB_RZRQ_GGMX,filter=(SCODE="{code}"),sort_columns=DATE,page_size=page_size)[all] |
| `margin_sum`<br>`两融余额/两融合计` | 两融余额合计 | table | - | page_size | - | dc.get(report=RPTA_RZRQ_LSHJ,sort_columns=DIM_DATE,page_size=page_size)[all] |
| `margin_top_net_buy`<br>`融资净买入前十/margin_top_net_buy` | 融资净买入前十大证券 | table | - | trade_date, page_size | - | dc.get(report=RPTA_WEB_RZRQ_GGMX,filter=(DATE='{trade_date}'),sort_columns=RZJME,page_size=page_size)[all] → dc.get(report=RPTA_WEB_RZRQ_GGMX,sort_columns=DATE,RZJME,sort_types=-1,-1,page_size=page_size)[all]⤵ |
| `market_moneyflow`<br>`大盘资金流/指数资金流/沪深两市资金流/market_moneyflow` | 大盘/指数资金流 | table | - | index | index=hs2|sh|sz|cyb|shb|szb|kcb（默认 hs2） | flow.index(index=index)[all] |
| `market_moneyflow_history`<br>`大盘资金流历史/指数资金流历史/market_moneyflow_history` | 大盘/指数资金流历史 | series | 元 | index, lmt | index=sh|sz|cyb|shb|szb|kcb（默认 sh） | flow.index_kline(index=index,lmt=lmt)[all] |
| `moneyflow`<br>`资金流向/资金流/money_flow` | 资金流向（历史） | series | 元 | code* | - | money.flow(code=code,lmt=20)[all] |
| `pledge_holder_detail`<br>`股东质押明细/质押明细/pledge_holder_detail` | 重要股东质押明细 | table | - | code, page_size | - | dc.get(report=RPTA_APP_ACCUMDETAILS,filter=(SECURITY_CODE="{code}"),sort_columns=NOTICE_DATE,page_size=page_size)[all] → dc.get(report=RPTA_APP_ACCUMDETAILS,sort_columns=NOTICE_DATE,page_size=page_size)[all]⤵ |
| `pledge_industry_stat`<br>`行业质押/质押行业统计/pledge_industry_stat` | 行业质押统计 | table | - | page_size | - | dc.get(report=RPT_CSDC_INDUSTRY_STATISTICS,sort_columns=AVERAGE_PLEDGE_RATIO,page_size=page_size)[all] |
| `pledge_market_overview`<br>`股权质押概况/质押市场概况/pledge_market_overview` | 股权质押市场概况 | series | - | page_size | - | dc.get(report=RPT_CSDC_STATISTICS,sort_columns=TRADE_DATE,page_size=page_size)[all] |
| `pledge_org_stat`<br>`质押方统计/质押机构统计/pledge_org_stat` | 质押方构成统计 | table | - | page_size | org_type=sec|bank（默认 sec） | dc.get(report=RPT_GDZY_ZYJG_SUM,filter=(PFORG_TYPE="{org_type_field}"),sort_columns=ORG_NUM,page_size=page_size)[all] |
| `pledge_org_type_stat`<br>`质押方类型/pledge_org_type_stat` | 质押方类型统计 | table | - | page_size | - | dc.get(report=RPTA_APP_PLEDGEORGTYPE,columns=PLEDGE_TYPE,PLEDGE_RATIO,PLEDGE_NUM,page_size=page_size)[all] |
| `pledge_ratio`<br>`质押比例/质押率` | 股权质押比例 | scalar | % | code* | - | dc.get(report=RPT_CSDC_LIST_NEWEST,filter=(SECURITY_CODE="{code}"),sort_columns=TRADE_DATE,page_size=1).PLEDGE_RATIO[first] |
| `pledge_ratio_dist`<br>`质押比例分布/pledge_ratio_dist` | 质押比例分布 | table | - | page_size | - | dc.get(report=RPTA_APP_APLEDGERATIO,sort_columns=RATIO_PARAMETER,sort_types=1,page_size=page_size)[all] |
| `pledge_ratio_list`<br>`质押比例/质押比例排行/pledge_ratio_list` | 上市公司质押比例排行 | table | - | page_size | - | dc.get(report=RPT_CSDC_LIST_NEWEST,sort_columns=PLEDGE_RATIO,page_size=page_size)[all] |
| `pledge_stock_history`<br>`个股质押比例/质押比例历史/pledge_stock_history` | 个股质押比例序列 | series | - | code*, page_size | - | dc.get(report=RPT_CSDC_LIST,filter=(SECURITY_CODE="{code}"),sort_columns=TRADE_DATE,page_size=page_size)[all] |
| `pledge_stock_org_detail`<br>`质押机构关联/个股质押机构/pledge_stock_org_detail` | 个股质押机构关联 | table | - | code*, page_size | - | dc.get(report=RPT_GDZY_ZYJG_SUM,filter=(SECURITY_CODE="{code}"),page_size=page_size)[all] |
| `pledge_warning_dist`<br>`质押预警线/预警线分布/pledge_warning_dist` | 质押预警线分布 | table | - | page_size | - | dc.get(report=RPTA_APP_WARNING,sort_columns=WARNING_CODE,sort_types=1,page_size=page_size)[all] |
| `region_moneyflow_rank`<br>`地域资金流/地域资金流排行/region_moneyflow_rank` | 地域资金流排行 | table | - | stat, page_size | stat=today|3d|5d|10d（默认 today） | flow.board_rank(board=region,stat=stat,page_size=page_size)[all] |
| `securities_loan_balance`<br>`融券余额/融券` | 融券余额 | scalar | 元 | code* | - | dc.get(report=RPTA_WEB_RZRQ_GGMX,filter=(SCODE="{code}"),sort_columns=DATE,page_size=5).RQYL[first] |
| `stock_data_flags`<br>`数据模块标记/个股数据标记/stock_data_flags` | 个股数据中心入口标记 | table | - | code* | - | dc.get(report=RPT_STOCK_HEADERCHANGE,filter=(SECURITY_CODE="{code}"),page_size=1)[all] |
| `stock_moneyflow_rank`<br>`个股资金流排行/主力净流入排名/资金流排行/main_moneyflow_rank` | 个股资金流排行 | table | - | market, stat, page_size | stat=today|3d|5d|10d（默认 today）；market=all|hsa|sha|kcb|sza|cyb|zxb|hb|sb|bja（默认 all） | flow.stock_rank(market=market,stat=stat,page_size=page_size)[all] |
| `zlsj_hold_rank`<br>`主力持仓/机构持仓股/基金重仓股/zlsj_hold_rank` | 机构持仓股排行 | table | - | date, page_size, page_num | org_type=fund|qfii|ssf|broker|insurance|trust（默认 fund） | zlsj.list(date=date,org_type={org_type_field},page_size=page_size,page_num=page_num)[all] |
| `zlsj_report_dates`<br>`主力报告期/机构持仓日期/zlsj_report_dates` | 主力数据报告期 | table | - | page_size | - | dc.get(report=RPT_MAIN_REPORTDATE,sort_columns=REPORT_DATE,page_size=page_size)[all] |

## 财务 `finance`（20 个）

| 指标 | 名称 | kind | 单位 | 参数 | 口径 | 数据源链 |
| :- | :- | :-: | :-: | :- | :- | :- |
| `balance_sheet`<br>`资产负债表/负债表` | 资产负债表 | table | - | code* | - | dc.get(report=RPT_DMSK_FN_BALANCE,filter=(SECURITY_CODE="{code}"),sort_columns=REPORT_DATE,page_size=10)[all] |
| `bps`<br>`每股净资产/BPS` | 每股净资产 | scalar | 元 | code* | - | dc.get(report=RPT_LICO_FN_CPD,filter=(SECURITY_CODE="{code}"),sort_columns=REPORTDATE,page_size=5).BPS[first] |
| `cashflow_statement`<br>`现金流量表/现金流` | 现金流量表 | table | - | code* | - | dc.get(report=RPT_DMSK_FN_CASHFLOW,filter=(SECURITY_CODE="{code}"),sort_columns=REPORT_DATE,page_size=10)[all] |
| `disclose_plan`<br>`预约披露/披露时间` | 预约披露 | table | - | code* | - | dc.get(report=RPT_PUBLIC_BS_APPOIN,filter=(SECURITY_CODE="{code}"),sort_columns=FIRST_APPOINT_DATE,page_size=10)[all] |
| `dividend`<br>`分红/送配/dividend` | 分红送配 | table | - | code* | - | dc.get(report=RPT_SHAREBONUS_DET,filter=(SECURITY_CODE="{code}"),sort_columns=REPORT_DATE,page_size=10)[all] |
| `eps`<br>`每股收益/EPS` | 每股收益 | scalar | 元 | code*, report_date | - | dc.get(report=RPT_LICO_FN_CPD,filter=(SECURITY_CODE="{code}"),sort_columns=REPORTDATE,page_size=5).BASIC_EPS[first] |
| `express`<br>`业绩快报/快报` | 业绩快报 | table | - | code* | - | dc.get(report=RPT_FCI_PERFORMANCEE,filter=(SECURITY_CODE="{code}"),sort_columns=REPORT_DATE,page_size=10)[all] |
| `financial_indicators`<br>`财务指标/主要指标` | 财务指标（全表） | table | - | code* | - | dc.get(report=RPT_LICO_FN_CPD,filter=(SECURITY_CODE="{code}"),sort_columns=REPORTDATE,page_size=10)[all] |
| `forecast`<br>`业绩预告/预告` | 业绩预告 | table | - | code* | - | dc.get(report=RPT_PUBLIC_OP_NEWPREDICT,filter=(SECURITY_CODE="{code}"),sort_columns=NOTICE_DATE,page_size=10)[all] |
| `gross_margin`<br>`毛利率/gross_margin` | 销售毛利率 | scalar | % | code* | - | dc.get(report=RPT_LICO_FN_CPD,filter=(SECURITY_CODE="{code}"),sort_columns=REPORTDATE,page_size=5).XSMLL[first] |
| `income_statement`<br>`利润表/损益表` | 利润表 | table | - | code* | - | dc.get(report=RPT_DMSK_FN_INCOME,filter=(SECURITY_CODE="{code}"),sort_columns=REPORT_DATE,page_size=10)[all] |
| `net_profit`<br>`净利润/归母净利润/profit` | 净利润 | scalar | 元 | code* | - | dc.get(report=RPT_LICO_FN_CPD,filter=(SECURITY_CODE="{code}"),sort_columns=REPORTDATE,page_size=5).PARENT_NETPROFIT[first] |
| `ocfps`<br>`每股现金流/ocfps` | 每股经营现金流 | scalar | 元 | code* | - | dc.get(report=RPT_LICO_FN_CPD,filter=(SECURITY_CODE="{code}"),sort_columns=REPORTDATE,page_size=5).MGJYXJJE[first] |
| `rating`<br>`评级/研报评级` | 机构评级 | table | - | code, page_size | - | news.reports(page_size=page_size)[all] |
| `revenue`<br>`营收/revenue/总收入` | 营业收入 | scalar | 元 | code* | - | dc.get(report=RPT_LICO_FN_CPD,filter=(SECURITY_CODE="{code}"),sort_columns=REPORTDATE,page_size=5).TOTAL_OPERATE_INCOME[first] |
| `roe`<br>`净资产收益率/ROE` | 净资产收益率 | scalar | % | code* | - | dc.get(report=RPT_LICO_FN_CPD,filter=(SECURITY_CODE="{code}"),sort_columns=REPORTDATE,page_size=5).WEIGHTAVG_ROE[first] |
| `survey`<br>`调研/机构调研` | 机构调研 | table | - | code* | - | dc.get(report=RPT_ORG_SURVEYNEW,filter=(SECURITY_CODE="{code}"),sort_columns=RECEIVE_START_DATE,page_size=10)[all] |
| `unlock`<br>`解禁/限售股/unlock` | 限售解禁 | table | - | code* | - | dc.get(report=RPT_LIFT_STAGE,filter=(SECURITY_CODE="{code}"),sort_columns=FREE_DATE,page_size=10)[all] |
| `yoy_net_profit`<br>`净利润同比/净利同比` | 净利润同比增长 | scalar | % | code* | - | dc.get(report=RPT_LICO_FN_CPD,filter=(SECURITY_CODE="{code}"),sort_columns=REPORTDATE,page_size=5).SJLHZ[first] |
| `yoy_revenue`<br>`营收同比` | 营收同比增长 | scalar | % | code* | - | dc.get(report=RPT_LICO_FN_CPD,filter=(SECURITY_CODE="{code}"),sort_columns=REPORTDATE,page_size=5).YSHZ[first] |

## 公司资料 `f10`（115 个）

| 指标 | 名称 | kind | 单位 | 参数 | 口径 | 数据源链 |
| :- | :- | :-: | :-: | :- | :- | :- |
| `capital_structure`<br>`股本结构/股本` | 股本结构 | table | - | code* | - | dc.securities(report=RPT_F10_EH_EQUITY,filter=(SECUCODE="{secucode}"),page_size=20)[all] |
| `concept`<br>`所属概念/题材/concept` | 所属概念 | table | - | code* | - | f10.module(code=code,module=f10_concept).ssbk[all] |
| `concept_keypoints`<br>`核心题材/题材要点/concept_keypoints` | 核心题材要点 | table | - | code* | - | f10.module(code=code,module=f10_concept).hxtc[all] → dc.securities(report=RPT_F10_CORETHEME_CONTENT,filter=(SECUCODE="{secucode}"),page_size=20)[all]⤵ |
| `dividend_financing`<br>`分红融资/分红历史` | 分红融资 | table | - | code* | - | f10.module(code=code,module=f10_bonus).lnfhrz[all] |
| `equity_incentive`<br>`股权激励/员工持股` | 股权激励 | table | - | code*, page_size | - | dc.get(report=RPT_EQUITY_INCENTIVE,filter=(SECUCODE="{secucode}"),sort_columns=LASTEST_NOTICE_DATE,page_size=page_size)[all] |
| `executives`<br>`高管/管理层` | 高管简历 | table | - | code* | - | f10.module(code=code,module=f10_management).gglb[all] |
| `f10_block_trade_detail`<br>`个股大宗交易/f10大宗交易/f10_block_trade_detail` | F10大宗交易 | table | - | code* | - | f10.module(code=code,module=f10_event).dzjy[all] |
| `f10_business_review`<br>`经营评述/业务回顾/f10_business_review` | F10经营评述 | table | - | code* | - | f10.module(code=code,module=f10_business).jyps[all] → dc.securities(report=RPT_F10_OP_BUSINESSANALYSIS,filter=(SECUCODE="{secucode}"),page_size=10)[all]⤵ |
| `f10_business_scope`<br>`主营范围/经营范围/f10_business_scope` | F10主营范围 | table | - | code* | - | f10.module(code=code,module=f10_business).zyfw[all] |
| `f10_company_scale`<br>`公司规模/规模对比/f10_company_scale` | F10公司规模 | table | - | code* | - | f10.module(code=code,module=f10_industry).gsgm[all] → dc.securities(report=RPT_PCF10_INDUSTRY_MARKET,filter=(SECUCODE="{secucode}"),page_size=20)[all]⤵ |
| `f10_competitiveness`<br>`核心竞争力/产品竞争力/f10_competitiveness` | F10核心竞争力 | table | - | code*, page_size | - | dc.securities(report=RPT_COMPETITIVENESS_PRODUCTTAG_NEW,filter=(SECUCODE="{secucode}"),page_size=page_size)[all] |
| `f10_controlling_holder`<br>`控股股东/实际控制人/f10_controlling_holder` | F10控股股东 | table | - | code* | - | f10.module(code=code,module=f10_holding).sjkzr[all] |
| `f10_core_indicators`<br>`操盘必读/核心指标/f10_core_indicators` | F10操盘必读核心指标 | table | - | code* | - | f10.module(code=code,module=f10_required).zxzb[all] |
| `f10_customer_supplier`<br>`客户供应商/主要客户/f10_customer_supplier` | F10客户与供应商 | table | - | code*, page_size | - | dc.securities(report=RPT_F10_BUSINESS_CUSTSUPP,filter=(SECUCODE="{secucode}"),page_size=page_size)[all] |
| `f10_dev_history`<br>`发展历程/变更历程/f10_dev_history` | F10发展历程 | table | - | code*, page_size | - | dc.securities(report=RPT_ORG_COURSECHANGE,filter=(SECUCODE="{secucode}"),sort_columns=CHANGE_DATE,page_size=page_size)[all] |
| `f10_dividend_histogram`<br>`分红融资直方/分红统计/f10_dividend_histogram` | F10分红融资直方 | table | - | code* | - | dc.securities(report=RPT_F10_DIVIDEND_HISTOGRAM,filter=(SECUCODE="{secucode}"),page_size=20)[all] |
| `f10_dividend_plan`<br>`分红方案/分红派息/f10_dividend_plan` | F10分红方案 | table | - | code* | - | f10.module(code=code,module=f10_bonus).fhyx[all] → dc.securities(report=RPT_F10_DIVIDEND_MAIN,filter=(SECUCODE="{secucode}"),page_size=20)[all]⤵ |
| `f10_dupont_compare`<br>`杜邦分析比较/杜邦比较/f10_dupont_compare` | F10杜邦分析比较 | table | - | code* | - | f10.module(code=code,module=f10_industry).dbfxbj[all] → dc.securities(report=RPT_PCF10_INDUSTRY_DBFX,filter=(SECUCODE="{secucode}"),page_size=20)[all]⤵ |
| `f10_executive_hold_stock`<br>`高管持股变动/董监高持股变动/f10_executive_hold_stock` | F10高管持股变动 | table | - | code* | - | f10.module(code=code,module=f10_event).ggcgbd[all] → dc.securities(report=RPT_F10_TRADE_EXCHANGEHOLD,filter=(SECUCODE="{secucode}"),page_size=20)[all]⤵ |
| `f10_executive_salary`<br>`高管薪酬/薪酬排行/f10_executive_salary` | F10高管薪酬 | table | - | code*, page_size | - | dc.securities(report=RPT_F10_ORGINFO_SALARY,filter=(SECUCODE="{secucode}"),page_size=page_size)[all] |
| `f10_extra_indicators`<br>`补充指标/操盘必读补充/f10_extra_indicators` | F10操盘必读补充指标 | table | - | code* | - | f10.module(code=code,module=f10_required).zxzbOther[all] |
| `f10_forecast_detail`<br>`机构预测/机构盈利预测/f10_forecast_detail` | F10机构预测 | table | - | code* | - | f10.module(code=code,module=f10_forecast).jgyc[all] → dc.securities(report=RPT_HSF10_RES_ORGPREDICT,filter=(SECUCODE="{secucode}"),page_size=20)[all]⤵ |
| `f10_forecast_org_detail`<br>`预测明细/盈利预测明细/f10_forecast_org_detail` | F10预测明细 | table | - | code* | - | f10.module(code=code,module=f10_forecast).ycmx[all] → dc.securities(report=RPT_HSF10_RES_PREDICTDETAIL,filter=(SECUCODE="{secucode}"),page_size=20)[all]⤵ |
| `f10_forecast_stat`<br>`盈利预测统计/预测统计/f10_forecast_stat` | F10盈利预测统计 | table | - | code* | - | f10.module(code=code,module=f10_forecast).yctj_list[all] → dc.securities(report=RPT_HSF10_RESPREDICT_STATISTICS,filter=(SECUCODE="{secucode}"),page_size=20)[all]⤵ |
| `f10_fund_hold`<br>`基金持股/f10基金持仓/f10_fund_hold` | F10基金持股 | table | - | code*, page_size | - | f10.module(code=code,module=f10_holding).jjcg[all] |
| `f10_growth_compare`<br>`成长性比较/成长性对比/f10_growth_compare` | F10成长性比较 | table | - | code* | - | dc.securities(report=RPT_PCF10_INDUSTRY_GROWTH,filter=(SECUCODE="{secucode}"),page_size=20)[all] |
| `f10_guarantee`<br>`对外担保/担保/f10_guarantee` | F10对外担保 | table | - | code*, page_size | - | f10.module(code=code,module=f10_event).dwdb[all] → dc.securities(report=RPT_F10_ORGRES_GUARANTEE,filter=(SECUCODE="{secucode}"),page_size=page_size)[all]⤵ |
| `f10_holder_relation`<br>`股东关联关系/关联关系/f10_holder_relation` | F10股东关联关系 | table | - | code* | - | dc.securities(report=RPT_F10_EH_RELATION,filter=(SECUCODE="{secucode}"),page_size=20)[all] |
| `f10_industry_compared`<br>`行业综合对比/同行比较/f10_industry_compared` | F10行业综合对比 | table | - | code*, page_size | - | dc.securities(report=RPT_F10_INDUSTRY_COMPARED,filter=(SECUCODE="{secucode}"),page_size=page_size)[all] |
| `f10_issue_info`<br>`发行相关/发行信息/f10_issue_info` | F10发行相关 | table | - | code* | - | f10.module(code=code,module=f10_survey).fxxg[all] → dc.securities(report=RPT_PCF10_ORG_ISSUEINFO,filter=(SECUCODE="{secucode}"),page_size=5)[all]⤵ |
| `f10_lhb_stock`<br>`个股龙虎榜/f10龙虎榜/f10_lhb_stock` | F10龙虎榜单 | table | - | code* | - | f10.module(code=code,module=f10_event).lhbd[all] |
| `f10_limited_share`<br>`有限售流通股/限售股/f10_limited_share` | F10有限售流通股 | table | - | code* | - | f10.module(code=code,module=f10_holding).ltgf[all] → dc.securities(report=RPT_F10_FREE_TOTALHOLDNUM,filter=(SECUCODE="{secucode}"),page_size=20)[all]⤵ |
| `f10_litigation`<br>`诉讼仲裁/诉讼/f10_litigation` | F10诉讼仲裁 | table | - | code*, page_size | - | f10.module(code=code,module=f10_event).sszc[all] → dc.securities(report=RPT_LITIGATION_ARBITRATION_BSINFO,filter=(SECUCODE="{secucode}"),page_size=page_size)[all]⤵ |
| `f10_main_composition`<br>`主营构成/收入构成/f10_main_composition` | F10主营构成 | table | - | code*, page_size | - | f10.module(code=code,module=f10_business).zygcfx[all] → dc.securities(report=RPT_F10_FN_SEGMENTSV,filter=(SECUCODE="{secucode}"),page_size=page_size)[all]⤵ |
| `f10_main_indicators`<br>`主要指标明细/zyzb/f10_main_indicators` | F10主要指标明细 | table | - | code* | - | f10.module(code=code,module=f10_required).zyzb[all] |
| `f10_management_bio`<br>`管理层简介/高管简历/f10_management_bio` | F10管理层简介 | table | - | code*, page_size | - | dc.securities(report=RPT_F10_ORGINFO_MANAINTRO,filter=(SECUCODE="{secucode}"),page_size=page_size)[all] |
| `f10_margin_detail`<br>`个股融资融券/f10两融/f10_margin_detail` | F10融资融券明细 | table | - | code* | - | f10.module(code=code,module=f10_event).rzrq[all] |
| `f10_market_performance`<br>`市场表现/涨跌幅对比/f10_market_performance` | F10市场表现 | table | - | code* | - | f10.module(code=code,module=f10_industry).scbx[all] → dc.securities(report=RPT_PCF10_MARKETPER,filter=(SECUCODE="{secucode}"),page_size=20)[all]⤵ |
| `f10_org_holding`<br>`机构持仓明细/主力持仓/f10_org_holding` | F10机构持仓明细 | table | - | code*, page_size | - | dc.securities(report=RPT_F10_MAIN_ORGHOLDDETAILS,filter=(SECUCODE="{secucode}"),page_size=page_size)[all] |
| `f10_pledge_detail`<br>`股权质押明细/质押明细/f10_pledge_detail` | F10股权质押明细 | table | - | code* | - | f10.module(code=code,module=f10_event).gqzy[all] |
| `f10_project_progress`<br>`项目进度/募投项目/f10_project_progress` | F10募投项目进度 | table | - | code* | - | f10.module(code=code,module=f10_capital_op).xmjd[all] → dc.securities(report=RPT_F10_CAPITAL_ITEM,filter=(SECUCODE="{secucode}"),page_size=20)[all]⤵ |
| `f10_public_org_hold`<br>`参控股企业/参股企业/f10_public_org_hold` | F10参控股企业 | table | - | code*, page_size | - | dc.securities(report=RPT_F10_PUBLIC_OP_HOLDINGORG,filter=(SECUCODE="{secucode}"),page_size=page_size)[all] |
| `f10_qtr_main`<br>`单季主要指标/季度指标/f10_qtr_main` | F10单季主要指标 | table | - | code*, page_size | - | dc.securities(report=RPT_F10_QTR_MAINFINADATA,filter=(SECUCODE="{secucode}"),sort_columns=REPORT_DATE,page_size=page_size)[all] |
| `f10_rating_stat`<br>`评级统计/投资评级统计/f10_rating_stat` | F10评级统计 | table | - | code* | - | f10.module(code=code,module=f10_forecast).pjtj[all] → dc.securities(report=RPT_HSF10_RES_ORGRATING,filter=(SECUCODE="{secucode}"),page_size=20)[all]⤵ |
| `f10_rating_summary`<br>`研报摘要/最新研报/f10_rating_summary` | F10研报摘要 | table | - | code* | - | f10.module(code=code,module=f10_required).ybzy[all] |
| `f10_recapitalize`<br>`参控股/并购重组/重大重组/f10_recapitalize` | F10参控股/并购重组 | table | - | code*, page_size | - | dc.securities(report=RPT_ORG_RECAPITALIZE,filter=(SECUCODE="{secucode}"),sort_columns=NOTICE_DATE,page_size=page_size)[all] |
| `f10_related_concept`<br>`关联概念/同概念个股/f10_related_concept` | F10关联概念 | table | - | code* | - | dc.securities(report=RPT_F10_RELATE_GN,filter=(SECUCODE="{secucode}"),page_size=20)[all] |
| `f10_right_issue_detail`<br>`配股明细/配股/f10_right_issue_detail` | F10配股明细 | table | - | code*, page_size | - | f10.module(code=code,module=f10_bonus).pgmx[all] → dc.securities(report=RPT_F10_DIVIDEND_ALLOTMENT,filter=(SECUCODE="{secucode}"),page_size=page_size)[all]⤵ |
| `f10_seo_detail`<br>`增发明细/增发/f10_seo_detail` | F10增发明细 | table | - | code*, page_size | - | f10.module(code=code,module=f10_bonus).zfmx[all] → dc.securities(report=RPT_F10_DIVIDEND_SEO,filter=(SECUCODE="{secucode}"),page_size=page_size)[all]⤵ |
| `f10_staff_structure`<br>`员工结构/人员构成/f10_staff_structure` | F10员工结构 | table | - | code* | - | dc.securities(report=RPT_F10_STAFFCOMPETE_STRUCTURE,filter=(SECUCODE="{secucode}"),page_size=20)[all] → dc.securities(report=RPT_HSF9_BASIC_STAFFCOMPOSITION,filter=(SECUCODE="{secucode}"),page_size=20)[all]⤵ |
| `f10_stock_news`<br>`个股资讯/相关资讯/f10_stock_news` | F10个股资讯 | table | - | code* | - | f10.module(code=code,module=f10_news).gszx[all] |
| `f10_stock_notice`<br>`个股公告/公司公告/f10_stock_notice` | F10个股公告 | table | - | code* | - | f10.module(code=code,module=f10_news).gsgg[all] |
| `f10_tszb`<br>`特色指标/tszb/f10_tszb` | F10特色指标 | table | - | code* | - | f10.module(code=code,module=f10_required).tszb[all] |
| `f10_valuation_compare`<br>`估值比较/同行估值/f10_valuation_compare` | F10估值比较 | table | - | code* | - | dc.securities(report=RPT_PCF10_INDUSTRY_CVALUE,filter=(SECUCODE="{secucode}"),page_size=20)[all] |
| `f10_valuation_percentile`<br>`估值分位/估值百分位/f10_valuation_percentile` | F10估值分位 | table | - | code* | - | dc.securities(report=RPT_STOCKVALUATIONTANTILE,filter=(SECUCODE="{secucode}"),page_size=20)[all] |
| `f10_violation`<br>`违规处理/违规处罚/f10_violation` | F10违规处理 | table | - | code* | - | f10.module(code=code,module=f10_event).wgcl[all] → dc.securities(report=RPT_HSF9_OP_VIOLATION,filter=(SECUCODE="{secucode}"),page_size=20)[all]⤵ |
| `finance_dupont`<br>`杜邦分析/杜邦` | 杜邦分析 | table | - | code* | - | dc.securities(report=RPT_F10_FINANCE_DUPONT,filter=(SECUCODE="{secucode}"),page_size=20)[all] |
| `finance_main`<br>`财务指标/主要指标` | 主要财务指标 | table | - | code* | - | dc.securities(report=RPT_F10_FINANCE_MAINFINADATA,filter=(SECUCODE="{secucode}"),page_size=20)[all] |
| `financing_history`<br>`融资历史/募资` | 融资历史 | table | - | code* | - | f10.module(code=code,module=f10_capital_op).mjzjly[all] |
| `foreign_profile`<br>`港股概况/美股概况` | 港股/美股公司概况 | table | - | secucode* | - | f10.foreign(secucode=secucode) |
| `free_shareholders`<br>`流通股东/十大流通股东` | 十大流通股东 | table | - | code* | - | dc.securities(report=RPT_F10_EH_FREEHOLDERS,filter=(SECUCODE="{secucode}"),page_size=20)[all] |
| `hk_business`<br>`港股业务回顾/港股业务展望/hk_business` | 港股业务回顾 | table | - | code* | - | dc.securities(report=RPT_HKF10_ORG_BUSSINESS,filter=(SECURITY_CODE="{code}"),page_size=10)[all] |
| `hk_detail`<br>`港股大事提醒/hk_detail` | 港股大事提醒 | table | - | secucode* | - | f10.detail(secucode=secucode,kind=index)[all] |
| `hk_dividend`<br>`港股分红派息/港股分红/hk_dividend` | 港股分红派息 | table | - | code* | - | dc.securities(report=RPT_HKF10_MAIN_DIVBASIC,filter=(SECURITY_CODE="{code}"),page_size=20)[all] |
| `hk_equity`<br>`港股股本结构/hk_equity` | 港股股本结构 | table | - | code* | - | dc.securities(report=RPT_HKF10_INFO_EQUITY,filter=(SECURITY_CODE="{code}"),page_size=20)[all] |
| `hk_equity_change`<br>`港股历史股权变动/港股股权变动/hk_equity_change` | 港股历史股权变动 | table | - | code* | - | dc.securities(report=RPT_HKF10_SH_EQUITYCHG,filter=(SECUCODE="{code}.HK"),page_size=20)[all] |
| `hk_equity_str`<br>`港股股本构成/hk_equity_str` | 港股股本构成 | table | - | code* | - | dc.securities(report=RPT_HKF10_INFO_EQUITYSTR,filter=(SECURITY_CODE="{code}"),page_size=20)[all] |
| `hk_fn_balance`<br>`港股资产负债表/港股资产负债表/hk_fn_balance` | 港股资产负债表 | table | - | code*, page_size | - | dc.securities(report=RPT_HKF10_FN_BALANCE_PC,filter=(SECURITY_CODE="{code}"),page_size=page_size)[all] |
| `hk_fn_cashflow`<br>`港股现金流量表/hk_fn_cashflow` | 港股现金流量表 | table | - | code*, page_size | - | dc.securities(report=RPT_HKF10_FN_CASHFLOW_PC,filter=(SECURITY_CODE="{code}"),page_size=page_size)[all] |
| `hk_fn_income`<br>`港股利润表/hk_fn_income` | 港股利润表 | table | - | code*, page_size | - | dc.securities(report=RPT_HKF10_FN_INCOME_PC,filter=(SECURITY_CODE="{code}"),page_size=page_size)[all] |
| `hk_fn_indicator`<br>`港股财务主要指标/港股主要指标/hk_fn_indicator` | 港股财务主要指标 | table | - | code* | - | dc.securities(report=RPT_HKF10_FN_MAININDICATOR,filter=(SECURITY_CODE="{code}"),sort_columns=REPORT_DATE,page_size=20)[all] |
| `hk_fn_max`<br>`港股最新财务指标/hk_fn_max` | 港股最新财务指标 | table | - | code* | - | dc.securities(report=RPT_CUSTOM_HKF10_FN_MAININDICATORMAX,filter=(SECURITY_CODE="{code}"),page_size=5)[all] |
| `hk_holder_equity`<br>`港股董事及股东权益/港股股东权益/hk_holder_equity` | 港股董事及股东权益 | table | - | code* | - | dc.securities(report=RPT_HKF10_EQUITYCHG_HOLDER,filter=(SECURITY_CODE="{code}"),page_size=20)[all] |
| `hk_industry_growth`<br>`港股行业成长性对比/港股成长性对比/hk_industry_growth` | 港股行业成长性对比 | table | - | code* | - | dc.securities(report=RPT_PCF10_INDUSTRY_HKGROWTH,filter=(SECURITY_CODE="{code}"),page_size=20)[all] |
| `hk_industry_scale`<br>`港股行业规模对比/港股规模对比/hk_industry_scale` | 港股行业规模对比 | table | - | code* | - | dc.securities(report=RPT_PCF10_INDUSTRY_SCALE,filter=(SECURITY_CODE="{code}"),page_size=20)[all] |
| `hk_industry_value`<br>`港股行业估值对比/港股估值对比/hk_industry_value` | 港股行业估值对比 | table | - | code* | - | dc.securities(report=RPT_PCF10_INDUSTRY_HKCVALUE,filter=(SECURITY_CODE="{code}"),page_size=20)[all] |
| `hk_issue_date`<br>`港股发行关键日期/港股招股日期/hk_issue_date` | 港股发行关键日期 | table | - | code* | - | dc.securities(report=RPT_PCF10_ISSUEINFODATE,filter=(SECUCODE="{code}.HK"),page_size=5)[all] |
| `hk_issue_info`<br>`港股首发资料/港股发行资料/hk_issue_info` | 港股首发资料 | table | - | code* | - | dc.securities(report=RPT_HSPE_ISSUEINFO,filter=(SECUCODE="{code}.HK"),page_size=5)[all] |
| `hk_management`<br>`港股董事会/港股高管/hk_management` | 港股董事会成员 | table | - | code* | - | dc.securities(report=RPT_HKPCF10_BASIC_EXECUTIVEINFO,filter=(SECURITY_CODE="{code}"),page_size=20)[all] |
| `hk_market_perf`<br>`港股市场表现对比/港股市场表现/hk_market_perf` | 港股市场表现对比 | table | - | code* | - | dc.securities(report=RPT_PCF10_HKMARKETPER,filter=(SECURITY_CODE="{code}"),page_size=20)[all] |
| `hk_profile`<br>`港股公司资料/港股概况/hk_profile` | 港股公司资料 | table | - | code* | - | dc.securities(report=RPT_HKF10_INFO_ORGPROFILE,filter=(SECURITY_CODE="{code}"),page_size=5)[all] |
| `hk_rating`<br>`港股投资评级/港股评级/hk_rating` | 港股投资评级 | table | - | code* | - | dc.securities(report=RPT_HKPCF10_INFO_ORGRATING,filter=(SECURITY_CODE="{code}"),page_size=20)[all] |
| `hk_repo`<br>`港股回购/hk_repo` | 港股股票回购 | table | - | code* | - | dc.securities(report=RPT_HKF10_INFO_REPO,filter=(SECURITY_CODE="{code}"),page_size=20)[all] |
| `hk_security_info`<br>`港股证券资料/港股发行/hk_security_info` | 港股证券资料 | table | - | code* | - | dc.securities(report=RPT_HKF10_INFO_SECURITYINFO,filter=(SECURITY_CODE="{code}"),page_size=5)[all] |
| `hk_split`<br>`港股拆股合并/港股拆股/hk_split` | 港股拆股合并 | table | - | code* | - | dc.securities(report=RPT_HKF10_SH_SPLIT,filter=(SECURITY_CODE="{code}"),page_size=20)[all] |
| `holder_num_change`<br>`股东户数变动/户数变化` | 股东户数变动 | table | - | code* | - | dc.securities(report=RPT_F10_EH_HOLDERNUM,filter=(SECUCODE="{secucode}"),page_size=20)[all] |
| `industry_compare`<br>`行业对比/同行对比` | 行业对比 | table | - | code* | - | f10.module(code=code,module=f10_industry).czxbj[all] |
| `industry_rank`<br>`同行业个股排名/行业个股排名/关联个股/related_company` | 同行业个股排名 | table | - | code* | - | f10.module(code=code,module=f10_relation).ggpm[all] |
| `institutional_holding`<br>`机构持股/股东研究` | 机构持股 | table | - | code* | - | f10.module(code=code,module=f10_holding).jgcc[all] |
| `major_event`<br>`重大事项/诉讼处罚` | 重大事项 | table | - | code* | - | f10.module(code=code,module=f10_event).dstx[all] |
| `profile_basic`<br>`公司概况/基本信息/企业信息` | 公司概况 | table | - | code* | - | dc.securities(report=RPT_F10_ORG_BASICINFO,filter=(SECUCODE="{secucode}"),page_size=1)[all] |
| `shareholders`<br>`十大股东/股东` | 十大股东 | table | - | code* | - | dc.securities(report=RPT_F10_EH_HOLDERS,filter=(SECUCODE="{secucode}"),page_size=20)[all] |
| `us_detail`<br>`美股大事提醒/us_detail` | 美股大事提醒 | table | - | secucode* | - | f10.detail(secucode=secucode,kind=index)[all] |
| `us_dividend`<br>`美股分红派息/美股分红/us_dividend` | 美股分红派息 | table | - | code*, page_size | - | dc.securities(report=RPT_USF10_INFO_DIVIDEND,filter=(SECURITY_CODE="{code}"),page_size=page_size)[all] |
| `us_equity_change`<br>`美股股本变动/us_equity_change` | 美股股本变动 | table | - | code*, page_size | - | dc.securities(report=RPT_US10_INFO_EQUITY,filter=(SECURITY_CODE="{code}"),page_size=page_size)[all] |
| `us_fn_balance`<br>`美股资产负债表/us_fn_balance` | 美股资产负债表 | table | - | code*, page_size | - | dc.securities(report=RPT_USF10_FN_BALANCE,filter=(SECURITY_CODE="{code}"),page_size=page_size)[all] |
| `us_fn_cashflow`<br>`美股现金流量表/us_fn_cashflow` | 美股现金流量表 | table | - | code*, page_size | - | dc.securities(report=RPT_USSK_FN_CASHFLOW,filter=(SECURITY_CODE="{code}"),page_size=page_size)[all] |
| `us_fn_income`<br>`美股利润表/us_fn_income` | 美股利润表 | table | - | code*, page_size | - | dc.securities(report=RPT_USF10_FN_INCOME,filter=(SECURITY_CODE="{code}"),page_size=page_size)[all] |
| `us_fn_indicator`<br>`美股财务综合指标/us_fn_indicator` | 美股财务综合指标 | table | - | code*, page_size | - | dc.securities(report=RPT_USF10_FN_GMAININDICATOR,filter=(SECURITY_CODE="{code}"),page_size=page_size)[all] |
| `us_fund_hold`<br>`美股基金持股/us_fund_hold` | 美股基金持股 | table | - | code*, page_size | - | dc.securities(report=RPT_PCUSF10_STOCK_FOUND,filter=(SECURITY_CODE="{code}"),page_size=page_size)[all] |
| `us_holders`<br>`美股股东权益/美股持股人/us_holders` | 美股董事及股东权益 | table | - | code*, page_size | - | dc.securities(report=RPT_PCUSF10_STOCK_HOLDERS,filter=(SECURITY_CODE="{code}"),page_size=page_size)[all] |
| `us_holders_date`<br>`美股持股报告期/us_holders_date` | 美股持股报告期 | table | - | code* | - | dc.securities(report=RPT_PCUSF10_STOCK_DATEHOLDERS,filter=(SECURITY_CODE="{code}"),page_size=20)[all] |
| `us_insider_trade`<br>`美股高管交易/美股内部人交易/us_insider_trade` | 美股高管交易 | table | - | code*, page_size | - | dc.securities(report=RPT_PCUSF10_STOCK_LEADER,filter=(SECURITY_CODE="{code}"),page_size=page_size)[all] |
| `us_main_indicator`<br>`美股主要指标/美股核心指标/us_main_indicator` | 美股主要指标 | table | - | code* | - | dc.securities(report=RPT_USF10_DATA_MAININDICATOR,filter=(SECURITY_CODE="{code}"),page_size=5)[all] |
| `us_management`<br>`美股管理层/美股高管/us_management` | 美股公司管理层 | table | - | code*, page_size | - | dc.securities(report=RPT_USF10_BASIC_EXECUTIVEINFO,filter=(SECURITY_CODE="{code}"),page_size=page_size)[all] |
| `us_org_hold`<br>`美股机构持股/美股机构持股汇总/us_org_hold` | 美股机构持股汇总 | table | - | code*, page_size | - | dc.securities(report=RPT_PCUSF10_STOCK_ORGHOLD,filter=(SECURITY_CODE="{code}"),page_size=page_size)[all] |
| `us_org_hold_detail`<br>`美股机构持股明细/美股机构明细/us_org_hold_detail` | 美股机构持股明细 | table | - | code*, page_size | - | dc.securities(report=RPT_USF10_SH_ORGHOLDDETAILS,filter=(SECURITY_CODE="{code}"),page_size=page_size)[all] |
| `us_product_structure`<br>`美股主营构成/美股产品结构/us_product_structure` | 美股主营构成 | table | - | code*, page_size | - | dc.securities(report=RPT_USF10_INFO_PRODUCTSTRUCTURE,filter=(SECURITY_CODE="{code}"),page_size=page_size)[all] |
| `us_profile`<br>`美股公司概况/美股概况/us_profile` | 美股公司概况 | table | - | code* | - | dc.securities(report=RPT_USF10_INFO_ORGPROFILE,filter=(SECURITY_CODE="{code}"),page_size=5)[all] |
| `us_rating`<br>`美股机构评级/美股评级/us_rating` | 美股机构评级 | table | - | code*, page_size | - | dc.securities(report=RPT_USF10_INFO_ORGRATING,filter=(SECURITY_CODE="{code}"),page_size=page_size)[all] |
| `us_region_structure`<br>`美股地区构成/美股地区结构/us_region_structure` | 美股地区构成 | table | - | code*, page_size | - | dc.securities(report=RPT_USF10_INFO_REGIONSTRUCTURE,filter=(SECURITY_CODE="{code}"),page_size=page_size)[all] |
| `us_security_info`<br>`美股证券资料/us_security_info` | 美股证券资料 | table | - | code* | - | dc.securities(report=RPT_USF10_INFO_SECURITYINFO,filter=(SECURITY_CODE="{code}"),page_size=5)[all] |
| `us_short_selling`<br>`美股卖空明细/美股做空/us_short_selling` | 美股卖空明细 | table | - | code*, page_size | - | dc.securities(report=RPT_USF10_ANALYSIS_SHORT,filter=(SECURITY_CODE="{code}"),page_size=page_size)[all] |
| `us_split`<br>`美股拆股并股/美股拆股/us_split` | 美股拆股并股 | table | - | code*, page_size | - | dc.securities(report=RPT_USF10_SH_SPLIT,filter=(SECURITY_CODE="{code}"),page_size=page_size)[all] |
| `valuation_analysis`<br>`估值分析/估值` | 估值分析 | table | - | code* | - | f10.module(code=code,module=f10_industry).gzbj[all] |

## 股东与高管 `company`（12 个）

| 指标 | 名称 | kind | 单位 | 参数 | 口径 | 数据源链 |
| :- | :- | :-: | :-: | :- | :- | :- |
| `executive_hold_chart`<br>`高管增减持图/高管持股变动月度/executive_hold_chart` | 高管持股变动图 | series | - | date_from, page_size | market=all|sh|sz（默认 all） | dc.get(report=RPT_EXECUTIVESHARES_STATISTICS,filter=(TRADE_MARKET="{market_field}")(MOUNTH>='{date_from}'),sort_columns=MOUNTH,sort_types=1,page_size=page_size)[all] → dc.get(report=RPT_EXECUTIVESHARES_STATISTICS,filter=(TRADE_MARKET="{market_field}"),sort_columns=MOUNTH,sort_types=1,page_size=page_size)[all]⤵ |
| `executive_hold_detail`<br>`高管持股明细/高管变动明细/executive_hold_detail` | 高管持股变动明细 | table | - | code, person_name, page_size | - | dc.get(report=RPT_EXECUTIVE_HOLD_DETAILS,filter=(SECURITY_CODE="{code}")(PERSON_NAME="{person_name}"),sort_columns=CHANGE_DATE,SECURITY_CODE,PERSON_NAME,sort_types=-1,1,1,page_size=page_size)[all] → dc.get(report=RPT_EXECUTIVE_HOLD_DETAILS,filter=(SECURITY_CODE="{code}"),sort_columns=CHANGE_DATE,SECURITY_CODE,PERSON_NAME,sort_types=-1,1,1,page_size=page_size)[all]⤵ → dc.get(report=RPT_EXECUTIVE_HOLD_DETAILS,sort_columns=CHANGE_DATE,SECURITY_CODE,PERSON_NAME,sort_types=-1,1,1,page_size=page_size)[all]⤵ |
| `executive_hold_rank_in`<br>`高管增持/增持排行/executive_hold_rank_in` | 高管增持排行 | table | - | page_size | period=1m|1q|6m|1y|2y（默认 1m） | dc.get(report=RPT_EXECUTIVE_CHANGEHOLD_RANK,filter=(CHANGE_TYPE="01")(DATE_TYPE="{period_field}"),sort_columns=AMOUNT,page_size=page_size)[all] |
| `executive_hold_rank_out`<br>`高管减持/减持排行/executive_hold_rank_out` | 高管减持排行 | table | - | page_size | period=1m|1q|6m|1y|2y（默认 1m） | dc.get(report=RPT_EXECUTIVE_CHANGEHOLD_RANK,filter=(CHANGE_TYPE="02")(DATE_TYPE="{period_field}"),sort_columns=AMOUNT,sort_types=1,page_size=page_size)[all] |
| `gdfx_hold_analyse`<br>`股东持股分析/持有个股分析/gdfx_hold_analyse` | 股东持股分析 | table | - | end_date, page_size | scope=free|all（默认 free）；listing_state=free|all（默认 free） | dc.get(report={scope_field},filter={listing_state_field}(END_DATE='{end_date}'),sort_columns=END_DATE,page_size=page_size)[all] → dc.get(report={scope_field},filter=(END_DATE>='2015-03-31'),sort_columns=END_DATE,page_size=page_size)[all]⤵ |
| `gdfx_hold_change`<br>`股东持股变动/股东数变动/gdfx_hold_change` | 股东持股变动统计 | table | - | end_date, page_size | scope=free|all（默认 free） | dc.get(report={scope_field},filter=(END_DATE='{end_date}'),sort_columns=HOLDER_NUM,HOLDER_NEW,sort_types=-1,-1,page_size=page_size)[all] → dc.get(report={scope_field},filter=(END_DATE>='2015-03-31'),sort_columns=HOLDER_NUM,HOLDER_NEW,sort_types=-1,-1,page_size=page_size)[all]⤵ |
| `gdfx_hold_change_latest`<br>`最新股东变动/股东变动最新/gdfx_hold_change_latest` | 股东持股变动最新 | table | - | page_size | scope=free|all（默认 free） | dc.get(report={scope_field},sort_columns=HOLDER_NUM,HOLDER_NEW,sort_types=-1,-1,page_size=page_size)[all] |
| `gdfx_hold_detail`<br>`十大流通股东/十大股东明细/gdfx_hold_detail` | 十大股东持股明细 | table | - | end_date, page_size | scope=free|all（默认 free）；listing_state=free|all（默认 free） | dc.get(report={scope_field},filter={listing_state_field}(END_DATE='{end_date}'),page_size=page_size)[all] → dc.get(report={scope_field},filter={listing_state_field},page_size=page_size)[all]⤵ |
| `gdfx_hold_statistics`<br>`股东协同统计/协同持股/gdfx_hold_statistics` | 股东协同持股统计 | table | - | page_size | scope=free|all（默认 free） | dc.get(report={scope_field},sort_columns=STATISTICS_TIMES,page_size=page_size)[all] |
| `gdfx_hold_teamwork`<br>`股东协同/协同持股明细/gdfx_hold_teamwork` | 股东协同持股明细 | table | - | page_size | scope=free|all（默认 free）；holder_kind=all|person|fund|qfii|ssf|broker|trust（默认 all） | dc.get(report={scope_field},filter=(HOLDER_TYPE="{holder_kind_field}"),sort_columns=COOPERAT_NUM,page_size=page_size)[all] → dc.get(report={scope_field},sort_columns=COOPERAT_NUM,page_size=page_size)[all]⤵ |
| `gdfx_hot_holder`<br>`热门股东/股东协同变动/gdfx_hot_holder` | 热门股东（协同次数变动） | table | - | page_size | change=in|out|new（默认 in） | dc.get(report=RPT_COOPFREEHOLDERS_ANALYSISNEW,filter=(HOLDNUM_CHANGE_TYPE="{change_field}"),sort_columns=STATISTICS_TIMES,COOPERATION_HOLDER_MARK,sort_types=-1,-1,page_size=page_size)[all] |
| `gdfx_report_dates`<br>`股东报告期/十大股东报告期/gdfx_report_dates` | 股东分析报告期 | table | - | page_size | scope=free|all（默认 free） | dc.get(report={scope_field},filter=(END_DATE>='2015-03-31'),sort_columns=END_DATE,page_size=page_size)[all] |

## 资讯 `news`（10 个）

| 指标 | 名称 | kind | 单位 | 参数 | 口径 | 数据源链 |
| :- | :- | :-: | :-: | :- | :- | :- |
| `announcement_content`<br>`公告正文` | 公告正文 | table | - | art_code* | - | news.announcement_content(art_code=art_code) |
| `announcement_pdf`<br>`公告PDF/公告原文/定期报告PDF/招股书/公告附件/announcement_pdf` | 公告原文PDF | scalar | - | art_code* | - | news.announcement_pdf(art_code=art_code)[all] |
| `announcements`<br>`公告/公司公告` | 公告列表 | table | - | page_size | - | news.announcements(ann_type=A,page_size=page_size)[all] |
| `convertible_bond`<br>`可转债/转债申购/可转债申购/cb` | 可转债申购 | table | - | page_size | - | dc.get(report=RPT_BOND_CB_LIST,sort_columns=PUBLIC_START_DATE,page_size=page_size)[all] |
| `flash_news`<br>`快讯/7x24` | 财经快讯 | table | - | page_size | - | news.flash(page_size=page_size)[all] |
| `new_stock`<br>`新股/打新/新股日历` | 新股申购 | table | - | page_size | - | dc.get(report=RPTA_APP_IPOAPPLY,sort_columns=APPLY_DATE,page_size=page_size)[all] |
| `news`<br>`新闻/财经新闻` | 财经新闻 | table | - | page_size | - | news.news(page_size=page_size)[all] |
| `report_content`<br>`研报正文` | 研报正文 | table | - | info_code* | - | news.report_content(info_code=info_code) |
| `report_pdf`<br>`研报PDF/研报原文/研报附件/report_pdf` | 研报PDF原文 | scalar | - | info_code* | - | news.report_pdf(info_code=info_code)[all] |
| `reports`<br>`研报/研究报告` | 研报列表 | table | - | page_size | - | news.reports(page_size=page_size)[all] |

## 基金 `fund`（11 个）

| 指标 | 名称 | kind | 单位 | 参数 | 口径 | 数据源链 |
| :- | :- | :-: | :-: | :- | :- | :- |
| `etf_lof`<br>`etf/lof/场内基金` | ETF/LOF 场内基金 | table | - | page_size | - | quote.clist(fs=b:MK0021,b:MK0022,b:MK0023,page_size=page_size)[all] |
| `fund_codes`<br>`基金/fund_codes` | 基金代码表 | table | - | page_size | - | fund.codes(page_size=page_size)[all] |
| `fund_company`<br>`基金公司/基金公司排名/fund_company` | 基金公司列表 | table | - | page_size | - | fund.company(page_size=page_size)[all] |
| `fund_dividend`<br>`基金分红/基金拆分/分红送配/拆分折算/fund_dividend` | 基金分红送配/拆分 | table | - | code* | - | fund.dividend(code=code)[all] |
| `fund_holding`<br>`基金持仓/重仓股` | 基金持仓 | table | - | code* | - | fund.holding(code=code)[all] |
| `fund_manager`<br>`基金经理/管理人` | 基金经理 | table | - | code* | - | fund.manager(code=code) |
| `fund_nav`<br>`净值/单位净值/fund_nav` | 基金净值 | series | 元 | code* | - | fund.nav(code=code,page_size=10)[all] |
| `fund_rank`<br>`基金排行/基金排名` | 基金排行 | table | - | page_size | - | fund.rank(dt=kf,page_size=page_size)[all] |
| `fund_rating`<br>`基金评级/基金星级/fund_rating` | 基金评级 | table | - | page_size | - | fund.rating(page_size=page_size)[all] |
| `fund_report_pdf`<br>`基金报告/基金PDF` | 基金定期报告PDF | table | - | code* | - | fund.report_pdf(fund_code=code,page_size=5)[all] |
| `kzz_detail`<br>`可转债/可转债明细/转股价/转股价值/转股溢价率/可转债条款/kzz_detail` | 可转债数据中心 | table | - | page_size | - | ext.kzz_detail(page_size=page_size)[all] |

## 宏观 `macro`（25 个）

| 指标 | 名称 | kind | 单位 | 参数 | 口径 | 数据源链 |
| :- | :- | :-: | :-: | :- | :- | :- |
| `benchmark_interest_rate`<br>`存贷款基准利率/基准利率/存款利率/贷款利率/benchmark_interest_rate` | 存贷款基准利率 | series | % | page_size | - | dc.get(report=RPT_ECONOMY_DEPOSIT_RATE,sort_columns=REPORT_DATE,sort_types=-1,page_size=page_size)[all] |
| `commodity_index`<br>`商品指数/中证商品指数/工业品价格指数/commodity_index` | 商品指数（中证商品指数） | series | - | indicator_id, page_size | - | ext.commodity_index(indicator_id=indicator_id,page_size=page_size)[all] |
| `cpi`<br>`CPI/居民消费价格指数` | 居民消费价格指数（CPI） | series | % | page_size | - | macro.domestic(indicator=cpi,page_size=page_size)[all] |
| `deposit_reserve_rate`<br>`存款准备金率/准备金率/存款准备金/deposit_reserve_rate` | 存款准备金率 | series | % | page_size | - | dc.get(report=RPT_ECONOMY_DEPOSIT_RESERVE,sort_columns=TRADE_DATE,sort_types=-1,page_size=page_size)[all] |
| `electricity`<br>`用电量/电力` | ~~全社会用电量~~ ⚠️上游已下线 | series | - | page_size | - | macro.domestic(indicator=electricity,page_size=page_size)[all] |
| `fiscal`<br>`财政/财政收入` | 财政收支 | series | % | page_size | - | macro.domestic(indicator=fiscal,page_size=page_size)[all] |
| `forex_loan`<br>`外汇贷款/金融机构外汇贷款/forex_loan` | 金融机构外汇贷款 | series | - | page_size | - | dc.get(report=RPT_ECONOMY_FOREX_LOAN,sort_columns=REPORT_DATE,sort_types=-1,page_size=page_size)[all] |
| `forex_reserve`<br>`外汇储备/外储` | 外汇储备 | series | - | page_size | - | macro.domestic(indicator=forex_reserve,page_size=page_size)[all] |
| `gdp`<br>`GDP/国内生产总值` | 国内生产总值（GDP） | series | % | page_size | - | macro.domestic(indicator=gdp,page_size=page_size)[all] |
| `global_interest_rate`<br>`全球利率/主要国家利率/全球央行利率/global_interest_rate` | 全球主要国家利率 | table | - | page_size | - | dc.get(report=RPT_MAIN_COUNTRY_IR,page_size=page_size)[all] |
| `lpr`<br>`LPR/贷款基准利率` | 贷款市场报价利率（LPR） | series | % | page_size | - | macro.domestic(indicator=lpr,page_size=page_size)[all] |
| `m2`<br>`M2/货币供应量` | 货币供应量（M2） | series | % | page_size | - | macro.domestic(indicator=m2,page_size=page_size)[all] |
| `macro_business_climate`<br>`企业景气指数/企业家信心指数/macro_business_climate` | 企业景气及企业家信心指数 | series | - | page_size | - | macro.domestic(indicator=business_climate,page_size=page_size)[all] |
| `macro_gold_reserve`<br>`黄金储备/央行黄金/macro_gold_reserve` | 黄金储备 | series | - | page_size | - | macro.domestic(indicator=gold_reserve,page_size=page_size)[all] |
| `macro_house_index`<br>`国房景气指数/房价指数/macro_house_index` | 国房景气指数 | series | - | page_size | - | macro.domestic(indicator=house_index,page_size=page_size)[all] |
| `macro_indicator_history`<br>`指标历史/行业指标历史/macro_indicator_history` | 宏观/行业指标历史序列 | series | - | indicator_id*, page_size | - | macro.indicator_history(indicator_id=indicator_id,page_size=page_size)[all] |
| `macro_indicator_list`<br>`行业指数/宏观指标库/行业指标/macro_indicator_list` | 宏观/行业指标库 | table | - | page_size | - | macro.indicator_list(page_size=page_size)[all] |
| `macro_industrial_va`<br>`工业增加值/工业增长/macro_industrial_va` | 工业增加值增长 | series | % | page_size | - | macro.domestic(indicator=industrial_va,page_size=page_size)[all] |
| `macro_money_supply`<br>`货币供应量/货币供应/M0/M1/macro_money_supply` | 货币供应量（M0/M1/M2） | series | - | page_size | - | macro.domestic(indicator=money_supply,page_size=page_size)[all] |
| `macro_overseas`<br>`海外宏观/海外经济` | 海外宏观经济 | table | - | economy, page_size | - | macro.overseas(economy=economy,page_size=page_size)[all] |
| `macro_trade`<br>`进出口/海关进出口/外贸/macro_trade` | 海关进出口 | series | - | page_size | - | macro.domestic(indicator=trade,page_size=page_size)[all] |
| `pmi`<br>`PMI/采购经理指数` | 制造业PMI | series | % | page_size | - | macro.domestic(indicator=pmi,page_size=page_size)[all] |
| `ppi`<br>`PPI/工业品价格` | 工业生产者出厂价格指数（PPI） | series | % | page_size | - | macro.domestic(indicator=ppi,page_size=page_size)[all] |
| `shibor`<br>`Shibor/SHIBOR/拆借利率/同业拆借利率/上海银行间拆借利率/银行间拆借/shibor` | 同业拆借利率 | series | % | page_size | market=shibor|chibor|libor|hibor（默认 shibor） | dc.get(report=RPT_IMP_INTRESTRATEN,filter=(LATEST_RECORD=1)(MARKET_CODE="{market_field}"),sort_columns=INDICATOR_ID,sort_types=1,page_size=page_size)[all] |
| `shzr`<br>`社融/社会融资` | ~~社会融资规模~~ ⚠️上游已下线 | series | - | page_size | - | macro.domestic(indicator=shzr,page_size=page_size)[all] |

## 股吧 `guba`（4 个）

| 指标 | 名称 | kind | 单位 | 参数 | 口径 | 数据源链 |
| :- | :- | :-: | :-: | :- | :- | :- |
| `guba_comments`<br>`评论/帖子评论` | 股吧评论 | table | - | code*, post_id* | - | guba.comments(code=code,post_id=post_id,page=1)[all] |
| `guba_post_content`<br>`帖子正文` | 股吧帖子正文 | table | - | code*, post_id* | - | guba.post_content(code=code,post_id=post_id) |
| `guba_posts`<br>`股吧帖子/帖子/股吧` | 股吧帖子列表 | table | - | code*, page | - | guba.posts(code=code,page=page,limit=20)[all] |
| `guba_rank`<br>`人气榜/热度排行` | 股吧人气榜 | table | - | ps | - | guba.rank(ps=ps)[all] |

## 工具 `tool`（7 个）

| 指标 | 名称 | kind | 单位 | 参数 | 口径 | 数据源链 |
| :- | :- | :-: | :-: | :- | :- | :- |
| `backtest`<br>`回测/组合回测` | 组合回测 | table | - | weights*, period_returns* | - | tool.backtest(weights=weights,period_returns=period_returns) |
| `diagnosis`<br>`诊断/评分/个股诊断` | 个股诊断评分 | scalar | 分 | code* | - | tool.diagnosis(code=code).diagnosis_score |
| `finance_infographic`<br>`财报图解/财报图` | 财报图解 | table | - | code* | - | tool.finance_infographic(code=code) |
| `fund_calc`<br>`定投/定投计算器/fund_calculator` | 基金定投计算 | table | - | code*, monthly_amount, months, annual_rate | - | tool.fund_calc(fund_code=code,monthly_amount=monthly_amount,months=months,annual_rate=annual_rate) |
| `index_valuation`<br>`指数估值/估值分位` | 指数估值 | table | - | - | - | tool.index_valuation[all] |
| `interactive`<br>`互动/问董秘/董秘回复` | 互动易问答 | table | - | code* | - | tool.interactive(code=code,page_size=10)[all] |
| `main_monitor`<br>`主力监控/主力资金` | 主力监控 | table | - | page_size | - | tool.main_monitor(page_size=page_size)[all] |

## 数据中心事件 `event`（20 个）

| 指标 | 名称 | kind | 单位 | 参数 | 口径 | 数据源链 |
| :- | :- | :-: | :-: | :- | :- | :- |
| `bgcz`<br>`并购/重组/并购重组` | 并购重组 | table | - | page_size | - | dc.get(report=RPTA_WEB_BGCZMX,page_size=page_size)[all] |
| `company_invest`<br>`公司投资/证券投资` | 公司证券投资 | table | - | page_size | - | dc.get(report=RPTA_WEB_ZQTZMX,page_size=page_size)[all] |
| `consistent_action`<br>`一致行动人` | 一致行动人 | table | - | page_size | - | dc.get(report=RPTA_WEB_YZXDRINDEX,sort_columns=NOTICEDATE,page_size=page_size)[all] |
| `entrust_financing`<br>`委托理财/理财` | 委托理财 | table | - | page_size | - | dc.get(report=RPTA_WEB_WTLCMX,page_size=page_size)[all] |
| `executive_hold`<br>`高管增持/高管减持` | 高管增减持 | table | - | page_size | - | dc.get(report=RPT_EXECUTIVE_HOLD_DETAILS,sort_columns=CHANGE_DATE,page_size=page_size)[all] |
| `futures_lhb`<br>`期货龙虎榜/期货持仓` | 期货龙虎榜 | table | - | page_size | - | dc.get(report=RPT_FUTU_DAILYPOSITION,sort_columns=TRADE_DATE,page_size=page_size)[all] |
| `goodwill`<br>`商誉` | 商誉 | table | - | page_size | - | dc.get(report=RPT_GOODWILL_MARKETSTATISTICS,sort_columns=REPORT_DATE,page_size=page_size)[all] |
| `hsgt_hold`<br>`港通持股/北向持股` | 沪深港通持股 | table | - | page_size | - | dc.get(report=RPT_MUTUAL_HOLD,sort_columns=HOLD_DATE,page_size=page_size)[all] |
| `ipo_calendar`<br>`新股日历/申购日历` | 新股日历 | table | - | page_size | - | dc.get(report=RPT_IPO_CALENDAR,sort_columns=TRADE_DATE,page_size=page_size)[all] |
| `ipo_review`<br>`IPO审核/上市审核` | IPO审核 | table | - | page_size | - | dc.get(report=RPT_IPO_INFOALLNEW,sort_columns=ACCEPT_DATE,page_size=page_size)[all] |
| `major_contract`<br>`重大合同/合同` | 重大合同 | table | - | page_size | - | dc.get(report=RPTA_WEB_ZDHT_LIST,sort_columns=DIM_RDATE,page_size=page_size)[all] |
| `market_valuation`<br>`市场估值/全市场估值` | 市场估值 | table | - | page_size | - | dc.get(report=RPT_VALUEMARKET,sort_columns=TRADE_DATE,page_size=page_size)[all] |
| `refinance`<br>`转融通/融券` | 转融通明细 | table | - | page_size | - | dc.get(report=RPT_REFINANCE_TRAN_DEL,sort_columns=TRADE_DATE,page_size=page_size)[all] |
| `related_trade`<br>`关联交易` | 关联交易 | table | - | page_size | - | dc.get(report=RPT_RELATED_TRADE,page_size=page_size)[all] |
| `right_issue`<br>`配股` | 配股 | table | - | page_size | - | dc.get(report=RPT_RIGHT_ISSUE,page_size=page_size)[all] |
| `share_repurchase`<br>`回购/股份回购` | 股票回购 | table | - | page_size | - | dc.get(report=RPTA_WEB_GETHGLIST_NEW,page_size=page_size)[all] |
| `shareholder_hold`<br>`股东持股/大股东` | 股东持股排行 | table | - | page_size | - | dc.get(report=RPTA_WEB_GDGGLB,page_size=page_size)[all] |
| `shareholder_meeting`<br>`股东大会` | 股东大会 | table | - | page_size | - | dc.get(report=RPT_GENERALMEETING_DETAIL,sort_columns=NOTICE_DATE,page_size=page_size)[all] |
| `stock_comment`<br>`千股千评/股票评论` | 千股千评 | table | - | page_size | - | dc.get(report=RPT_DMSK_TS_STOCKNEW,sort_columns=TRADE_DATE,page_size=page_size)[all] |
| `suspend`<br>`停牌/复牌/停复牌` | 停复牌 | table | - | trade_date, page_size | - | event.suspend(trade_date=trade_date,page_size=page_size)[all] |

