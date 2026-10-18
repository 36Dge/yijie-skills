# 来源匹配
每条原始观察保存query、request、source_operation_id、captured_at和mcp_result。query必须包含method、target_asin、market=US，request必须与prepare完全相等；匹配不等于证明服务器来源，需复核Native工具历史。

- Keepa商品：products按完整ASIN唯一匹配，USD/$币种。不能用父体/邻近ASIN或第一个商品。
- Keepa历史：顶层对象或列表按完整asin唯一匹配；buyboxPrice不跨产品借用。选中某个value时保留其time，并说明采样价不保证当前可成交。历史无币种回显时，仅按显式US请求与来源文档口径处理；不能换汇猜测。
- SIF汇总：按asin唯一；SP词数不存在保持缺失，真实0也不代表零广告支出。关键词逐条按目标筛选。
- SellerSprite：顶层asin和marketplace都匹配，不能把站点缺失当US。
- 1688：目标由原始请求上下文绑定，产品以offerId唯一选择；products.asin是货源编号。重复offer（如多个变体）不挑第一条，要求获得可唯一定位报价资料。variant/报价确认单另外明确，列表价不证明对应SKU价格。
- 细分市场：按用户明确选中的nicheId唯一匹配；关键词/站点由原请求保留，nicheTitle只做解释。ACoS不可直接换成TACoS。
- Amazon搜索/Google：候选/研究态，不作为利润直接数值证据。

calculate重新检查所有原始观察，不接收手工改好的normalized回执代替。source_operation_id重复即停止，不覆盖；某条失败保留source_failures，受影响候选标incomplete。observed价格必须引用匹配行的精确字段与原数值、相同时间戳；其它费用使用明确user_scenario并附资料来源。假设不是已验证的商家事实。
