# 数据与搜索接入
现有注册表包含LinkFox、Tushare、东方财富、Wind、晨星、恒生聚源，不含NeoData/WeStock。注册不等于有账号或当前工具可执行。来源可替代但覆盖/字段/时效不等价，报告披露实际使用的服务和原始数据来源。
LinkFox：prepare kind=search得到proxy_call的toolName=aiMode/googleSearch/arguments.keyword。查询公开信息且不包含私有材料；返回stdout/链接只作discovery。要有原披露正文/页码或实际金融服务数据才能支持数值，不能把AI概述当已核实财报。
Tushare：prepare kind=price，仅ts_code（六位.SH/.SZ/.BJ）和trade_date（YYYYMMDD）；实际工具tushare_daily，原Native资格及逐次审批。输出单行rows，精确代码/日期，close仅未复权价格，不能自己补股数求市值。
金融数据：prepare kind=finance仅接受现有四服务之一、当前Native暴露的tool{name,title,inputSchema}、arguments和具体purpose。title为“service · upstreamName”，公开name依现有Host算法匹配；此一致性不是资格证明。脚本不自建schema宽松校验器，原Broker必须以当前冻结schema真正验证并审批。方法名从当前工具列表读取，不使用示例合成名作为线上方法。仅数据/文档研究，不批准交易/自选变更/分发。
observe保留实际参数、source_operation_id、retrieved_on和MCP结果，错误/不明成功码停止。金融服务响应不统一，只标source_requires_review，不套NeoData字段、不猜单位。资源已安装不代表上述服务可用。
官方核对：Tushare公开daily文档https://tushare.pro/document/2?doc_id=27；东方财富妙想官方2026-09-24公告说明数据/资料场景，但未给本机账号工具schema；LinkFox公开仓库aiMode/googleSearch参考。仅公开GET，不做账号认证、tools/list或业务调用。当前内置web_search仍disabled。
