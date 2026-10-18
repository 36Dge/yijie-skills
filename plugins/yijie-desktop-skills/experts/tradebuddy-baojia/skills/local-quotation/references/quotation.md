# 报价数据与计算
先确认字段，勿套行业默认。完整配置样例见 ../examples/quote-config.json。
- quote_id、date（YYYY-MM-DD）、supplier、customer、currency（三位码）、currency_decimals=2、source、terms：均明确给出。身份/付款/有效期缺失时询问，用户允许可明确记“待确认”，不能编联系人。
- tax_mode为excluded（单价未税）或included（单价含税）；tax_rate为明确小数，例如用户13%→0.13，不能默认13%。freight为用户提供的最终运费金额，freight_basis必须final_amount，不再自行加运费税。
- items（内嵌列表）或--items CSV/XLSX：列sku/name/spec/unit/quantity/unit_price；数量正数，单价允许明确0。保留精确SKU，不截去前导零。每项数值最多6位小数，金额2位。
- 先数量×单价按ROUND_HALF_UP舍入2位。未税价：net=该金额，tax=round(net×税率,2)，gross=net+tax；含税价：gross=该金额，net=round(gross/(1+税率),2)，tax=gross-net。
- 汇总所有逐行net/tax/gross，再加最终运费。不要用总额×税率替代逐行舍入，不重复计税，不默认为含运。Excel保留相同公式和缓存，编辑后由表格引擎重算；calculation.json是本次生成的静态计算记录，不自动随Excel手改更新。
- 报价修改用新quote_id与新输出目录；不覆盖旧文件。真实市场价、税法适用性、行业规则未核验，用户给税率只是本次计算输入。
