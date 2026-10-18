# 本地辅助命令
在当前任务可写目录执行安装资源中的scripts/sourcing.py，使用Python3标准库，无第三方安装/网络。--input是UTF-8 JSON文件，--output-dir必须是当前任务下不存在的新目录；不覆盖历史。

python3 <resource>/scripts/sourcing.py prepare --input query.json --output-dir prepared
python3 <resource>/scripts/sourcing.py observe --input observation.json --output-dir observed
python3 <resource>/scripts/sourcing.py calculate --input scenario.json --output-dir calculated

prepare输入见examples/query.json：method/target_asin/market，加相应keyword/image_url/days/page。不允许不适用字段或随意透传请求。输出request等待当前工具资格核实和用户审批。
observe输入：query、实际request、source_operation_id、captured_at（带时区）、mcp_result；货源可加offer_id，细分市场可加niche_id。未选中时仅候选。成功state=matched不表示交易可行或来源真实性已独立认证。
calculate输入见scenario.json：scenario_id、observations原始观察数组、candidates。每候选target_asin/market/offer_id/variant/supplier_source/quote/costs。quote含variant、purchase_quantity、minimum_order_quantity、price_basis="CNY/purchase_unit"、confirmed_at/source/note；说明指定变体、阶梯与采购单位。
costs各字段包含value/unit/basis/source/as_of/note。observed仅支持对应供应商price、Keepa.price、精确历史buyboxPrice.N.value；source必须等于原operation id，field保留精确字段，as_of为原captured_at。它只是直接价格证据，SKU/实际成交还需核验。其它费用一律user_scenario，source指出用户资料/假设依据，不填field；不能把模型猜测标为用户已确认。

输出input.json原字节、inspection.json结果；calculate另输出静态report.html。schema_version=1仅此资源私有，不是公共契约/Native工具凭证。单个异常观察记录失败，不污染其它候选；成本缺项返回incomplete。根格式/重复身份/不支持方法等返回非0且不生成成功产物。local helper不负责MCP调用、凭据、自动获取/上传素材、服务重试或真实账户验证。
