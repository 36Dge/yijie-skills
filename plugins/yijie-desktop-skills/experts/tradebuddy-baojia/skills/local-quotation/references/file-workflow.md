# 本地文件执行
先确认Python3.10+确实可用。仅使用本轮既有文件/命令权限，不依赖其他宿主安装的库。
1. 读取用户输入，保留来源和SHA；如果列名不同，在当前任务目录另建映射后的CSV或JSON。价格/数量/税等不得补默认。
2. 阅读 ../examples/quote-config.json。准备配置；若用户给CSV/XLSX，优先用--items读取原文件，避免人工重新抄写。多sheet用--sheet明确选择；公式依赖已缓存值，缺缓存/错误单元格需用户重算，不执行外链。日期用明确ISO文本，不能把Excel日期序号猜成报价日期。
3. 在当前任务工作目录运行：
`python3 <包根>/scripts/quotation.py --config <配置.json> --items <明细.xlsx或csv> --sheet <工作表名> --output-dir <不存在的新子目录>`
CSV不用--sheet；也可配置内嵌items。记账/比较附加`--ledger <旧台账.xlsx或csv> --compare-sku <准确SKU>`。
4. 实际exit0且stdout.status=complete后读取calculation.json和需要的comparison.json；按输入独立核算关键行、合计与币种/税口径，核对旧台账行仍在。生成XLSX包含报价明细和条款来源；必须给用户文件实际路径。无工具不得说已保存。
5. 新输出目录必须在当前任务工作区内，父目录须存在。已有目录拒绝，不清空重跑。中途失败说明已存在的部分文件，修正后使用新版本目录。输入和受管包一律不修改。
