# 本地文件协议 v1
先读取examples/plan.json与sources.json。Python 3.10+标准库，无网络。
`python3 -B <本包绝对路径>/scripts/product.py --input <plan.json> --sources <sources.json> --out <用户工作区>/product-v1`
输出目录必须不存在；改稿使用product-v2，先读v1，不改v1/input或receipt。失败后先修输入、选新目录；没有receipt不称完整交付。
plan：schema_version=1、title、documents(1–6)。每文档kind为prd/roadmap/stakeholder/research/competitive/metrics之一且不重复，sections为{heading,body}列表，source_ids引用来源，quotes为可选{source_id,text}原句，open_questions为非空文本（确实没有则“无”）。不得把不同流程都填相同泛化段落；分别满足对应参考。
sources：sources数组，每项{id,locator,text}；id唯一，locator写输入文件/章节/用户消息位置，text保留原文，不为让引句通过而重写来源。
可选rice：reach_period、effort_unit、items。每项{id,name,reach_period,effort_unit,reach,impact,confidence,effort,source_ids}；数值可用十进制字符串，未知null，confidence明确0–1。effort已知必须>0；周期/单位必须逐项与总表一致。缺参不排名，完整分数输出Decimal字符串，平分保留输入顺序。
脚本检查结构、引用ID、引句字面匹配与RICE，不验证正文每个主张。需人工/模型逐项核对正文数值、出处、假设、受众和验收。receipt仅是文件hash证明，不是审批或事实认证。
