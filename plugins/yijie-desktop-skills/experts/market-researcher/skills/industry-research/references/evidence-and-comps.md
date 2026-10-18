# 证据与可比计算
scope明确currency、basis=FY/LTM、period_start/end（约完整一年）、valuation_date和ebitda_definition。日期不从运行时间猜，不混FY/NTM/季度；按用户研究截止日阻止后来发布的信息混入历史研究。
sources记录id/kind/title/locator/published_on/retrieved_on/content/entity_ids/period_ends；kind为issuer/exchange/provider/user/search。provider/search附原始receipt，正文须来自对应回执。引用不能只有虚构URL：issuer/user需实际读取材料并摘录原文；机械校验不认证URL、全文或含义。只读摘要不得标issuer。源文件实际路径/页码或真实URL保留，不自动联网打开。
每公司entity_id需交易所/类别明确，name、business_model、8个metrics。每metric有value、scale（1/千/百万/十亿）、currency、basis、period_start/end、as_of、definition、source_id和原文quote。来源entity_ids/period_ends从实际文档标题/表头或原回执核对登记；引用段须确在保留正文中，数值按完整数字匹配，不能把1000中的100当来源。代码不认证来源索引或上下文含义，仍需实际核对，不拼接伪造原句。
营业收入/EBITDA/净利润采用统一FY/LTM起止期；债务/现金/优先股/少数股权为财务期末instant；market_cap为估值日instant（period_end仍表示本次比较采用的财务期）。引用发布日不可晚于研究截止日，也不能早于声称已知的数据日期。缺失或冲突该项为N/A并保留问题。
统一金额到目标币种百万单位，仅做显式scale转换，不自动FX。EV=市值+债务+优先股+少数股权−现金，五项缺一不算EV。EV/Revenue、EV/EBITDA、P/E只在分子/分母正值时计算，负/零盈利为NM；EBITDA率可为负。统计逐列只纳入有效值并显示样本数，不把缺值当零。不同EBITDA定义/时间/币种不能纳入；定义相同也不代表业务可比，仍保留说明。
研究段落kind=fact/analysis/unknown，来源ID必须存在；非unknown至少有非search来源。代码不判断自然语言是否真的受来源支持，模型质量/财务语义仍需实际复核。原包IFERROR(...,0)、绝对毛利率层级与示例数字不采用。
