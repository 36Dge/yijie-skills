# 年度FCFF与可比估值

Ke×E权重 + **税前Kd×(1−T)×D权重**。税盾仅一次。FCFF=EBIT−max(EBIT,0)×税率+折旧摊销−资本支出−营运资本增加。按年度年末折现，终值FCFF_n×(1+g)/(WACC−g)；WACC必须>g且>0，终期FCFF须>0。缺净债务不出股权值，缺股数不出每股值。亏损/零分母或非正分子倍数为NM，不参与均值；当前只计算PE、EV/EBITDA。

一次税盾例：Ke10%、税前Kd5%、税25%、E/D各50%得6.875%。上游双税盾6.40625%已排除。方法核对：NYU Damodaran《Valuation: Principles and Practice》https://pages.stern.nyu.edu/~adamodar/pdfiles/acf3E/book/ch12.pdf ，查阅2026-10-17。不是当前市场利率来源。

XLSX保留真实公式及缓存；Inputs独占基础假设，DCF计算，Summary引用结果，History独立核对，Sensitivity显式情景列表使用普通折现公式（不是Excel What-If Data Table）。改变用户输入须重跑生成一致的JSON/HTML/XLSX；直接在工作簿编辑仅更新该工作簿，不更新旁边报告。财务输入的真实性与预测合理性不会因数学闭合而自动通过。
