# 台账与同口径历史
只读用户指定的旧本地台账。脚本支持本适配版生成的ledger.csv或ledger.xlsx（sheet为报价台账）；其他表格先明确字段映射并另存适配输入，不能覆写原文档。
字段：record_id（quote_id:行号）、quote_id、date、supplier、customer、currency、tax_mode、tax_rate、source、sku、name、spec、unit、quantity、unit_price、net、tax、gross。记录重复拒绝；有意改版使用新编号。新版本保留旧行的所有值与附加字段，旧文件保持字节不变。
--ledger指定旧版，--compare-sku指定精确料号。比较只在spec/unit/currency/tax_mode/tax_rate相同的组内列出最小最大单价；保留报价日期、供应商与来源。交货、运费、付款条款可能仍不同，不把“组内最低单价”说成“最优采购”。无匹配明确0条，不使用近似SKU或另一个首行替代。
用户要求查历史而不新增报价时，可正常工具只读旧表，使用脚本中的read_table/compare进行查询并只交结果，不为查询强行创建新报价或记录。不得虚报云端记账成功。
