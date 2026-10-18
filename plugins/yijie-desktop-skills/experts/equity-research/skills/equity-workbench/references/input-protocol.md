# 输入与运行

`python3 -B <本包>/scripts/equity.py --input <授权输入.json> --output <工作区新目录>`。输出目录父目录须存在，不覆盖旧目录。完整普通合成 schema 见 examples/input.json。

schema_version=1；company、currency、amount_scale（1/1000/10000/1e6/1e8），as_of=YYYY-MM-DD，period_basis=annual，discount_timing=year-end。所有金额同币种和倍率，没有自动FX。sources每项id/kind(synthetic/user-file/qualified-connector)/locator/as_of/description；每个history/forecast/comps及assumptions须source_id。

history须2–10期连续年报：period_start/end，assets/liabilities/equity，cash_begin/end、cfo/cfi/cff/fx，revenue/ebit/net_income/noncash_adjustments/change_working_capital。经营现金流=净利润+非现金调整−营运资本变化；差异超过币种0.01拒绝，不自动补平。

assumptions：cost_equity/debt_cost_pretax/tax_rate/equity_weight/debt_weight以小数明确，权重和1，rationale说明依据；terminal_growth、net_debt、diluted_shares。net_debt是包含全部权益桥接调整后的净扣减（正为扣减，净现金为负），没有资料就null。diluted_shares是实际股数，未知null，不按金额倍率缩放。每股值=股权价值×amount_scale/股数。

forecast 1–10年，year连续1..N代表估值日起逐年年末，ebit/da/capex/delta_wc同金额单位；预测是假设，不能生成后称来源事实。亏损EBIT不产生即期税收退款。sensitivity显式wacc/growth列表各1–9项，WACC≤g格不可用。comps可空；每家公司须name/source_id/currency/amount_scale/as_of/period_start/end/market_cap/net_debt/ebitda/net_income，同币种、时点和最新年度利润期间，缺数据null。

更新：另存 input-v2.json，使用新输出目录v2。读取两版result比较WACC、现金流、EV与每股值，另写change-note.md列输入变更依据。不能直接改result、XLSX缓存或回执。计算器输出research.md仅说明口径；另写研究备忘录标事实/假设/判断，引用来源和结果。

浏览器交互：`python3 -B <本包>/scripts/preview.py --project <输出目录>`，只提供receipt一致的4个静态文件，输出随机loopback端口，输入stop正常关闭。复制代码支持 `python3 -B equity.py --input input.json --output ../新目录`，原report.css须保留。
