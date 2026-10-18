# 15项有效流程映射

同一个私有入口，按用户任务选用。研究文稿是模型基于明确证据生成，计算仅调用已实现helper；不能把文字路由等同于已验收全部高级功能。

| 上游ID | 任务 | 本期交付与边界 |
|---|---|---|
| catalyst-calendar | 催化日历 | 有来源事件日期、时区、确定/预计、影响与后续核验；保存CSV/MD，不自动建日历或监控 |
| company-tearsheet | 公司速览 | 业务事实、报告期核心财务、未知项、风险与来源；保存一页MD |
| earnings-analysis | 业绩前瞻/解读 | 先核发布状态，实际/指引/共识分列；共识缺失不做Beat/Miss；MD，非8–12页DOCX |
| idea-generation | 研究候选 | 仅用户给定样本与明确条件，保留筛选范围与缺值；CSV/MD，不自动全市场扫描 |
| initiating-coverage | 首次覆盖 | 证据研究稿和有界模型；原6页签三表预测+4估值页签、25–35图和30–50页DOCX未实现 |
| model-update | 模型更新 | 原input/result→变更来源→新目录完整重跑→change-note；不改旧结果 |
| morning-note | 晨报 | 仅有时点证据的消息，不把没取数写成无新闻；MD，不代发邮件 |
| sector-overview | 行业概览 | 明确行业/地域/年份和样本，来源/假设分离；MD，不保证PPT/DOCX |
| thesis-tracker | 论点跟踪 | 论点、支持/反证、日期、来源、待证伪条件；保存版本化JSON/MD，不自动常驻 |
| comps-valuation | 可比估值 | 同币种/期间/时点，PE与EV/EBITDA由helper计算，选入理由人工审阅；XLSX/HTML |
| dcf-model-builder | DCF | 真实年度FCFF、历史三表核对和敏感性；不是完整预测三表或亏损重组模型 |
| long-short-pitch | 多空论证 | 基于证据分别论点/反证/催化/未知，MD；不假造做空资格、头寸或执行建议 |
| memo-builder | 研究备忘录 | 业务/证据/估值/假设/反证/待确认项；无概率不填概率，无当前价不报上行 |
| event-scenario-analyzer | 事件情景 | 有来源事件和用户明确假设另存模型，比较结果；没有事件统计/蒙特卡洛引擎 |
| portfolio-risk | 风险研究 | 持仓单位、成本、资金规模和约束须明确，MD列风险；无自动风险计算/对冲/调仓引擎 |

earnings-preview已废弃并入earnings-analysis，不注册。外部Figma/Bloomberg/FactSet/Google Calendar不是本包提供的工具。
