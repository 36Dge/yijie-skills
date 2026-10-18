# 本地命令与私有格式
在当前任务目录执行安装资源中的scripts/research.py。Python3标准库，--input为JSON文件，--output-dir必须是当前任务下不存在的新目录；保留旧输出，不覆盖。
python3 <resource>/scripts/research.py prepare --input query.json --output-dir prepared
python3 <resource>/scripts/research.py observe --input receipt.json --output-dir observed
python3 <resource>/scripts/research.py build --input research.json --output-dir research-output
prepare输入kind=search/query，或kind=price/ts_code/trade_date，或kind=finance/service_id/tool/arguments/purpose。金融tool必须来自当前Native元数据；脚本只做计划，不签发权限、不执行网络或自建OAuth。
observe包含plan、actual_service_id、actual_tool_name、actual_arguments、source_operation_id、retrieved_on与mcp_result。支持structuredContent或单text块，原金融JSON/文本保留为待复核资料；search只能discovery_only，Tushare只unadjusted_price_only。工具错误、不同参数或行情代码/日期、空数据拒绝。
build完整示例见examples/research.json。sources和companies/metrics私有格式见evidence-and-comps.md，四研究sections（overview/competition/valuation/watchlist）必填，允许明确unknown。未读来源不创建虚构issuer记录。build先校验，缺失指标在issues保留，不丢掉公司；根格式或重复身份错误停止。生成input.json/inspection.json/report.html/comps.xlsx，schema_version=1仅私有工件，不是公共契约或执行凭证。
