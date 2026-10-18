# 年度FCFF与可比估值

Ke×E权重 + **税前Kd×(1−T)×D权重**。税盾仅一次。FCFF=EBIT−max(EBIT,0)×税率+折旧摊销−资本支出−营运资本增加。按年度年末折现，终值FCFF_n×(1+g)/(WACC−g)；WACC必须>g且>0，终期FCFF须>0。缺净债务不出股权值，缺股数不出每股值。亏损/零分母或非正分子倍数为NM，不参与均值；当前只计算PE、EV/EBITDA。

一次税盾例：Ke10%、税前Kd5%、税25%、E/D各50%得6.875%。上游双税盾6.40625%已排除。方法核对：NYU Damodaran《Valuation: Principles and Practice》https://pages.stern.nyu.edu/~adamodar/pdfiles/acf3E/book/ch12.pdf ，查阅2026-10-17。不是当前市场利率来源。

XLSX保留真实公式及缓存；Inputs独占基础假设，DCF计算，Summary引用结果，History独立核对，Sensitivity显式情景列表使用普通折现公式（不是Excel What-If Data Table）。改变用户输入须重跑生成一致的JSON/HTML/XLSX；直接在工作簿编辑仅更新该工作簿，不更新旁边报告。财务输入的真实性与预测合理性不会因数学闭合而自动通过。

0.1.1补充：memo-facts.md提供实际同比、逐个敏感性格相对基准变化和终值占比。结果只描述计算，不推断利润变化原因；净利润与EBIT差异缺费用/税项等明细时无法归因。敏感性相对基准变化是整组假设情景的差，不能声称所有单变量±1个百分点都有统一区间效果。

## 更新比较的确定性交付
更新模型必须传入 --previous-input <上一版/input.json>。计算器重新计算两份输入，自动生成 comparison.json、previous-input.json、change-note.md 并纳入 receipt；不得重写这些文件。两版必须同公司、同币种、同金额倍率与同方法；不拿不同主体或单位硬比。比较是当前计算器对两份输入的结果，不伪称旧计算器版本复现。
研究备忘录和最终回复直接引用 change-note.md 的数值，不重新手写差异表或心算百分比。未知/上版非正的相对变化为 N/A；股数固定时股权和每股价值相对变化必须一致。敏感性格内EV与相对各自基准的变化分开；不得一概说“方向相反”。终值来自 result.json，不填猜测的近似数。所有额外派生数字先另存可复算脚本及实际结果，缺少已执行计算则省略该数字。
