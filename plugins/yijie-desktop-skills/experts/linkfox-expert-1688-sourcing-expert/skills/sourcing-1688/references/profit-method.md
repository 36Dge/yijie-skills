# 单位贡献利润情景 v1
金额用Decimal计算，最后四舍五入到美分，非有限/负值/错误单位不参与。不存在默认汇率、FBA费、佣金、广告费、退货率或销量。输入缺失、来源错配、SKU报价未确认或数值不合法时state=incomplete，利润/margin/rank=null。明确0也需说明依据；不把空串/null/false当0。

每笔Amazon销售使用同一单位：
C = purchase_cny / fx_cny_per_usd * purchase_units_per_sale。
基础成本 B = C + inbound_usd + fba_usd + referral_usd + advertising_usd + storage_usd + placement_usd + other_usd。
每次退货增量损失 L = refunded_revenue_usd - referral_refund_usd + refund_admin_usd + return_handling_usd - recovery_usd。
单位贡献利润 = sale_usd - B - return_rate * L。
预期净收入 = sale_usd - return_rate * refunded_revenue_usd；利润率 = 利润 / 预期净收入，净收入为0时利润率未知。

采购/配送等已经在B扣一次，退货不重复扣；退款收入在L计入。referral_refund是实际可返还的原佣金，refund_admin是另扣管理费，不能把净返佣填入前者后再扣一次；return_handling合并实际退货处理/移除/弃置等增量费用；recovery是可回收库存成本抵减，须有明确依据，最多C+头程。退款金额≤售价，佣金返还≤原佣金，退货率0..1。部分退款可显式填写均值，该线性情景不覆盖多事件/跨周期复杂会计。

sale_usd单位USD/sale；purchase_cny单位CNY/purchase_unit；fx为CNY/USD；purchase_units_per_sale为purchase_units/sale；基础费用USD/sale；return_rate为returns/sale；退货字段USD/return。基础cost不应再包含已经计入退货增量的费用。金额来源是observed或user_scenario，日期/来源/说明必填。

佣金按实际类目规则/最低佣金、FBA按适用包装/重量/配送条件核实，不能仅用一条百分比或原2025费表推断。广告可以用用户明确的每单分摊额，不能从SP关键词数量推算，不能以行业ACoS当TACoS。仓储/入库按季节与周转分摊后显式填写，不暗用运行月份。

同ASIN同情景内按单位贡献利润排序，仅完整候选参与。全部原始输入随报告保留；不跨ASIN排名，不乘竞品月销量，不生成预期月收益。负利润照实显示。合成示例：售价30、采购36CNY/汇率7.2=5USD，其余基础成本11.70，退货率10%、退款30/返佣4.5/管理费0.9/处理1/回收0，则B=16.70、退货调整2.74、贡献利润10.56。此为算术例子，不是推荐费率。
