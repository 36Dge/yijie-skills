# 输入与运行

`python3 -B <本包>/scripts/backtest.py --input <输入.json> --output <工作区新目录>`。父目录须存在，新目录不可已存在。完整示例examples/input.json仅合成验收，不能作真实历史价格。

schema_version=1；symbol/currency/timezone/universe_selection/assumption_rationale显式；frequency=daily，price_adjustment=raw，corporate_actions=none-in-window。仅无分红拆股等公司行为的原始日线区间；其他口径先停止解释未实现。
sources含id/kind/locator/as_of/description，price_source_id/calendar_source_id必须存在。calendar是包含预热与评估全部session的严格升序唯一日期；bars必须逐项相符。start是明确session，end须最后一条，不能静默截期。

bars每项date/open/close/buyable/sellable。收盘价不能缺失、不前填；仅当两侧不可交易时允许open=null。买卖可成交标记必须用户数据明确提供，涵盖停牌、涨跌停等真实限制，helper无法独立证明流动性。也可用bars_file引用输入旁相对CSV，列名同上，true/false小写，open空代表null；不能同时给bars。

initial_cash>0，annual_sessions整数，risk_free_annual显式小数。execution: signal_timing=close，fill_timing=next-session-open，unfilled_policy=cancel，end_position=mark-to-close，lot_size整数，minimum_holding_sessions整数（T+1填1），allocation为每次买入现金比例；buy_commission/sell_commission/sell_tax/slippage为小数，minimum_commission为单笔最小费用。

strategy: sma_cross {fast,slow}（fast<slow，预热至少slow个session）；或close_signals {source_id,signals:[{date,known_at_close,action}]}，每session最多一个buy或sell，known_at_close须同date。这是输入陈述，不证明来源真实无前视。预热中的信号不产生订单。首版只全仓卖出现有持股，不做加仓、部分卖、网格、多资产、空头、衍生品、事件研究。

输出equity/trades/fills三个CSV，summary.json、decisions.json、input.json、method.md、代码和HTML。net_return是买卖费用与卖税后收益，gross_price_return另列；单位小数非百分数。未平仓持股及浮动损益单列，不计为已平仓胜率。更新参数须另存新input和新目录，比较两版文件，不修改原产物。

交互预览 `python3 -B <本包>/scripts/preview.py --project <结果目录>`；正常输入stop退出。复制代码复算 `python3 -B backtest.py --input input.json --output ../新目录`。原report.css保留，不依赖安装包位置。
